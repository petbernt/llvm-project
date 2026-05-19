#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


def _load_check_module():
    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "libcxx" / "utils" / "behavior" / "check.py"
    spec = importlib.util.spec_from_file_location("libcxx_behavior_check", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BehaviorCheckTest(unittest.TestCase):
    def setUp(self):
        self.behavior_check = _load_check_module()

    def _make_libcxx_tree(self, tmpdir: str) -> Path:
        libcxx_dir = Path(tmpdir) / "libcxx"
        (libcxx_dir / "behavior").mkdir(parents=True)
        (libcxx_dir / "test").mkdir(parents=True)
        return libcxx_dir

    def _run_main(self, libcxx_dir: Path):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.behavior_check.main(["--libcxx-dir", str(libcxx_dir)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_valid_mapping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libcxx_dir = self._make_libcxx_tree(tmpdir)
            (libcxx_dir / "behavior" / "algorithm.yaml").write_text(
                """
functions:
  std::find:
    behaviors:
      - id: "algorithm.find.B1"
        text: "Returns the first match."
""",
                encoding="utf-8",
            )
            (libcxx_dir / "test" / "find.pass.cpp").write_text(
                """
int main(int, char**) {
  // @verifies algorithm.find.B1
  return 0;
}
""",
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libcxx_dir)

        self.assertEqual(code, 0, stderr)
        self.assertIn("Mapped behaviors: 1/1", stdout)
        self.assertIn("test/find.pass.cpp:3", stdout)

    def test_unknown_annotation_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libcxx_dir = self._make_libcxx_tree(tmpdir)
            (libcxx_dir / "behavior" / "algorithm.yaml").write_text(
                """
functions:
  std::find:
    behaviors:
      - id: "algorithm.find.B1"
        text: "Returns the first match."
""",
                encoding="utf-8",
            )
            (libcxx_dir / "test" / "find.pass.cpp").write_text(
                "// @verifies algorithm.find.B2\n",
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libcxx_dir)

        self.assertEqual(code, 1)
        self.assertIn("unknown behavior id referenced: algorithm.find.B2", stderr)
        self.assertIn("Unmapped behaviors", stdout)

    def test_unmapped_behavior_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libcxx_dir = self._make_libcxx_tree(tmpdir)
            (libcxx_dir / "behavior" / "algorithm.yaml").write_text(
                """
functions:
  std::find:
    behaviors:
      - id: "algorithm.find.B1"
        text: "Returns the first match."
""",
                encoding="utf-8",
            )
            (libcxx_dir / "test" / "find.pass.cpp").write_text(
                "int main(int, char**) { return 0; }\n",
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libcxx_dir)

        self.assertEqual(code, 1)
        self.assertIn("missing verifying test for behavior: algorithm.find.B1", stderr)
        self.assertIn("Mapped behaviors: 0/1", stdout)

    def test_duplicate_behavior_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libcxx_dir = self._make_libcxx_tree(tmpdir)
            (libcxx_dir / "behavior" / "a.yaml").write_text(
                """
functions:
  std::find:
    behaviors:
      - id: "algorithm.find.B1"
        text: "Returns the first match."
""",
                encoding="utf-8",
            )
            (libcxx_dir / "behavior" / "b.yaml").write_text(
                """
functions:
  std::find:
    behaviors:
      - id: "algorithm.find.B1"
        text: "Returns the first match."
""",
                encoding="utf-8",
            )
            (libcxx_dir / "test" / "find.pass.cpp").write_text(
                "// @verifies algorithm.find.B1\n",
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libcxx_dir)

        self.assertEqual(code, 1)
        self.assertIn("duplicate behavior id declared: algorithm.find.B1", stderr)
        self.assertIn("Duplicate behavior IDs", stdout)

    def test_missing_directories_report_configuration_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libcxx_dir = Path(tmpdir) / "libcxx"
            libcxx_dir.mkdir()

            code, _, stderr = self._run_main(libcxx_dir)

        self.assertEqual(code, 2)
        self.assertIn("behavior directory not found", stderr)


if __name__ == "__main__":
    unittest.main()
