import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


def _load_behavior_check_module():
    repo_root = Path(__file__).resolve().parents[4]
    script_path = repo_root / "libc" / "utils" / "behavior" / "check.py"
    spec = importlib.util.spec_from_file_location("behavior_check", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BehaviorCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.behavior_check = _load_behavior_check_module()

    def _make_libc_tree(self, tmpdir: str) -> Path:
        libc_dir = Path(tmpdir) / "libc"
        (libc_dir / "behavior").mkdir(parents=True)
        (libc_dir / "test").mkdir(parents=True)
        return libc_dir

    def _run_main(self, libc_dir: Path):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.behavior_check.main(["--libc-dir", str(libc_dir)])
        return code, out.getvalue(), err.getvalue()

    def _run_source(self, source: str, ids=("string.demo.B1",)):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            (libc_dir / "behavior" / "string.yaml").write_text(
                "functions:\n  demo:\n    behaviors:\n"
                + "".join(f"      - id: {behavior_id}\n" for behavior_id in ids),
                encoding="utf-8",
            )
            (libc_dir / "test" / "demo_test.cpp").write_text(source, encoding="utf-8")
            return self._run_main(libc_dir)

    def test_passes_when_all_behaviors_are_mapped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            (libc_dir / "behavior" / "string.yaml").write_text(
                "\n".join(
                    [
                        "functions:",
                        "  memcpy:",
                        "    behaviors:",
                        "      - id: string.memcpy.B1",
                        "        text: Returns dest.",
                        "      - id: string.memcpy.B2",
                        "        text: Copies bytes.",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "memcpy_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.memcpy.B1",
                        "// @verifies string.memcpy.B2",
                        "TEST(Suite, Name) {",
                        "  (void)0;",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libc_dir)
            self.assertEqual(code, 0, stderr)
            self.assertIn("Mapped behaviors: 2/2", stdout)
            self.assertIn("| `string.memcpy.B1` | Suite.Name |", stdout)
            self.assertIn("| `string.memcpy.B2` | Suite.Name |", stdout)

    def test_maps_multiline_declarations_without_leaking_annotations(self):
        for macro in ("TEST", "TEST_F", "TEST_P", "TYPED_TEST", "TYPED_TEST_P"):
            with self.subTest(macro=macro):
                code, stdout, stderr = self._run_source(
                    "// @verifies string.demo.B1\n"
                    f"{macro}(Suite,\n    Intended) {{}}\n"
                    "// @verifies string.demo.B2\n"
                    "TEST(Suite, Next) {}\n"
                    "// @verifies string.demo.B3\n"
                    f"{macro}(\n    Suite,\n    Last) {{}}\n",
                    ids=("string.demo.B1", "string.demo.B2", "string.demo.B3"),
                )
                self.assertEqual(code, 0, stderr)
                self.assertIn("| `string.demo.B1` | Suite.Intended |", stdout)
                self.assertIn("| `string.demo.B2` | Suite.Next |", stdout)
                self.assertIn("| `string.demo.B3` | Suite.Last |", stdout)

    def test_rejects_commented_or_unrecognized_tests_without_skipping_ahead(self):
        for declaration in (
            "// TEST(Suite, CommentedOut) {}",
            "/* TEST(Suite, CommentedOut) {} */",
            '"TEST(Suite, StringLiteral) {}";',
            "CUSTOM_TEST(Suite, Unsupported) {}",
        ):
            for following in ("", "\nTEST(Suite, Unrelated) {}"):
                with self.subTest(declaration=declaration, following=following):
                    code, stdout, stderr = self._run_source(
                        "// @verifies string.demo.B1\n" + declaration + following
                    )
                    self.assertEqual(code, 1)
                    self.assertIn("demo_test.cpp:1: dangling @verifies", stderr)
                    self.assertIn("Mapped behaviors: 0/1", stdout)
                    self.assertNotIn("Suite.", stdout)

    def test_ignores_annotations_in_literals_and_block_comments(self):
        code, stdout, stderr = self._run_source(
            """const char *example = "// @verifies string.demo.UNKNOWN";
const char *raw = R"example(" // @verifies string.demo.UNKNOWN
TEST(Suite, Fake) {}
)example";
/*
// @verifies string.demo.UNKNOWN
TEST(Suite, CommentedOut) {}
*/
// @verifies string.demo.B1
TEST(Suite, Intended) {}
"""
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("@verifies annotations: 1", stdout)
        self.assertIn("| `string.demo.B1` | Suite.Intended |", stdout)

    def test_accepts_quoted_and_unquoted_ids(self):
        for quote in ("", "'", '"'):
            with self.subTest(quote=quote):
                code, stdout, stderr = self._run_source(
                    "// @verifies string.demo.B1\nTEST(Suite, Intended) {}",
                    ids=(f"{quote}string.demo.B1{quote}",),
                )
                self.assertEqual(code, 0, stderr)
                self.assertIn("| `string.demo.B1` | Suite.Intended |", stdout)

    def test_fails_on_duplicate_id_within_one_file(self):
        code, stdout, stderr = self._run_source(
            "// @verifies string.demo.B1\nTEST(Suite, Intended) {}",
            ids=("string.demo.B1", '"string.demo.B1"'),
        )
        self.assertEqual(code, 1)
        self.assertIn("duplicate behavior id declared: string.demo.B1", stderr)

    def test_fails_when_no_behavior_ids_are_found(self):
        code, stdout, stderr = self._run_source("TEST(Suite, Unannotated) {}", ids=())
        self.assertEqual(code, 1)
        self.assertIn("no behavior IDs found", stderr)

    def test_fails_when_behavior_is_unmapped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
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
            (libc_dir / "test" / "memcpy_test.cpp").write_text(
                "TEST(Suite, Name) {}", encoding="utf-8"
            )

            code, stdout, stderr = self._run_main(libc_dir)
            self.assertEqual(code, 1)
            self.assertIn(
                "missing verifying test for behavior: string.memcpy.B1", stderr
            )
            self.assertIn("Mapped behaviors: 0/1", stdout)
            self.assertIn("Unmapped behaviors (1):", stdout)

    def test_fails_on_unknown_verifies_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
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
            (libc_dir / "test" / "memcpy_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.memcpy.UNKNOWN",
                        "TEST(Suite, Name) {}",
                    ]
                ),
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libc_dir)
            self.assertEqual(code, 1)
            self.assertIn(
                "unknown behavior id referenced: string.memcpy.UNKNOWN", stderr
            )
            self.assertIn("Unknown referenced IDs (1):", stdout)

    def test_fails_on_duplicate_behavior_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
            (libc_dir / "behavior" / "a.yaml").write_text(
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
            (libc_dir / "behavior" / "b.yaml").write_text(
                "\n".join(
                    [
                        "functions:",
                        "  memset:",
                        "    behaviors:",
                        "      - id: string.memcpy.B1",
                        "        text: Duplicate.",
                    ]
                ),
                encoding="utf-8",
            )
            (libc_dir / "test" / "memcpy_test.cpp").write_text(
                "\n".join(
                    [
                        "// @verifies string.memcpy.B1",
                        "TEST(Suite, Name) {}",
                    ]
                ),
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libc_dir)
            self.assertEqual(code, 1)
            self.assertIn("duplicate behavior id declared: string.memcpy.B1", stderr)
            self.assertIn("Duplicate behavior IDs (1):", stdout)

    def test_fails_on_dangling_annotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            libc_dir = self._make_libc_tree(tmpdir)
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
            (libc_dir / "test" / "memcpy_test.cpp").write_text(
                "// @verifies string.memcpy.B1\n",
                encoding="utf-8",
            )

            code, stdout, stderr = self._run_main(libc_dir)
            self.assertEqual(code, 1)
            self.assertIn("dangling @verifies annotation", stderr)
            self.assertIn("Unmapped behaviors (1):", stdout)


if __name__ == "__main__":
    unittest.main()
