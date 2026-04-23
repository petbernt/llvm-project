# Methodology for Behavior Mapping and Qualification Evidence

This document describes a practical workflow for building qualification-style
evidence for an LLVM library component using the behavior-mapping PoC in this
branch.

It is intentionally pragmatic. The goal is not to claim formal qualification by
itself, but to make the work repeatable and auditable:
- break a function down into explicit behaviors
- map those behaviors to concrete tests
- verify that the mapped tests exist and run
- use coverage as a gap-finding tool
- add or refine tests where behaviors are not adequately exercised

The current PoC is libc-local and hosted-test oriented, but the workflow is
meant to scale to other LLVM libraries with similar needs.

## Short Version

For one function, the intended loop is:

1. Add behavior entries in `libc/behavior/*.yaml`.
2. Annotate tests with `// @verifies <BEHAVIOR_ID>`.
3. Run the validator.
4. Run the execution-aware report.
5. Run coverage for the mapped tests.
6. Add or tighten tests if a behavior is unmapped or insufficiently exercised.
7. Re-run the same commands until the evidence is coherent.

Typical commands:

```bash
# Source-level consistency check.
python3 libc/utils/behavior_mapping_check.py

# If configured with LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON:
ninja -C <build-dir> check-libc-behavior-mapping

# Execution-aware report for one function.
python3 libc/utils/behavior_mapping_report.py \
  --build-dir <build-dir> \
  --functions memchr \
  --run-tests

# End-to-end hosted coverage for one function.
./run_libc_behavior_coverage.sh -- memchr
```

## Principles

- Keep the unit of work small.
  Start with one function or one narrow API surface.
- Describe observable behavior, not implementation structure.
  The methodology should survive internal refactors.
- Treat traceability and coverage as complementary evidence.
  A mapped test proves intent. Coverage helps check execution and find holes.
- Prefer reviewable incremental changes.
  Behavior metadata, test annotations, new tests, and reporting support should
  each be understandable on their own.
- Be explicit about scope limits.
  Hosted unit-test coverage is not the same thing as complete implementation
  coverage across all architectures and build modes.

## Recommended PoC Scope

For a first PoC on one function, choose a target with:
- small or medium API surface
- already existing unit tests
- low ambiguity about observable behavior
- clear failure modes or edge cases

Good examples are string and memory primitives such as `memchr`, `memcmp`,
`strlen`, or `strncpy`.

Avoid starting with:
- APIs that depend heavily on platform state
- APIs with many locale, threading, or environment interactions
- functions whose behavior is mostly delegated through many target-specific
  entrypoints

## End-to-End Workflow

1. Choose one function and define the intended scope.
   Decide what this PoC will and will not cover for that function.

2. Break the function into behavior statements.
   Add behavior entries in `libc/behavior/*.yaml` using stable IDs.

3. Review existing tests against those behaviors.
   Identify which tests already exercise a behavior and which behaviors have no
   obvious test.

4. Annotate tests with `// @verifies <BEHAVIOR_ID>`.
   Only annotate a test when the relationship is clear and intentional.

5. Run the source-level validator.
   Check for unknown IDs, duplicates, and unmapped behaviors.

6. Run the execution-aware report.
   Confirm that mapped tests correspond to built executables and can be run.

7. Generate coverage from the mapped test set.
   Use coverage to identify control-flow or helper paths not exercised by the
   currently mapped tests.

8. Add or refine tests where needed.
   Fill behavior gaps first. Then use coverage to refine execution evidence.

9. Re-run validation and coverage.
   The final state should be internally consistent and reproducible.

10. Capture limitations.
   Record any behaviors intentionally left unmapped, platform-specific gaps, or
   implementation variants not included in the hosted coverage run.

## Build Setup

For the validator alone, no special build is required.

For the execution-aware report and coverage flow, configure libc with behavior
mapping enabled:

```bash
cmake -B <build-dir> -S runtimes -G Ninja \
  -DLLVM_ENABLE_RUNTIMES=libc \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DLLVM_INCLUDE_TESTS=ON \
  -DLLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON
```

If you want the coverage flow from this branch-local PoC, also enable coverage
instrumentation:

