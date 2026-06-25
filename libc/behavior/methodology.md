# Methodology for Behavior Mapping

This PoC is a lightweight workflow for making selected libc test intent explicit
and machine-checkable. It is meant to answer a practical question:

"Can we describe a function's intended behavior, map that behavior to tests,
and check that the mapping stays internally consistent?"

It does not claim formal qualification of LLVM itself.

## Goal

For each selected function:
- document observable behaviors in `libc/behavior/*.yaml`
- map those behaviors to tests with `// @verifies <BEHAVIOR_ID>`
- validate that the mapping is internally consistent
- run the mapped tests when a build tree is available
- add or tighten tests where the mapping exposes gaps

## Scope

This branch is intentionally narrow:
- libc-local
- hosted unit-test oriented
- best suited to simple deterministic functions such as string and memory APIs

The report output should be read as evidence about selected unit-test binaries,
not as complete evidence for every architecture-specific implementation.

## Workflow

1. Pick one function.
   Start small. A single function is the intended unit of work.

2. Add behavior entries.
   Describe externally visible behavior in `libc/behavior/*.yaml`. Include
   source metadata that distinguishes ISO C, POSIX, extension, and LLVM-libc
   documented-choice behavior.

3. Map behaviors to tests.
   Add `// @verifies <BEHAVIOR_ID>` directly above the test case that is meant
   to verify that behavior.

4. Run the validator.
   Check for unknown IDs, duplicates, and documented behaviors that still have
   no mapped test.

5. Run the execution-aware report.
   Check which mapped tests correspond to built unit-test binaries and whether
   those binaries pass.

6. Add or tighten tests where needed.
   Fix unmapped behaviors first. Then inspect whether the mapped tests assert
   each behavior clearly enough.

7. Re-run the same commands.
   Keep the loop tight until the mapping and test set are coherent.

## Commands

Run the source-level validator from the repository root:

```bash
python3 libc/utils/behavior/check.py
```

If libc was configured with `LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`, the same
check is also available as a CMake target:

```bash
ninja -C <build-dir> check-libc-behavior-mapping
```

Run the execution-aware report for one function:

```bash
python3 libc/utils/behavior/report.py \
  --build-dir <build-dir> \
  --functions memchr \
  --run-tests
```

## When To Add Tests

Add a new test or improve an existing one when:
- a documented behavior has no `@verifies` mapping
- the mapped test exists but does not assert the behavior clearly
- the mapped test does not correspond to a built and runnable unit-test binary

Do not add annotations just to silence the validator. The mapping should reflect
intentional verification.

## Limitations

- This is not certification evidence by itself.
- It does not cover every target-specific implementation variant.
- It depends on the hosted libc unit-test setup used in this branch.
- Some behaviors may still need analysis or additional tests before the mapping
  is strong enough to be reused downstream.
