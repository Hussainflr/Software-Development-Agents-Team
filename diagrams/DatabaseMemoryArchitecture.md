# Database, Memory, Artifact, and Trace Architecture

This diagram shows how Mission Control, LangGraph, SQLite, memory, artifacts, evaluation, and Agentic OS traces work together during a run.

```text
+================================================================================+
|                              HUMAN MANAGER                                      |
|       enters requirement, reviews outputs, stops/restarts, approves deploy      |
+======================================+=========================================+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                         STREAMLIT MISSION CONTROL                              |
|                                                                                |
| Reads from FastAPI:                                                            |
| - run status and current stage                                                  |
| - agent statuses                                                                |
| - activity logs and trace-style events                                          |
| - generated files                                                               |
| - context snapshots                                                             |
| - short-term memory                                                             |
| - long-term memory                                                              |
| - evaluation scores                                                             |
| - provider/model readiness                                                      |
| - Agentic OS capabilities                                                       |
+--------------------------------------+-----------------------------------------+
                                       |
                                       | REST / polling
                                       v
+--------------------------------------------------------------------------------+
|                              FASTAPI BACKEND                                   |
|                                                                                |
| Responsibilities:                                                              |
| - validate requirement                                                          |
| - create run                                                                    |
| - expose run detail                                                             |
| - expose /api/os/capabilities                                                   |
| - stop/restart run                                                              |
| - approve deployment                                                            |
| - read dashboard data from Repository                                           |
+--------------------------------------+-----------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
|                            REPOSITORY LAYER                                    |
|                                                                                |
| One persistence facade used by API, workflow, memory, evaluation, and traces.   |
| Keeps ORM details out of agents and orchestration code.                         |
+----------------------+-------------------+--------------------+----------------+
                       |                   |                    |
                       v                   v                    v
+-----------------------------+  +----------------------+  +----------------------+
|        SQLITE DATABASE      |  |     FILE SYSTEM      |  |   LLM PROVIDER       |
|        agent_team.db        |  | generated_projects/  |  | Ollama/OpenAI/etc.   |
+-----------------------------+  +----------------------+  +----------------------+
| runs                        |  | run_<id>/            |  | Receives focused     |
| agent_statuses              |  | - generated_backend  |  | context, skills,     |
| agent_logs                  |  | - generated_frontend |  | tool list, memory,   |
| agent_messages              |  | - generated_tests    |  | and output schema.   |
| generated_files             |  | - deployment         |  +----------------------+
| context_snapshots           |  | - reports planned    |
| short_term_memory           |  | - screenshots planned|
| long_term_memory            |  +----------------------+
| evaluation_results          |
+-------------+---------------+
              |
              v
+--------------------------------------------------------------------------------+
|                         AGENTIC OS MEMORY MODEL                                |
+--------------------------------------------------------------------------------+
| Short-term memory   | run-scoped context, outputs, latest evaluation            |
| Long-term memory    | sanitized reusable summaries across successful runs       |
| Session memory      | planned: active conversation/session-level goals          |
| Artifact memory     | generated files stored in SQLite and filesystem           |
| Vector memory       | planned: ChromaDB/Qdrant semantic retrieval layer         |
+--------------------------------------------------------------------------------+
```

## Runtime Data Flow

```text
1. Requirement Validation
   Dashboard / API
        |
        +--> guardrails/requirements.py
              + small talk detection
              + off-topic detection
              + prompt injection detection
              + unsafe intent detection
              + possible PII detection


2. Run Created
   FastAPI /api/runs
        |
        v
   Repository.create_run()
        |
        +--> runs
        +--> agent_statuses for Backend, Frontend, Tester, Deployment


3. Control Loop Starts
   LangGraph node
        |
        +--> ControlLoopState
        |       phase: sense / plan / act / evaluate / refine / finalize
        |
        +--> TraceRecorder.record(...)
                |
                +--> agent_logs with structured trace payload


4. Context Is Built
   Workflow
        |
        +--> LongTermMemory.retrieve(requirement)
        |        |
        |        +--> long_term_memory search
        |
        +--> ContextBuilder.build(...)
                 |
                 + uses requirement
                 + uses relevant generated artifacts
                 + uses tester feedback
                 + uses retrieved long-term memory
                 |
                 v
          Repository.add_context_snapshot(...)
                 |
                 +--> context_snapshots


5. Agent Produces Output
   Agent + LLM
        |
        v
   AgentOutput(summary, artifacts, notes, bugs)
        |
        +--> Artifact sanitizer
        |        + strip markdown fences
        |        + normalize accidental indentation
        |        + compile-check Python files
        |
        +--> Repository.add_message(...)
        |        +--> agent_messages
        |
        +--> Repository.add_log(...)
        |        +--> agent_logs
        |
        +--> Repository.upsert_generated_files(...)
        |        +--> generated_files
        |
        +--> write_artifacts(...)
                 +--> generated_projects/run_<id>/


6. Evaluation and Repair
   Tester Agent
        |
        +--> generated tests and bug report
        |
        v
   EvaluationScorer
        |
        +--> deterministic checks
        +--> optional LLM judge
        +--> requirement alignment
        +--> security/quality signals
        |
        +--> Repository.add_evaluation(...)
        +--> ShortTermMemory.remember("latest_evaluation", ...)

   If failed and refinement budget remains:
        |
        v
   LangGraph routes to Backend/Frontend revision loop

   If failed after budget:
        |
        v
   Run status = failed, deployment approval blocked


7. Long-Term Memory
   Successful or useful run summary
        |
        v
   LongTermMemory.remember(category, summary, source_run_id)
        |
        +--> sanitizes secrets
        +--> truncates summary
        +--> long_term_memory


8. Dashboard Reads Everything
   Streamlit Dashboard
        |
        v
   FastAPI /api/runs/{run_id}
        |
        +--> runs
        +--> agent_statuses
        +--> agent_logs
        +--> generated_files
        +--> agent_messages
        +--> context_snapshots
        +--> short_term_memory
        +--> long_term_memory
        +--> evaluation_results
```

## Table Map

```text
+---------------------+----------------------+--------------------------------------+
| Data Area           | SQLite Table         | Purpose                              |
+---------------------+----------------------+--------------------------------------+
| Run state           | runs                 | Requirement, provider, model, stage  |
| Agent status        | agent_statuses       | idle/thinking/working/completed/etc. |
| Activity/traces     | agent_logs           | Timeline plus structured trace events|
| Agent messages      | agent_messages       | Agent summaries and responses        |
| Generated files     | generated_files      | File path + content for dashboard    |
| Context snapshots   | context_snapshots    | Exact focused context sent to agent  |
| Short-term memory   | short_term_memory    | Run-scoped summaries and checkpoints |
| Long-term memory    | long_term_memory     | Reusable summaries across runs       |
| Evaluation          | evaluation_results   | Correctness/completeness/code score  |
+---------------------+----------------------+--------------------------------------+
```

## Planned Storage Expansion

```text
SQLite today
  |
  +--> PostgreSQL profile
  |     - production persistence
  |     - concurrent users
  |     - stronger migrations
  |
  +--> ChromaDB/Qdrant profile
        - vector memory
        - semantic retrieval
        - artifact/document embeddings
```
