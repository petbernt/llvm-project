# libc++ behavior-to-test traceability

This opt-in PoC makes the intended relationship between selected libc++ behaviors
and their tests explicit:

**Standard or documented choice → behavior ID → test source location**

Behavior descriptions in [algorithm.yaml](algorithm.yaml) and
[array.yaml](array.yaml) record source references and stable behavior IDs. The
current scope is `std::copy`, `std::fill`, `std::equal`, and selected `std::array`
operations. These are concise, non-normative descriptions, maintained through
normal code review.

Tests reference the IDs through `// @verifies` annotations near relevant
assertions or helper blocks. The checker reports each annotation's file and line,
which suits libc++ tests containing several checks in one file. It detects
unmapped behaviors, unknown references, duplicate behavior IDs, and an empty
behavior inventory.

The workflow validates these source-level links locally or in CI, without
building libc++ or running its tests. Reviewers assess the source interpretation,
behavior descriptions, and whether assertions adequately verify them. A passing
check establishes mapping consistency.

The metadata model and YAML schema validation remain
[future work](methodology.md#metadata-schema-future-work). A passing traceability
check does not establish that the complete YAML metadata is valid.

Optional [AI workflows](methodology.md#optional-ai-workflows-future-work) for
drafting behaviors, finding tests, and adding missing tests are also future work.

Start with the [workflow](methodology.md) for a worked example and CI setup.
The [tool reference](../utils/behavior/README.md) lists commands, supported input,
and checker tests.
