# Methodology for Conformance Test Traceability

This PoC is a lightweight workflow for attaching explicit conformance-test
intent to selected libc++ tests. It is meant to answer a practical question:

"Can we describe a standard-library API's externally visible behavior, map that
behavior to tests, and check that the mapping does not silently drift?"

It does not claim formal qualification of LLVM or libc++.

## Goal

For each selected API:
- document observable behavior in `libcxx/behavior/*.yaml`
- map that behavior to tests with `// @verifies <BEHAVIOR_ID>`
- validate that the mapping is internally consistent
- keep the modeled set small enough to review by normal libc++ standards

## Scope

This branch is intentionally narrow:
- libc++-local
- source-level only
- focused on simple, useful standard-library APIs
- best suited to behaviors already exercised by existing lit tests

The initial modeled set is:
- `std::copy`
- `std::fill`
- `std::equal`
- selected `std::array` observers and modifiers

## Workflow

1. Pick one small API.
   Start with behavior that is already easy to explain from the Standard.

2. Add behavior entries.
   Describe externally visible behavior in `libcxx/behavior/*.yaml`.

3. Map behaviors to tests.
   Add `// @verifies <BEHAVIOR_ID>` near the assertions or helper block that
   is meant to verify that behavior.

4. Run the validator.
   Check for unknown IDs, duplicate IDs, and documented behaviors that still
   have no mapped test.

5. Tighten tests where needed.
   Do not add annotations just to silence the validator. The mapping should
   reflect intentional verification.

## Commands

Run the source-level validator from the repository root:

```bash
python3 libcxx/utils/behavior/check.py
```

If libc++ was configured with `LIBCXX_INCLUDE_BEHAVIOR_MAPPING=ON`, the same
check is also available as a CMake target:

```bash
ninja -C <build-dir> check-libcxx-behavior-mapping
```

## Limitations

- This is not certification evidence by itself.
- It does not provide a complete downstream evidence package.
- It does not attempt coverage measurement yet.
- It depends on source annotations in libc++ tests.
- Some behaviors may need further review to confirm that they are the right
  refinement of the Standard wording.
