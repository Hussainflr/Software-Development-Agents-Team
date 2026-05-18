# Evaluation Skill

## Purpose
Score generated artifacts against the original requirement and production-readiness criteria.

## Usage Conditions
Use after testing, review, security analysis, or before deployment approval.

## Input Format
- Requirement
- Artifact manifest
- Test results
- Known bugs
- Reviewer findings

## Execution Steps
1. Check requirement alignment.
2. Score correctness, completeness, code quality, and safety.
3. Detect hallucinated or inconsistent artifacts.
4. Decide whether to approve, refine, retry, or fail.

## Output Schema
- correctness
- completeness
- code_quality
- security
- passed
- findings
- repair_instructions

## Quality Checks
- Scores are justified by evidence.
- Failed checks map to concrete repair actions.

## Failure Handling
If artifacts are missing or inconsistent, fail evaluation and send feedback to the responsible agent.
