# Testing Skill

## Purpose
Create and run meaningful tests for generated software.

## Usage Conditions
Use whenever code is generated or changed.

## Input Format
- Requirement
- Generated artifacts
- Public interfaces
- Known bugs

## Execution Steps
1. Identify user-visible behavior and API contracts.
2. Write focused unit and integration tests.
3. Include failure-path tests where relevant.
4. Report pass/fail status and actionable defects.

## Output Schema
- test_files
- test_commands
- results
- bugs
- recommendations

## Quality Checks
- Tests align with the requirement.
- Tests do not rely on hidden services unless declared.
- Failures include clear reproduction steps.

## Failure Handling
If tests cannot run locally, explain the blocker and provide a simulated result with risk clearly marked.
