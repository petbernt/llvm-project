# libc++ behavior mapping experiment

This directory contains small, non-normative behavior descriptions for selected
libc++ standard-library APIs.

The PoC is centered on three questions:
- which externally visible behaviors are documented?
- which libc++ tests claim to verify them?
- does the source-level mapping stay internally consistent?

For the workflow document, see `libcxx/behavior/methodology.md`.

## Layout

- `libcxx/behavior/*.yaml`
  Behavior metadata for the currently modeled APIs. Files are grouped by
  standard-library header, for example `algorithm.yaml` and `array.yaml`.
- `libcxx/utils/behavior/check.py`
  Source-level validator for behavior IDs and `@verifies` annotations.

## What The Checker Does

`check.py` reads the YAML files and libc++ test annotations, then reports:
- unknown IDs referenced from tests
- duplicate IDs in the metadata
- documented behaviors that still have no mapped test

Unlike the libc PoC, this checker maps annotations to source locations rather
than to GTest case names. libc++ tests are lit tests and commonly express several
checks inside helper functions or blocks, so file-and-line locations are a
better fit for an initial libc++ experiment.

## Common Commands

Run the source-level validator:

```bash
python3 libcxx/utils/behavior/check.py
```

Run the validator through CMake after configuring libc++ with
`-DLIBCXX_INCLUDE_BEHAVIOR_MAPPING=ON`:

```bash
ninja -C <build-dir> check-libcxx-behavior-mapping
```

## Script Tests

Run the checker script tests from the repository root:

```bash
python3 libcxx/utils/behavior/tests/check_test.py
```

## Scope

This is not certification evidence by itself. It is a lightweight experiment for
making test intent queryable and for detecting drift between selected
standard-library behavior descriptions and libc++ tests.
