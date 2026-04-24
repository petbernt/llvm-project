# libc behavior mapping experiment

This directory contains small, non-normative behavior descriptions for selected
llvm-libc functions.

The PoC is centered on two questions:
- which behaviors are documented?
- which tests claim to verify them?

For the workflow document, see `libc/behavior/methodology.md`.

## Layout

- `libc/behavior/*.yaml`
  Behavior metadata for the currently modeled functions.
- `libc/utils/behavior/check.py`
  Source-level validator for behavior IDs and `@verifies` annotations.
- `libc/utils/behavior/report.py`
  Execution-aware report that maps annotations to built unit-test binaries.

## What The Scripts Do

- `check.py`
  Reads the YAML files and test annotations, then reports unknown IDs,
  duplicate IDs, and documented behaviors that still have no mapped test.
- `report.py`
  Starts from the same mapping, then looks in a build tree for the matching
  unit-test binaries. It can also run those binaries and emit JSON.

The layering is intentional:
- use `check.py` to validate the mapping
- use `report.py` to confirm the mapped tests exist and run

## Common Commands

Run the source-level validator:

```bash
python3 libc/utils/behavior/check.py
```

Run the validator through CMake after configuring libc with
`-DLLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`:

```bash
ninja -C <build-dir> check-libc-behavior-mapping
```

Run the execution-aware report and execute the discovered test binaries.
If `--functions` is omitted, it reports all functions with behavior IDs
declared in `libc/behavior/*.yaml`:

```bash
python3 libc/utils/behavior/report.py --build-dir <build-dir> --run-tests
```

Limit that report to selected functions:

```bash
python3 libc/utils/behavior/report.py \
  --build-dir <build-dir> \
  --functions memcpy memset
```

## Notes

The source-level checker is the first consistency gate. It answers whether the
metadata and annotations agree, not whether the corresponding binaries were
built or executed.

The report script adds that build-tree view when you point it at an existing
libc build.

## Script Tests

Run the checker script tests from the repository root:

```bash
python3 libc/utils/behavior/tests/check_test.py
```

Run the reporting script tests:

```bash
python3 libc/utils/behavior/tests/report_test.py
```
