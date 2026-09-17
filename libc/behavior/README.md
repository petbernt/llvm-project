# libc behavior-to-test traceability

This PoC makes the intended relationship between selected libc behaviors and
their tests explicit:

**Standard or documented choice → behavior ID → test case**

Behavior descriptions in [string.yaml](string.yaml) and [stdlib.yaml](stdlib.yaml)
record source references, preconditions, and behavior IDs. Tests reference those
IDs through `// @verifies` annotations. The checker detects missing mappings,
unknown references, duplicate IDs, and annotations without a following test.

The main workflow validates these source-level links locally or in CI, without
building libc or running its tests. Reviewers assess the behavior descriptions
and whether the test assertions adequately verify them.

The metadata model and YAML schema validation remain
[future work](methodology.md#metadata-schema-future-work). A passing traceability
check does not establish that the complete YAML metadata is valid.

Start with the [methodology](methodology.md) for a worked example and CI setup.
The [tool reference](../utils/behavior/README.md) lists commands and prerequisites.