```bash
cmake -B <build-dir> -S runtimes -G Ninja \
  -DLLVM_ENABLE_RUNTIMES=libc \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DLLVM_INCLUDE_TESTS=ON \
  -DLLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON \
  -DLLVM_BUILD_INSTRUMENTED_COVERAGE=ON
```

## How to Write Behavior Statements

A behavior statement should describe something externally meaningful about the
function.

Good behavior statements usually cover:
- return value semantics
- side effects on memory or outputs
- zero-length or empty-input behavior
- bounds or no-access behavior
- null-check or contract behavior when enabled
- ordering or first-match semantics
- sign or comparison semantics

Avoid behavior statements that merely restate implementation details such as:
- "uses helper X"
- "compares in a loop"
- "dispatches to Y on x86_64"

Those may matter for performance or structure, but they are not stable behavior
requirements.

## How Fine-Grained the Breakdown Should Be

Too coarse:
- one behavior entry for an entire function

Too fine:
- one behavior entry per line of code

A useful middle ground is:
- one behavior per distinct externally reviewable claim

For example, for a simple memory function, a reasonable split might be:
- normal result for valid non-empty input
- zero-count does not access the buffers
- return value points to destination or first match
- no overwrite or no read outside the permitted range
- null-pointer contract trap when null checks are enabled

## How to Map Behaviors to Tests

Use `// @verifies <BEHAVIOR_ID>` directly above the test case that provides the
evidence.

Mapping rules:
- annotate only the tests that intentionally verify the behavior
- it is fine for one test to verify multiple related behaviors
- it is fine for one behavior to be covered by more than one test
- do not annotate speculative or incidental coverage
- do not use annotations as a substitute for improving a weak test

A good mapping answers:
- if this behavior regresses, which test is expected to fail?

If that answer is unclear, the behavior is probably not mapped well enough yet.

## How to Evaluate Existing Tests

For each behavior:
- identify the exact test or tests that claim to verify it
- inspect whether the assertions really match the behavior text
- check whether the test is portable, hosted-only, Linux-only, or config-gated
- note whether the test exercises the direct wrapper, an internal helper, or
  both

Common outcomes:
- the behavior already has a strong mapped test
- the behavior is partially exercised but not asserted clearly enough
- the behavior is only covered incidentally and needs a dedicated test
- the behavior is completely untested

## Role of the Validator

The validator is the first consistency gate. It answers:
- are all `@verifies` IDs known?
- are behavior IDs unique?
- are any documented behaviors currently unmapped?

This is necessary but not sufficient. A passing validator means the metadata and
annotations are internally consistent. It does not prove the binaries were built
or executed.

How to run it:

```bash
# From the repository root.
python3 libc/utils/behavior_mapping_check.py
```

Or, if you configured libc with `LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON`:

```bash
ninja -C <build-dir> check-libc-behavior-mapping
```

How to use the result:
- unknown ID: an annotation references a behavior that does not exist
- duplicate ID: two behaviors use the same identifier
- unmapped behavior: the behavior is documented, but no test claims to verify it

## Role of the Execution-Aware Report

The execution-aware report adds the next layer of evidence:
- which annotated test sources correspond to built test executables
- whether those executables were actually run
- whether they passed or failed

This helps answer:
- do the mapped tests exist in the current build?
- are they only source annotations, or are they live test artifacts?

How to run it:

```bash
# Report for all currently modeled functions in the build tree.
python3 libc/utils/behavior_mapping_report.py --build-dir <build-dir>

# Limit to one function and execute the discovered test binaries.
python3 libc/utils/behavior_mapping_report.py \
  --build-dir <build-dir> \
  --functions memchr \
  --run-tests

# Write JSON for downstream inspection.
python3 libc/utils/behavior_mapping_report.py \
  --build-dir <build-dir> \
  --functions memchr \
  --run-tests \
  --json-output report.json
```

What to look for:
- no discovered binary: the mapped test source does not correspond to a built
  executable in the current build
- failed execution: the test exists but did not pass
- pass with execution evidence: the mapped test is both present and runnable

## Role of Coverage

Coverage is best used here as a gap-finding and confirmation tool, not as the
sole proof of correctness.

Useful questions for coverage:
- does the mapped test set execute the function wrapper at all?
- are obvious branches or contract checks unexercised?
- are helper paths being reached from the mapped tests?
- did a newly added test actually reach the intended logic?

