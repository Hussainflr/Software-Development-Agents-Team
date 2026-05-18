# Deployment Skill

## Purpose
Prepare local-first deployment artifacts and operator instructions.

## Usage Conditions
Use only after tests and evaluation pass, and after human approval when required.

## Input Format
- Generated backend/frontend files
- Runtime requirements
- Environment variables
- Test results

## Execution Steps
1. Create Dockerfile and compose configuration.
2. Add health checks and startup commands.
3. Document environment variables.
4. Provide local run and troubleshooting instructions.

## Output Schema
- dockerfile
- compose_file
- run_script
- deployment_notes
- health_checks

## Quality Checks
- No secrets are hardcoded.
- Commands work on localhost first.
- Health checks match real service routes.

## Failure Handling
If deployment is unsafe or unverified, block deployment and request human action.
