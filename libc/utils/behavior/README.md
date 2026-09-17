# Behavior traceability checker

See the [overview](../../behavior/README.md) for the concept and the
[methodology](../../behavior/methodology.md) for adding behaviors and annotations.
Run the commands below from the repository root.

## Traceability checker

`check.py` validates behavior IDs and their `@verifies` references in test source.
It prints the mapping and fails on unmapped behaviors, unknown IDs, duplicate
IDs, or dangling annotations. No configuration or build is required:

```bash
python3 libc/utils/behavior/check.py
```

The checker extracts IDs from the files; it does not validate YAML syntax or a
metadata schema. See [planned schema validation](../../behavior/methodology.md#metadata-schema-future-work).

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