Coverage should not be over-claimed:
- line coverage alone does not prove a behavior is tested
- branch coverage alone does not prove the assertions are meaningful
- wrapper coverage may hide that important work happens in internal helpers
- hosted coverage may exclude target-specific optimized implementations

## How to Use Coverage in This PoC

The current helper is:

`./run_libc_behavior_coverage.sh`

Current branch behavior:
- auto-discovers functions from `libc/behavior/*.yaml` by default
- runs the mapped hosted unit binaries
- merges raw profiles
- emits a text report and HTML report
- restricts inputs to exact plain `__unit__` binaries by default

How to run it:

```bash
# All currently modeled functions.
./run_libc_behavior_coverage.sh

# One function.
./run_libc_behavior_coverage.sh -- memchr

# A small selected set.
./run_libc_behavior_coverage.sh -- memcpy memset memcmp
```

Important outputs:
- `behavior-report.log`
- `behavior-report.json`
- `llvm-cov-report.txt`
- `coverage-html/index.html`

Recommended usage pattern:
- start with the mapped function set for one function
- inspect the HTML report for the wrapper source
- if the wrapper delegates, inspect relevant helper sources too
- use `--show-expansions` output in the HTML view to understand macro-driven
  branches such as null checks

## How to Decide When a New Test Is Needed

Add a new test when any of the following is true:
- a documented behavior has no mapped test
- a mapped test does not make the intended assertion clearly enough
- coverage shows an important branch or contract path is never exercised
- the only current evidence is incidental coverage from a broad sweep test
- behavior differs under a config guard and that mode has no direct test

Do not add a new test just to increase coverage numbers if it does not improve
behavior evidence.

## Preferred Test Additions

The best new tests are:
- narrow
- named after the behavior they verify
- explicit about the expected result
- stable across implementation refactors

Examples:
- zero-count does not access memory
- returns first matching character
- comparison uses unsigned character ordering
- crash-on-null is enforced when null checks are enabled

## What to Do When Coverage Looks Wrong

Coverage reports often need interpretation.

Common causes of confusion:
- branches introduced by macros such as `LIBC_CRASH_ON_NULLPTR`
- coverage attributed to wrapper files while the work happens in helpers
- trap paths not flushing profile data cleanly
- multiple binaries with different implementations causing noisy merged data

Debugging steps:
- inspect the HTML report with macro expansions
- compare wrapper coverage with helper coverage
- reduce the binary set to the exact unit binaries for the mapped function
- confirm which tests actually ran in the behavior report log

Useful commands when debugging:

```bash
# See which functions are currently modeled.
python3 libc/utils/behavior_mapping_report.py \
  --libc-dir libc \
  --print-functions

# See which binaries a mapped function resolves to.
python3 libc/utils/behavior_mapping_report.py \
  --build-dir <build-dir> \
  --functions memchr \
  --print-binaries
```

## Evidence Expected at the End of One Function PoC

A credible one-function PoC should end with:
- behavior entries for that function in `libc/behavior/*.yaml`
- test annotations that map behaviors to concrete tests
- a passing validator run
- an execution-aware report showing the mapped tests were built and executed
- a coverage report for the selected mapped test set
- at least one example of adding or tightening a test because the methodology
  exposed a real gap
- a short note on remaining limitations

## Suggested Review Questions

When reviewing a contribution produced with this methodology, ask:
- are the behavior statements clear, stable, and externally meaningful?
- do the mapped tests really verify what the behavior text claims?
- are any important behaviors still unmapped?
- is the coverage being interpreted correctly and not over-claimed?
- are config-specific or platform-specific cases documented clearly?
- did the work improve evidence, or only add process overhead?

## Patch Structuring Guidance

For upstreamable work, a clean sequence is usually:
- strengthen or add tests where needed
- add behavior metadata for a narrow function set
- add `@verifies` annotations
- add or update validation/report tooling
- add documentation

For branch-local PoC work, it is acceptable to keep the methodology document and
coverage helper together, but the changes should still be reviewable in small
steps.

## Current Limitations of This PoC

This branch does not yet provide:
- proof of complete implementation coverage across all targets
- proof that every optimized architecture-specific entrypoint is exercised
- formal qualification artifacts by itself
- automatic proof that an annotation is semantically correct

What it does provide is a structured workflow for making the evidence better,
more queryable, and easier to review.
