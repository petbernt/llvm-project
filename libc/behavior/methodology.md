# Behavior-to-test traceability workflow

This PoC connects selected libc behaviors to the tests intended to verify them:

**Standard or documented choice → behavior ID → test case**

The checker validates links between behavior IDs and test annotations. Reviewers
assess the source references, behavior descriptions, and test assertions. A
consistent mapping alone does not establish complete standards conformance.

## Add a behavior and map it to a test

Work on one function at a time. Add or extend its entry in `libc/behavior/*.yaml`.
Record its source, such as an ISO C clause, POSIX reference, extension, or
LLVM-libc documented choice, along with its preconditions. Give each observable
behavior a unique ID, such as `stdlib.strtol.B4`.

For example, [libc/behavior/stdlib.yaml](stdlib.yaml) contains this entry under
`functions.strtol.behaviors`. The complete function entry also records its source
reference, signature, and preconditions:

```yaml
- id: "stdlib.strtol.B4"
  source: { inherits: "function", classification: "mandated" }
  text: "When no conversion is performed, returns 0 and stores str in str_end if str_end is not null."
```

Add `// @verifies <BEHAVIOR_ID>` immediately above the test that asserts the
behavior. In [libc/test/src/stdlib/strtol_test.cpp](../test/src/stdlib/strtol_test.cpp),
`ReportsNoConversion` references the same behavior ID:

```cpp
// @verifies stdlib.strtol.B4
TEST_F(LlvmLibcStrtolTest, ReportsNoConversion) {
  char *str_end = nullptr;
  const char *input = "word10";

  ASSERT_EQ(LIBC_NAMESPACE::strtol(input, &str_end, 10), 0L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - input, ptrdiff_t(0));
}
```

The checker connects the YAML entry and the test through their shared behavior
ID; the YAML does not need a test-file path.

Reuse a suitable test or add one where coverage is missing. Strengthen assertions
when they do not adequately verify the behavior; do not add annotations just to
silence the checker. A test can have multiple annotations, and a behavior can be
mapped to multiple tests.

## Check traceability locally

From the repository root, run:

```bash
python3 libc/utils/behavior/check.py
```

No CMake configuration or build is required. The checker prints a behavior-to-test
matrix and returns a nonzero exit status if it finds:

- A documented behavior with no mapped test.
- An annotation referencing an unknown behavior ID.
- A duplicate behavior ID.
- An annotation with no following recognized test declaration.

Update the descriptions, tests, or annotations as needed, then rerun the checker.
It scans test source, so a mapped test may still be excluded by build conditions.

## Enforce the same check in CI

Add `-DLLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING=ON` to the CI job's CMake configuration,
then run the target below. For a new build directory, see the
[standalone libc configuration instructions](../docs/overlay_mode.md#building-llvm-libc-as-a-standalone-runtime)
and add the same option.

```bash
ninja -C <build-dir> check-libc-behavior-mapping
```

Use this command's exit status to fail the CI step when traceability is broken.
The target runs the validator and its Python unit tests; CTest shows
captured output on failure. It requires a configured build directory, but does
not require building the library or libc test executables first.
Enabling the option makes the target available; the CI job must invoke it explicitly.

## Metadata schema (future work)

The metadata contents and required fields are still being defined. The current
checker extracts behavior IDs from YAML text; it does not validate YAML syntax
or a metadata schema. The existing files illustrate the current format.

Future work is to agree the metadata model, define a schema for its structure,
required fields, types, and allowed values, and add schema validation before
the traceability checks in CI. This would validate the inputs to the traceability
workflow; reviewing their meaning would still be necessary.

## Further reading

- [Overview](README.md): the concept and its scope.
- [Tool reference](../utils/behavior/README.md): checker commands and unit tests.
