# Behavior Utility Scripts

This directory contains helper scripts used by the libc++ behavior-mapping PoC.

## Scripts

- `check.py`
  Source-level validator for behavior YAML files and `@verifies` annotations.

## Tests

- `tests/check_test.py`
  Unit tests for the source-level validator.

## Common Commands

Run the source-level validator from the repository root:

```bash
python3 libcxx/utils/behavior/check.py
```

Run the script unit tests:

```bash
python3 libcxx/utils/behavior/tests/check_test.py
```

If libc++ is configured with `LIBCXX_INCLUDE_BEHAVIOR_MAPPING=ON`, CMake also
provides:

```bash
ninja -C <build-dir> check-libcxx-behavior-mapping
```
