# Debugging Skill

## Purpose
Diagnose failing code, tests, tools, or generated artifacts and propose focused repairs.

## Usage Conditions
Use after exceptions, failed tests, failed evaluations, or broken deployment checks.

## Input Format
- Failure summary
- Logs and traces
- Relevant files
- Recent changes

## Execution Steps
1. Localize the failure from available evidence.
2. Identify the smallest likely root cause.
3. Propose a targeted repair.
4. Define verification commands or checks.

## Output Schema
- root_cause
- fix_plan
- affected_files
- verification
- residual_risk

## Quality Checks
- The fix addresses the observed failure.
- The verification checks the repaired behavior.

## Failure Handling
If evidence is insufficient, request the missing log, trace, or file path.
