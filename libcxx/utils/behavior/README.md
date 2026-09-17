# Behavior traceability checker

See the [overview](../../behavior/README.md) for the concept and the
[workflow](../../behavior/methodology.md) for adding behaviors and annotations.
Run the commands below from the repository root. The checker and its unit tests
use Python 3's standard library; no additional Python packages are required.

## Traceability checker

`check.py` scans `libcxx/behavior/**/*.yaml` and files under `libcxx/test/`.
It prints a Markdown matrix from behavior IDs to annotation file-and-line
locations, with paths relative to `libcxx/`. No configuration or build is required:

```bash
python3 libcxx/utils/behavior/check.py
```

It exits with status 1 for unmapped behaviors, unknown referenced IDs, duplicate
IDs, or an empty behavior inventory, and status 2 if the behavior or test
directory is missing. Use
`--libcxx-dir <path-to-libcxx>` to check a different source tree.

For CI, [configure libc++](../../behavior/methodology.md#enforce-the-same-check-in-ci)
with `-DLIBCXX_INCLUDE_BEHAVIOR_MAPPING=ON` and run:

```bash
ninja -C <build-dir> check-libcxx-behavior-mapping
```

This target runs the checker and its Python unit tests. It returns a nonzero
status on failure, with captured output shown by CTest. It does not build or run
libc++'s test executables.

## Tests for the checker

These test the validator itself, including its failure conditions:

```bash
python3 libcxx/utils/behavior/tests/check_test.py
```

## Supported input and limitations

Use indented `behaviors:` lists with each `id:` on its own line, as in the
existing metadata files. IDs may be unquoted or double-quoted; single-quoted
IDs and inline YAML lists are not supported. Use letters, digits, underscores,
dots, and hyphens in IDs so they can be referenced by annotations.

Place one `// @verifies <ID>` per line near the relevant assertion or helper
block. The checker finds matching text and records the annotation's location;
it does not associate it with a C++ declaration or assertion. It does not parse
comments or string literals, or evaluate preprocessor or lit conditions.

The checker does not validate YAML syntax, source references, or a metadata
schema. See
[planned schema validation](../../behavior/methodology.md#metadata-schema-future-work).
