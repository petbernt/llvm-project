#!/usr/bin/env python3

"""Execution-aware report for llvm-libc behavior mappings.

This complements `behavior_mapping_check.py`:

- `behavior_mapping_check.py` validates source-level consistency
- this script optionally joins that mapping data to built test executables in a
  build tree, and can also execute those test binaries

The script stays intentionally lightweight. It does not try to replace lit or
CTest; it only provides a focused report for the behavior mapping experiment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from behavior_mapping_check import _discover_behavior_ids, _discover_verifies


_EXECUTABLE_SUFFIX_RE = (
    r"(?:\.__(?:unit|hermetic)__(?:\.[A-Za-z0-9_.-]+)*)?\.__build__(?:\.exe)?$"
)
_MULTI_IMPL_RE = re.compile(r"\badd_libc_multi_impl_test\(\s*(?P<name>[A-Za-z0-9_]+)\b")


def _read_params_file(params_path: Path) -> tuple[list[str], list[str], dict[str, str]]:
    loader_args: list[str] = []
    test_args: list[str] = []
    extra_env: dict[str, str] = {}

    if not params_path.is_file():
        return loader_args, test_args, extra_env

    content = params_path.read_text(encoding="utf-8", errors="replace")
    sections = content.split("---\n")
    if len(sections) >= 3:
        loader_args = [line for line in sections[0].splitlines() if line]
        test_args = [line for line in sections[1].splitlines() if line]
        env_section = sections[2]
    else:
        test_args = [line for line in sections[0].splitlines() if line]
        env_section = sections[1] if len(sections) > 1 else ""

    for line in env_section.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        extra_env[key] = value

    return loader_args, test_args, extra_env


def _get_params_path(binary_path: Path) -> Path | None:
    direct = Path(str(binary_path) + ".params")
    if direct.is_file():
        return direct

    if binary_path.suffix.lower() == ".exe":
        sibling = binary_path.with_suffix(".params")
        if sibling.is_file():
            return sibling

    return None


def _behavior_function_name(behavior_id: str) -> str:
    parts = behavior_id.split(".")
    return parts[1] if len(parts) >= 3 else ""


def _render_status_summary(count: int, total: int) -> str:
    return f"{count}/{total}" if total else "0/0"


def _source_relative_to_test_root(libc_dir: Path, source_path: Path) -> Path | None:
    test_root = (libc_dir / "test").resolve()
    try:
        return source_path.resolve().relative_to(test_root)
    except ValueError:
        return None


def _discover_multi_impl_stems(libc_dir: Path) -> set[str]:
    stems: set[str] = set()
    for cmake_path in sorted((libc_dir / "test").rglob("CMakeLists.txt")):
        text = cmake_path.read_text(encoding="utf-8", errors="replace")
        for match in _MULTI_IMPL_RE.finditer(text):
            stems.add(f"{match.group('name')}_test")
    return stems


def _candidate_filename_regexes(
    relative_test_path: Path, multi_impl_stems: set[str]
) -> list[re.Pattern[str]]:
    if relative_test_path.parts[0] == "src":
        category = ".".join(relative_test_path.parts[1:-1])
        prefix = rf"libc\.test\.src\.{re.escape(category)}\."
    elif relative_test_path.parts[0] == "include":
        prefix = r"libc\.test\.include\."
    else:
        return []

    stem = relative_test_path.stem
    regexes = [
        re.compile(prefix + re.escape(stem) + _EXECUTABLE_SUFFIX_RE),
    ]

    if stem in multi_impl_stems:
        function_prefix = stem[: -len("_test")]
        regexes.append(
            re.compile(
                prefix
                + re.escape(function_prefix)
                + r"_[A-Za-z0-9_]+_test"
                + _EXECUTABLE_SUFFIX_RE
            )
        )

    return regexes


def _candidate_search_dirs(build_dir: Path, relative_test_path: Path) -> list[Path]:
    rel_parent = relative_test_path.parent
    candidates = [
        build_dir / "libc" / "test" / rel_parent,
        build_dir / "test" / rel_parent,
        build_dir / rel_parent,
        build_dir,
    ]

    unique_dirs: list[Path] = []
    seen: set[Path] = set()
    for directory in candidates:
        resolved = directory.resolve()
        if resolved in seen or not directory.is_dir():
            continue
        seen.add(resolved)
        unique_dirs.append(directory)
    return unique_dirs


def _discover_binaries_for_source(
    build_dir: Path, libc_dir: Path, source_path: Path, multi_impl_stems: set[str]
) -> list[Path]:
    relative_test_path = _source_relative_to_test_root(libc_dir, source_path)
    if relative_test_path is None:
        return []

    regexes = _candidate_filename_regexes(relative_test_path, multi_impl_stems)
    if not regexes:
        return []

    matches: set[Path] = set()
    for search_dir in _candidate_search_dirs(build_dir, relative_test_path):
        for path in search_dir.iterdir():
            if not path.is_file():
                continue
            if any(regex.fullmatch(path.name) for regex in regexes):
                matches.add(path.resolve())

    return sorted(matches)


def _run_binary(binary_path: Path, test_command: str | None) -> dict[str, object]:
    params_path = _get_params_path(binary_path)
    loader_args: list[str] = []
    test_args: list[str] = []
    extra_env: dict[str, str] = {}
    if params_path is not None:
        loader_args, test_args, extra_env = _read_params_file(params_path)

    env = dict(**extra_env)
    env.update({"PWD": str(binary_path.parent)})
    merged_env = dict(os.environ)
    merged_env.update(env)

    if test_command:
        if "@BINARY@" in test_command:
            prefix, _, suffix = test_command.partition("@BINARY@")
            command = (
                shlex.split(prefix)
                + loader_args
                + [str(binary_path)]
                + shlex.split(suffix)
                + test_args
            )
        else:
            command = shlex.split(test_command) + loader_args + [str(binary_path)] + test_args
    else:
        command = [str(binary_path)] + test_args

    result = subprocess.run(
        command,
        cwd=binary_path.parent,
        env=merged_env,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _status_from_runs(binary_runs: list[dict[str, object]] | None) -> str:
    if binary_runs is None:
        return "not-run"
    if not binary_runs:
        return "not-built"
    if any(run["returncode"] != 0 for run in binary_runs):
        return "fail"
    return "pass"


def _render_table(rows: list[dict[str, object]]) -> str:
    lines = [
        "| Behavior | Tests | Source files | Binaries | Execution |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        tests = ", ".join(row["tests"])
        files = ", ".join(row["source_files"])
        binaries = ", ".join(row["binaries"]) if row["binaries"] else "(none)"
        lines.append(
            f"| `{row['behavior']}` | {tests} | {files} | {binaries} | {row['execution']} |"
        )
    return "\n".join(lines)


def build_report(
    libc_dir: Path,
    build_dir: Path | None,
    function_filters: set[str],
    run_tests: bool,
    test_command: str | None,
) -> dict[str, object]:
    behavior_dir = libc_dir / "behavior"
    test_dir = libc_dir / "test"

    behavior_ids, yaml_files, duplicate_to_files = _discover_behavior_ids(behavior_dir)
    behavior_to_tests, referenced_in_files, total_verifies, errors = _discover_verifies(
        test_dir
    )
    multi_impl_stems = _discover_multi_impl_stems(libc_dir)

    unknown_ids = sorted(set(behavior_to_tests) - behavior_ids)
    uncovered_ids = sorted(behavior_ids - set(behavior_to_tests))

    selected_behavior_ids = sorted(
        behavior_id
        for behavior_id in behavior_ids
        if not function_filters or _behavior_function_name(behavior_id) in function_filters
    )

    source_file_to_binaries: dict[Path, list[Path]] = {}
    source_file_to_runs: dict[Path, list[dict[str, object]] | None] = {}

    if build_dir is not None:
        needed_source_files = {
            source_path
            for behavior_id in selected_behavior_ids
            for source_path in referenced_in_files.get(behavior_id, set())
        }
        for source_path in sorted(needed_source_files):
            binaries = _discover_binaries_for_source(
                build_dir, libc_dir, source_path, multi_impl_stems
            )
            source_file_to_binaries[source_path] = binaries
            if run_tests and binaries:
                source_file_to_runs[source_path] = [
                    _run_binary(binary_path, test_command) for binary_path in binaries
                ]
            elif run_tests:
                source_file_to_runs[source_path] = []
            else:
                source_file_to_runs[source_path] = None

    rows: list[dict[str, object]] = []
    built_behaviors = 0
    pass_behaviors = 0
    discovered_binaries: set[str] = set()
    executed_binaries = 0
    failed_binaries = 0

    for behavior_id in selected_behavior_ids:
        source_files = sorted(str(path.relative_to(libc_dir)) for path in referenced_in_files.get(behavior_id, set()))
        source_paths = sorted(referenced_in_files.get(behavior_id, set()))

        binaries: list[str] = []
        binary_runs: list[dict[str, object]] | None = None
        if build_dir is not None:
            all_binaries: list[str] = []
            all_runs: list[dict[str, object]] = []
            all_built = True
            for source_path in source_paths:
                per_source_binaries = source_file_to_binaries.get(source_path, [])
                if not per_source_binaries:
                    all_built = False
                all_binaries.extend(str(path.relative_to(build_dir)) for path in per_source_binaries)
                per_source_runs = source_file_to_runs.get(source_path)
                if per_source_runs:
                    all_runs.extend(per_source_runs)
            binaries = sorted(set(all_binaries))
            if all_built and source_paths:
                built_behaviors += 1
            if run_tests:
                binary_runs = all_runs if binaries else []
                if binary_runs and all(run["returncode"] == 0 for run in binary_runs):
                    pass_behaviors += 1
                executed_binaries += len(binary_runs)
                failed_binaries += sum(1 for run in binary_runs if run["returncode"] != 0)
            discovered_binaries.update(binaries)

        execution = _status_from_runs(binary_runs) if build_dir is not None else "source-only"
        if build_dir is not None and not run_tests:
            execution = "built" if binaries else "not-built"

        rows.append(
            {
                "behavior": behavior_id,
                "tests": sorted(behavior_to_tests.get(behavior_id, set())),
                "source_files": source_files,
                "binaries": binaries,
                "execution": execution,
            }
        )

    return {
        "summary": {
            "behavior_files": len(yaml_files),
            "behavior_ids": len(behavior_ids),
            "selected_behavior_ids": len(selected_behavior_ids),
            "verifies_annotations": total_verifies,
            "mapped_behaviors": len(behavior_ids) - len(uncovered_ids),
            "selected_mapped_behaviors": sum(
                1 for behavior_id in selected_behavior_ids if behavior_id in behavior_to_tests
            ),
            "built_behaviors": built_behaviors,
            "passing_behaviors": pass_behaviors,
            "discovered_binaries": len(discovered_binaries),
            "executed_binaries": executed_binaries,
            "failed_binaries": failed_binaries,
        },
        "errors": {
            "dangling_annotations": errors,
            "duplicate_behavior_ids": {
                behavior_id: sorted(str(path) for path in paths)
                for behavior_id, paths in sorted(duplicate_to_files.items())
            },
            "unknown_behavior_ids": unknown_ids,
            "uncovered_behavior_ids": uncovered_ids,
        },
        "rows": rows,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Report llvm-libc behavior mappings, built tests, and optional execution status."
    )
    parser.add_argument(
        "--libc-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to libc/ (defaults relative to this script).",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=None,
        help="Optional build directory used to discover test executables.",
    )
    parser.add_argument(
        "--functions",
        nargs="*",
        default=[],
        help="Optional list of function names to report (for example: memcpy memset).",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run discovered test executables and include pass/fail status.",
    )
    parser.add_argument(
        "--test-command",
        default=None,
        help="Optional launcher command. Use @BINARY@ as a placeholder for the test binary.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path to write the full report as JSON.",
    )
    args = parser.parse_args(argv)

    libc_dir = args.libc_dir.resolve()
    build_dir = args.build_dir.resolve() if args.build_dir is not None else None
    function_filters = set(args.functions)

    report = build_report(
        libc_dir=libc_dir,
        build_dir=build_dir,
        function_filters=function_filters,
        run_tests=args.run_tests,
        test_command=args.test_command,
    )

    summary = report["summary"]
    print(f"Behavior files: {summary['behavior_files']}")
    print(f"Behavior IDs: {summary['behavior_ids']}")
    print(f"Selected behavior IDs: {summary['selected_behavior_ids']}")
    print(f"@verifies annotations: {summary['verifies_annotations']}")
    print(
        "Mapped selected behaviors: "
        + _render_status_summary(
            summary["selected_mapped_behaviors"], summary["selected_behavior_ids"]
        )
    )
    if build_dir is not None:
        print(
            "Behaviors with built test binaries: "
            + _render_status_summary(
                summary["built_behaviors"], summary["selected_behavior_ids"]
            )
        )
        print(f"Discovered test binaries: {summary['discovered_binaries']}")
        if args.run_tests:
            print(
                "Behaviors with passing executed tests: "
                + _render_status_summary(
                    summary["passing_behaviors"], summary["selected_behavior_ids"]
                )
            )
            print(f"Executed test binaries: {summary['executed_binaries']}")
            print(f"Failed test binaries: {summary['failed_binaries']}")

    print()
    print(_render_table(report["rows"]))

    if args.json_output is not None:
        args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    has_mapping_errors = any(
        [
            report["errors"]["dangling_annotations"],
            report["errors"]["duplicate_behavior_ids"],
            report["errors"]["unknown_behavior_ids"],
            report["errors"]["uncovered_behavior_ids"],
        ]
    )
    has_execution_failures = args.run_tests and summary["failed_binaries"] > 0
    return 1 if has_mapping_errors or has_execution_failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
