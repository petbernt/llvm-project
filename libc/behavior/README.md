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
- the current scope focuses on simple string and memory primitives that are
  common in low-level code, currently `memcpy`, `memset`, `memcmp`, `memchr`,
  `strlen`, `memrchr`, `strcmp`, `strncmp`, and `strnlen`

This is source-level mapping only. It does not claim that mapped tests were
built, executed, or passed in a particular run.

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

## Checker tests

Run the checker unit tests from the repository root with:

`python3 libc/utils/behavior_mapping_check_test.py`
