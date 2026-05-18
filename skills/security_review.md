# Security Review Skill

## Purpose
Identify security, privacy, permission, and secret-handling risks.

## Usage Conditions
Use before deployment, before terminal/API actions, and when generated code touches auth, data, files, or network.

## Input Format
- Requirement
- Artifacts
- Tool actions
- Environment variables

## Execution Steps
1. Scan for hardcoded secrets and unsafe commands.
2. Check auth, input validation, and file/network boundaries.
3. Identify destructive or external actions.
4. Recommend mitigations and approval requirements.

## Output Schema
- passed
- findings
- severity
- blocked_actions
- mitigations

## Quality Checks
- High-risk findings block deployment.
- Findings include file paths or action names where possible.

## Failure Handling
If risk cannot be assessed, require human approval before proceeding.
