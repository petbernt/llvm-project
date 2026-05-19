#!/usr/bin/env python3

"""Behavior-to-test mapping validator for libc++.

This script validates a small, source-level mapping model:

- behavior IDs are authored in YAML files under `libcxx/behavior/`
- tests can claim intended coverage with `// @verifies <BEHAVIOR_ID>`

The validator:
- fails if a behavior ID has no mapped test annotation
- fails if an annotation references an unknown behavior ID
- fails if a behavior ID is declared more than once
- prints a short summary and a Markdown matrix of behavior ID to source
  locations
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


_TRACKED_BLOCK_RE = re.compile(
    r"^(?P<indent>\s*)(?:behaviors|requirements)\s*:\s*(#.*)?$"
)
_ID_RE = re.compile(r'^\s*(?:-\s*)?id\s*:\s*"?(?P<id>[^"#]+?)"?\s*(?:#.*)?$')
_VERIFIES_RE = re.compile(r"@verifies\s+(?P<id>[A-Za-z0-9_.-]+)\b")


def _extract_behavior_ids_from_yaml(text: str) -> tuple[set[str], set[str]]:
    """Extract tracked IDs from YAML behavior lists."""
    behavior_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    in_tracked_block = False
    tracked_block_indent_len = -1

    for line in text.splitlines():
        if not in_tracked_block:
            match = _TRACKED_BLOCK_RE.match(line)
            if match:
                in_tracked_block = True
                tracked_block_indent_len = len(match.group("indent"))
            continue

        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue

        current_indent_len = len(line) - len(line.lstrip(" "))
        if current_indent_len <= tracked_block_indent_len:
            in_tracked_block = False
            tracked_block_indent_len = -1
            match = _TRACKED_BLOCK_RE.match(line)
            if match:
                in_tracked_block = True
                tracked_block_indent_len = len(match.group("indent"))
            continue

        id_match = _ID_RE.match(line)
        if not id_match:
            continue

        behavior_id = id_match.group("id").strip()
        if behavior_id in behavior_ids:
            duplicate_ids.add(behavior_id)
        else:
            behavior_ids.add(behavior_id)

    return behavior_ids, duplicate_ids


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _discover_behavior_ids(
    behavior_dir: Path,
) -> tuple[set[str], list[Path], dict[str, set[Path]]]:
    """Find behavior IDs under `behavior_dir` and report duplicates."""
    yaml_files = sorted(behavior_dir.rglob("*.yaml"))
    first_seen_in: dict[str, Path] = {}
    duplicate_to_files: dict[str, set[Path]] = defaultdict(set)

    for path in yaml_files:
        file_ids, local_duplicates = _extract_behavior_ids_from_yaml(_read_text(path))

        for duplicate_id in local_duplicates:
            duplicate_to_files[duplicate_id].add(path)

        for behavior_id in file_ids:
            if behavior_id in first_seen_in:
                duplicate_to_files[behavior_id].update(
                    {first_seen_in[behavior_id], path}
                )
                continue
            first_seen_in[behavior_id] = path

    return set(first_seen_in), yaml_files, duplicate_to_files


def _discover_verifies(
    test_root: Path, libcxx_dir: Path
) -> tuple[dict[str, set[str]], dict[str, set[Path]], int]:
    """Scan tests for `@verifies` annotations and record source locations."""
    behavior_to_locations: dict[str, set[str]] = defaultdict(set)
    referenced_in_files: dict[str, set[Path]] = defaultdict(set)
    total_verifies = 0

    for path in sorted(test_root.rglob("*")):
        if not path.is_file():
            continue

        for line_number, line in enumerate(_read_text(path).splitlines(), start=1):
            for match in _VERIFIES_RE.finditer(line):
                behavior_id = match.group("id")
                relative_path = path.relative_to(libcxx_dir)
                behavior_to_locations[behavior_id].add(
                    f"{relative_path}:{line_number}"
                )
                referenced_in_files[behavior_id].add(path)
                total_verifies += 1

    return behavior_to_locations, referenced_in_files, total_verifies


def _render_matrix(
    behavior_ids: list[str], behavior_to_locations: dict[str, set[str]]
) -> str:
    lines = ["| Behavior | Verifying source locations |", "|---|---|"]
    for behavior_id in behavior_ids:
        locations = ", ".join(sorted(behavior_to_locations.get(behavior_id, set())))
        lines.append(f"| `{behavior_id}` | {locations} |")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate libc++ behavior-to-test mappings."
    )
    parser.add_argument(
        "--libcxx-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Path to libcxx/ (defaults relative to this script).",
    )
    args = parser.parse_args(argv)

    libcxx_dir = args.libcxx_dir.resolve()
    behavior_dir = libcxx_dir / "behavior"
    test_dir = libcxx_dir / "test"

    if not behavior_dir.is_dir():
        print(f"error: behavior directory not found: {behavior_dir}", file=sys.stderr)
        return 2
    if not test_dir.is_dir():
        print(f"error: test directory not found: {test_dir}", file=sys.stderr)
        return 2

    behavior_ids, yaml_files, duplicate_to_files = _discover_behavior_ids(
        behavior_dir
    )
    behavior_to_locations, referenced_in_files, total_verifies = _discover_verifies(
        test_dir, libcxx_dir
    )

    unknown_ids = sorted(set(behavior_to_locations) - behavior_ids)
    uncovered_ids = sorted(behavior_ids - set(behavior_to_locations))

    ok = True
    if duplicate_to_files:
        ok = False
        for behavior_id in sorted(duplicate_to_files):
            files = ", ".join(
                str(path) for path in sorted(duplicate_to_files[behavior_id])
            )
            print(
                f"error: duplicate behavior id declared: {behavior_id} ({files})",
                file=sys.stderr,
            )

    if unknown_ids:
        ok = False
        for unknown in unknown_ids:
            files = ", ".join(
                str(path) for path in sorted(referenced_in_files.get(unknown, set()))
            )
            print(
                f"error: unknown behavior id referenced: {unknown} ({files})",
                file=sys.stderr,
            )

    if uncovered_ids:
        ok = False
        for missing in uncovered_ids:
            print(
                f"error: missing verifying test for behavior: {missing}",
                file=sys.stderr,
            )

    print(f"Behavior files: {len(yaml_files)}")
    print(f"Behavior IDs: {len(behavior_ids)}")
    print(f"@verifies annotations: {total_verifies}")
    print(
        "Mapped behaviors: "
        f"{len(behavior_ids) - len(uncovered_ids)}/{len(behavior_ids)}"
    )
    if duplicate_to_files:
        print(f"Duplicate behavior IDs ({len(duplicate_to_files)}):")
        for behavior_id in sorted(duplicate_to_files):
            print(f"  - {behavior_id}")
    if unknown_ids:
        print(f"Unknown referenced IDs ({len(unknown_ids)}):")
        for unknown in unknown_ids:
            print(f"  - {unknown}")
    if uncovered_ids:
        print(f"Unmapped behaviors ({len(uncovered_ids)}):")
        for missing in uncovered_ids:
            print(f"  - {missing}")

    print()
    print(_render_matrix(sorted(behavior_ids), behavior_to_locations))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
