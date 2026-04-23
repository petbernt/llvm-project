# libc behavior mapping experiment

This directory contains small, non-normative behavior descriptions for selected
llvm-libc functions.

The immediate goal is to make it easier to answer questions such as:
- where is a specific libc behavior tested?
- which documented behaviors currently have no mapped test?
- which test claims to verify a given behavior?

The current experiment is intentionally narrow:
- behavior metadata lives in `libc/behavior/*.yaml`
- tests in `libc/test/` can declare intended coverage with
  `// @verifies <BEHAVIOR_ID>` comments placed directly above the matching test
- `libc/utils/behavior_mapping_check.py` validates that the metadata and
  annotations are internally consistent
- `libc/utils/behavior_mapping_report.py` can optionally match those annotated
  test files to built test executables in a build tree and report pass/fail
  status for executed binaries
- the current scope focuses on simple string and memory primitives that are
  common in low-level code, currently `memcpy`, `memset`, `memcmp`, `memchr`,
  `strlen`, `memrchr`, `strcmp`, `strncmp`, `strnlen`, `strchr`, `strrchr`,
  `strcspn`, `strspn`, and `strnlen_s`

The validator is source-level only. The reporting script adds an optional
execution-aware layer when you point it at a build tree.

## Current workflow

1. Add or update behavior statements in `libc/behavior/*.yaml`.
2. Annotate tests with `@verifies` comments where the intended relationship is
   clear.
3. If you want the CMake target, configure libc with:

   `-DLLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`

4. Run the checker.

   If you configured libc with `LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`, prefer
   the CMake target:

   `ninja -C <build-dir> check-libc-behavior-mapping`

   Or run the script directly from the repository root:

   `python3 libc/utils/behavior_mapping_check.py`

5. Review any unknown IDs, duplicate IDs, or unmapped behaviors.

## Execution-aware report

If you have a libc build tree with the relevant tests built, you can also ask
for a report that joins the source annotations to discovered test executables:

`python3 libc/utils/behavior_mapping_report.py --build-dir <build-dir>`

To execute the discovered test binaries and include pass/fail status:

`python3 libc/utils/behavior_mapping_report.py --build-dir <build-dir> --run-tests`

To limit the report to selected functions:

`python3 libc/utils/behavior_mapping_report.py --build-dir <build-dir> --functions memcpy memset`

If you configured libc with `LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`, there is
also a convenience target:

`ninja -C <build-dir> report-libc-behavior-mapping`

The report script can also write JSON for downstream processing:

`python3 libc/utils/behavior_mapping_report.py --build-dir <build-dir> --run-tests --json-output report.json`

This is a better fit than the validator when you want evidence that a mapped
test binary was actually built and, optionally, executed successfully.

## Notes for memcpy / memset

`memcpy_test.cpp` and `memset_test.cpp` currently mix portable and host-OS
specific coverage.

Portable tests:
- `SizeSweep` in both files does not depend on Linux protected pages.
- `CrashOnNullPtr` in both files does not use protected pages either, but it is
  only built when `LIBC_ADD_NULL_CHECKS` is enabled and still depends on the
  hosted death-test executor rather than bare-metal execution.

Linux protected-page tests:
- `ZeroCountDoesNotAccessMemory`
- `CheckAccess`

Those are both guarded by:

`#if !defined(LIBC_FULL_BUILD) && defined(LIBC_TARGET_OS_IS_LINUX)`

## Checker tests

Run the checker unit tests from the repository root with:

`python3 libc/utils/behavior_mapping_check_test.py`

Run the reporting-script unit tests from the repository root with:

`python3 libc/utils/behavior_mapping_report_test.py`
