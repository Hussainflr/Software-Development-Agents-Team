# Planning Skill

## Purpose
Turn a user goal into an executable plan with agents, dependencies, risks, and acceptance criteria.

## Usage Conditions
Use when a task needs decomposition, workflow routing, or human approval checkpoints.

## Input Format
- User goal
- Available agents and tools
- Known constraints
- Retrieved memory

## Execution Steps
1. Classify the task intent.
2. Identify deliverables and acceptance criteria.
3. Split work into ordered and parallelizable steps.
4. Mark approval checkpoints and risky actions.
5. Produce a concise execution plan.

## Output Schema
- summary
- steps
- dependencies
- approvals_required
- risks

## Quality Checks
- Every step has an owner.
- Risky actions require approval.
- The plan can be resumed after interruption.

## Failure Handling
If the goal is vague, ask for clarification instead of starting generation.
