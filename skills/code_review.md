# Code Review

Review generated artifacts for bugs, missing behavior, maintainability risks, and integration gaps.

Rules:
- List concrete bugs in the `bugs` field.
- Keep bug descriptions actionable and specific.
- Flag missing tests, broken imports, unsafe paths, and deployment mismatches.
- If no blocking bugs are found, return an empty `bugs` list.

