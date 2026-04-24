# Behavior Utility Scripts

This directory contains the helper scripts used by the libc behavior-mapping
PoC.

## Scripts

- `check.py`
  Source-level validator for behavior YAML files and `@verifies` annotations.
- `report.py`
  Execution-aware reporter that maps annotations to built unit-test binaries and
  can run them.

## Tests

- `check_test.py`
  Unit tests for the source-level validator.
- `report_test.py`
  Unit tests for the execution-aware reporter.

The test files are kept next to the scripts for now because the test surface is
still small.

## Common Commands

Run the source-level validator from the repository root:

```bash
python3 libc/utils/behavior/check.py
```

Run the execution-aware report against an existing libc build:

```bash
python3 libc/utils/behavior/report.py --build-dir <build-dir> --run-tests
```

Run the script unit tests:

```bash
python3 libc/utils/behavior/check_test.py
python3 libc/utils/behavior/report_test.py
```

If libc is configured with `LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`, CMake also
provides:

```bash
ninja -C <build-dir> check-libc-behavior-mapping
ninja -C <build-dir> report-libc-behavior-mapping
```
