# Behavior-to-test traceability workflow

This PoC connects selected libc++ behaviors to the tests intended to verify them:

**Standard or documented choice → behavior ID → test source location**

The checker validates links between behavior IDs and test annotations. Reviewers
assess the source references, behavior descriptions, and test assertions. A
consistent mapping alone does not establish complete standards conformance.

## Add a behavior and map it to a test

Work on one API at a time. Add or extend its entry in `libcxx/behavior/*.yaml`,
using one file per header. Record the source, usually an ISO C++ standard edition
and library clause, and identify the applicable overload and preconditions.
The current entries describe selected C++23 APIs. In `signature`, use a
declaration including the function name, parameters, and applicable qualifiers.
Member declarations use their class context, for example `std::array<T, N>`.
For several overloads, list their declarations in a multiline `signature` string,
as for `std::equal`. Qualify behavior descriptions when overloads differ. The
checker does not parse these declarations or select the tests' language mode.

Describe each observable behavior in concise, original wording and give it a
unique, stable ID. Keep each entry specific enough to map to an assertion or
small test block.

For example, [libcxx/behavior/algorithm.yaml](algorithm.yaml) contains this entry
under `functions["std::copy"].behaviors`. The complete function entry also records
its source reference, signature, and preconditions:

```yaml
- id: "algorithm.copy.B2"
  kind: "Returns"
  source: { inherits: "function", classification: "mandated" }
  text: "Returns an iterator to the end of the result range."
```

Here, `inherits: "function"` refers to the function's source, the C++23 clause
`[alg.copy]`. The classification records that the behavior is mandated by that
source; the description is a non-normative summary.

Add `// @verifies <BEHAVIOR_ID>` near the assertion or helper block that verifies
the behavior. This excerpt from the iterator test helper in
[libcxx/test/std/algorithms/alg.modifying.operations/alg.copy/copy.pass.cpp](../test/std/algorithms/alg.modifying.operations/alg.copy/copy.pass.cpp)
references the same behavior ID:

```cpp
OutIter r = std::copy(InIter(ia), InIter(ia + N), OutIter(ib));
// @verifies algorithm.copy.B2
assert(base(r) == ib + N);
```

The complete test file supplies the arrays and iterator types. The assertion
checks that the returned iterator points just past the copied output range.
The checker connects the YAML entry and this source location through their
shared behavior ID; the YAML does not need a test-file path.

Reuse suitable assertions or add a separate, focused test where verification is
missing, preserving existing upstream tests. Do not add annotations just to
silence the checker. Use one annotation per behavior ID; a block can have several
annotations, and a behavior can be mapped to several locations. Every declared
behavior needs a mapping; tests without annotations are allowed.

## Check traceability locally

From the repository root, run:

```bash
python3 libcxx/utils/behavior/check.py
```

No CMake configuration or build is required. The checker prints a matrix from
behavior IDs to annotation locations, with paths relative to `libcxx/`, and
returns a nonzero exit status if it finds:

- A documented behavior with no mapped annotation.
- An annotation referencing an unknown behavior ID.
- A duplicate behavior ID.
- No behavior IDs found.

Update the descriptions, tests, or annotations as needed, then rerun the checker.
It scans text without interpreting C++ or lit conditions: an annotation can
still be counted if its assertion is removed or excluded from a test run.
Review the mapping and use the [normal libc++ test workflow](../docs/TestingLibcxx.rst)
to validate test changes. Traceability checking itself does not build or execute
those tests or measure their coverage.

## Enforce the same check in CI

Add `-DLIBCXX_INCLUDE_BEHAVIOR_MAPPING=ON` to the CI job's libc++ CMake
configuration, then run the target below. For a new build directory, follow the
[default runtimes configuration](../docs/VendorDocumentation.rst#the-default-build)
and add the same option. `<build-dir>` refers to the directory configured from
`runtimes/`.

```bash
ninja -C <build-dir> check-libcxx-behavior-mapping
```

Use this command's exit status to fail the CI step when traceability is broken.
The target runs the checker and its Python unit tests; CTest shows captured
output on failure. It requires a configured build directory, but does not
require building the library or libc++ test executables first. The option is
off by default; enabling it makes the target available, and the CI job must
invoke it explicitly.

## Metadata schema (future work)

The metadata contents and required fields are still being defined. The current
checker extracts behavior IDs from YAML text; it does not validate YAML syntax
or a metadata schema. The existing files illustrate the current format; see
the [tool reference](../utils/behavior/README.md#supported-input-and-limitations)
for extraction limits.

Future work is to agree the metadata model, define a schema for its structure,
required fields, types, and allowed values, and add schema validation before
the traceability checks in CI. Reviewing the meaning of the metadata would
still be necessary.

## Optional AI workflows (future work)

Once the manual workflow and review expectations have been validated, reusable
prompts or agent skills could assist with three steps:

1. **Draft behaviors:** break down cited requirements or documented choices into
   concise, atomic entries with stable IDs and explicit sources. Write original,
   non-normative summaries and identify overloads and preconditions.
2. **Find existing tests:** inspect assertions and propose mappings to the
   behaviors they verify. Explain which assertions support each mapping and flag
   uncertain matches or missing tests for review.
3. **Add tests for gaps:** propose a separate, focused test and its annotation
   when no suitable test is found. Build and run it through the normal libc++
   test workflow, then rerun the traceability checker.

These would be optional contributor tools developed separately from the core
traceability mechanism; no AI tooling is currently provided or required.
Generated descriptions, mappings, and tests remain proposals for human review
at each step. Any use must follow the
[LLVM AI Tool Use Policy](../../llvm/docs/AIToolPolicy.md), including contributor
review before submitting changes for maintainer review.

## Further reading

- [Overview](README.md): the concept and its scope.
- [Tool reference](../utils/behavior/README.md): checker commands and unit tests.
