import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_behavior_report_module():
    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "libc" / "utils" / "behavior" / "report.py"
    spec = importlib.util.spec_from_file_location("behavior_report", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BehaviorReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.behavior_report = _load_behavior_report_module()

    def _make_libc_tree(self, tmpdir: str) -> Path:
        libc_dir = Path(tmpdir) / "libc"
        (libc_dir / "behavior").mkdir(parents=True)
        (libc_dir / "test" / "src" / "string").mkdir(parents=True)
        return libc_dir

    def _write_shell_test(self, path: Path, body: str) -> None:
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def _run_main(self, *args: str):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.behavior_report.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_reports_built_binary_for_regular_test(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            build_dir = Path(tmpdir) / "build"
            test_build_dir = build_dir / "libc" / "test" / "src" / "string"
            test_build_dir.mkdir(parents=True)

            (libc_dir / "behavior" / "string.yaml").write_text(
                "\n".join(
                    [
                        "functions:",
                        "  memcmp:",
                        "    behaviors:",
                        "      - id: string.memcmp.B1",
                        "        text: Returns zero for count zero.",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "src" / "string" / "memcmp_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.memcmp.B1",
                        "TEST(Suite, Name) {}",
                    ]
                ),
                encoding="utf-8",
            )
            self._write_shell_test(
                test_build_dir / "libc.test.src.string.memcmp_test.__unit__.__build__",
                "exit 0\n",
            )

            code, stdout, _ = self._run_main(
                "--libc-dir",
                str(libc_dir),
                "--build-dir",
                str(build_dir),
            )
            self.assertEqual(code, 0)
            self.assertIn("Behaviors with built test binaries: 1/1", stdout)
            self.assertIn(
                "libc/test/src/string/libc.test.src.string.memcmp_test.__unit__.__build__",
                stdout,
            )

    def test_reports_multi_impl_binaries_for_memcpy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            build_dir = Path(tmpdir) / "build"
            test_build_dir = build_dir / "libc" / "test" / "src" / "string"
            test_build_dir.mkdir(parents=True)

            (libc_dir / "behavior" / "string.yaml").write_text(
                "\n".join(
                    [
                        "functions:",
                        "  memcpy:",
                        "    behaviors:",
                        "      - id: string.memcpy.B1",
                        "        text: Returns dest.",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "src" / "string" / "memcpy_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.memcpy.B1",
                        "TEST(Suite, Name) {}",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "src" / "string" / "CMakeLists.txt").write_text(
                "add_libc_multi_impl_test(memcpy libc-string-tests SRCS memcpy_test.cpp)\n",
                encoding="utf-8",
            )
            self._write_shell_test(
                test_build_dir / "libc.test.src.string.memcpy_test.__unit__.__build__",
                "exit 0\n",
            )
            self._write_shell_test(
                test_build_dir
                / "libc.test.src.string.memcpy_x86_64_opt_sse2_test.__unit__.__build__",
                "exit 0\n",
            )

            code, stdout, _ = self._run_main(
                "--libc-dir",
                str(libc_dir),
                "--build-dir",
                str(build_dir),
            )
            self.assertEqual(code, 0)
            self.assertIn("Discovered test binaries: 2", stdout)
            self.assertIn("memcpy_x86_64_opt_sse2_test", stdout)

    def test_reports_execution_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            build_dir = Path(tmpdir) / "build"
            test_build_dir = build_dir / "libc" / "test" / "src" / "string"
            test_build_dir.mkdir(parents=True)

            (libc_dir / "behavior" / "string.yaml").write_text(
                "\n".join(
                    [
                        "functions:",
                        "  memset:",
                        "    behaviors:",
                        "      - id: string.memset.B1",
                        "        text: Returns dest.",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "src" / "string" / "memset_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.memset.B1",
                        "TEST(Suite, Name) {}",
                    ]
                ),
                encoding="utf-8",
            )
            self._write_shell_test(
                test_build_dir / "libc.test.src.string.memset_test.__unit__.__build__",
                "echo fail >&2\nexit 1\n",
            )

            code, stdout, _ = self._run_main(
                "--libc-dir",
                str(libc_dir),
                "--build-dir",
                str(build_dir),
                "--run-tests",
            )
            self.assertEqual(code, 1)
            self.assertIn("Behaviors with passing executed tests: 0/1", stdout)
            self.assertIn(
                "| `string.memset.B1` | Suite.Name | test/src/string/memset_test.cpp |",
                stdout,
            )
            self.assertIn("| fail |", stdout)

    def test_writes_json_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            json_path = Path(tmpdir) / "report.json"

            (libc_dir / "behavior" / "string.yaml").write_text(
                "\n".join(
                    [
                        "functions:",
                        "  strlen:",
                        "    behaviors:",
                        "      - id: string.strlen.B1",
                        "        text: Returns zero for an empty string.",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "src" / "string" / "strlen_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.strlen.B1",
                        "TEST(Suite, Name) {}",
                    ]
                ),
                encoding="utf-8",
            )

            code, _, _ = self._run_main(
                "--libc-dir",
                str(libc_dir),
                "--json-output",
                str(json_path),
            )
            self.assertEqual(code, 0)
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["selected_behavior_ids"], 1)
            self.assertEqual(report["rows"][0]["behavior"], "string.strlen.B1")


if __name__ == "__main__":
    unittest.main()
