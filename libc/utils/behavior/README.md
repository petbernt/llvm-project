# Behavior traceability checker

See the [overview](../../behavior/README.md) for the concept and the
[methodology](../../behavior/methodology.md) for adding behaviors and annotations.
Run the commands below from the repository root.

## Traceability checker

`check.py` validates behavior IDs and their `@verifies` references in test source.
It prints the mapping and fails on unmapped behaviors, unknown IDs, duplicate
IDs, dangling annotations, or an empty behavior inventory. No configuration or
build is required:

```bash
python3 libc/utils/behavior/check.py
```

The checker extracts IDs from the files; it does not validate YAML syntax or a
metadata schema. See [planned schema validation](../../behavior/methodology.md#metadata-schema-future-work).

Use indented `behaviors:` lists with each `id:` on its own line. IDs can be
unquoted, single-quoted, or double-quoted; inline YAML lists are not supported.
Place one `// @verifies <ID>` per line directly above a `TEST`, `TEST_F`, `TEST_P`,
`TYPED_TEST`, or `TYPED_TEST_P` declaration, whose arguments may span lines.
Only whitespace or further annotation lines may intervene. Wrapper macros that
generate tests are not expanded.

For CI, [configure libc](../../behavior/methodology.md#enforce-the-same-check-in-ci)
with `-DLLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON` and run:

```bash
ninja -C <build-dir> check-libc-behavior-mapping
```

This target runs the validator and its Python unit tests. It returns a
nonzero status on failure, with captured output shown by CTest. It does not
build or run libc's test executables.

## Tests for the checker

These test the validator itself, including its failure conditions:

```bash
python3 libc/utils/behavior/tests/check_test.py
```
