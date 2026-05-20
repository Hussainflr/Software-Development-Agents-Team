# Agentic OS System Flow

```text
+-------------------+
|   Human Manager   |
+---------+---------+
          |
          v
+---------------------------+
| Mission Control Dashboard |
| Streamlit                 |
| - task input              |
| - provider/model select   |
| - run history             |
| - status/logs/files       |
| - memory/evaluation       |
| - approval controls       |
+-------------+-------------+
              |
              | REST / polling
              v
+---------------------------+
| FastAPI Backend           |
| backend.app.main          |
| - /api/providers          |
| - /api/os/capabilities    |
| - /api/requirements/...   |
| - /api/runs/...           |
+-------------+-------------+
              |
              v
+---------------------------+
| Requirement Guardrails    |
| guardrails/requirements.py|
| - small talk blocking     |
| - off-topic detection     |
| - prompt injection checks |
| - unsafe intent checks    |
| - possible PII checks     |
+-------------+-------------+
              |
              v
+---------------------------+
| Agentic OS Runtime        |
| app/core                  |
| - capability registry     |
| - control-loop policy     |
| - OS metadata for UI/API  |
+-------------+-------------+
              |
              v
+----------------------------------------------------+
| LangGraph Workflow                                 |
| workflows/software_team_graph.py                   |
|                                                    |
| Control loop phases:                               |
| sense -> plan -> act -> evaluate -> refine/retry   |
|       -> finalize / approval / stop / failed       |
+------------------------+---------------------------+
                         |
                         v
+----------------------------------------------------+
| Structured Workflow State                          |
| - run_id, requirement, provider, model             |
| - artifacts, messages, bug report                  |
| - evaluation result, revision count                |
| - control_loop phase/current_agent/retries         |
+------------------------+---------------------------+
                         |
          +--------------+---------------+
          |                              |
          v                              v
+----------------------+       +----------------------+
| Agent Catalog        |       | Tool Registry        |
| agents/catalog.py    |       | tools/registry.py    |
| - Planner            |       | - filesystem         |
| - Research           |       | - terminal/python    |
| - Coder              |       | - git/docker         |
| - Backend/Frontend   |       | - web/API/database   |
| - Debugger/Tester    |       | - vector/doc/table   |
| - Reviewer/Security  |       | - approval metadata  |
| - Deployment         |       | - MCP-compatible     |
| - Evaluator/Memory   |       +----------+-----------+
+----------+-----------+                  |
           |                              v
           |                   +----------------------+
           |                   | MCP Adapter Contract |
           |                   | tools/mcp.py         |
           |                   | local tools -> MCP   |
           |                   | manifest/descriptors |
           |                   +----------------------+
           |
           v
+----------------------------------------------------+
| Active Software Team Graph                         |
|                                                    |
| Planner Agent                                      |
|      |                                             |
|      v                                             |
| Backend -> Frontend -> Reviewer -> Security        |
|      ^                              |              |
|      |                              v              |
|      +------ revision loop < Tester -> Evaluator   |
|                                     |              |
|                                     v              |
|                         Human Approval Gate        |
|                                     |              |
|                                     v              |
|                             Deployment Agent       |
+------------------------+---------------------------+
                         |
                         v
+----------------------+       +----------------------+
| Memory + Database    |       | Generated Artifacts  |
| SQLite Repository    |       | generated_projects/  |
| - runs/status/logs   |       | run_<id>/            |
| - messages/context   |       | - backend            |
| - short-term memory  |       | - frontend           |
| - long-term memory   |       | - tests              |
| - evaluations        |       | - deployment         |
+----------+-----------+       +----------+-----------+
           |                              |
           v                              v
+----------------------------------------------------+
| Observability                                      |
| observability/tracing.py                           |
| - control-loop phase traces                        |
| - agent traces                                     |
| - evaluation events                                |
| - error/failure analytics via logs                 |
+----------------------------------------------------+
```

## Current Runtime Path

```text
Human Manager
  -> Dashboard
  -> FastAPI
  -> Requirement Guardrails
  -> LangGraph
  -> Planner Agent
  -> Backend Agent
  -> Frontend Agent
  -> Reviewer Agent
  -> Security Agent
  -> Tester Agent
  -> Generated Test Execution
  -> Evaluator Agent
  -> Revision Loop if needed
  -> Human Approval
  -> Deployment Agent
  -> Generated Project
```

## Agentic OS Expansion Path

```text
Planner
  -> Research
  -> Backend + Frontend
  -> Reviewer + Security
  -> Tester
  -> Evaluator
  -> Debugger/Repair Loop
  -> Human Approval
  -> Deployment
  -> Memory Agent
```
