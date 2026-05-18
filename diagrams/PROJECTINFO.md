# Project Info

This document is a file-by-file map of the Agentic Software Development Team project as it evolves into an Agentic OS. It explains what each file does, where it is used, and how it fits into the local Mission Control application.

## High-Level Runtime Flow

```text
Human Manager
     |
     v
Streamlit Dashboard
dashboard/app.py
     |
     | REST polling and commands
     v
FastAPI Backend
app/main.py -> backend/app/main.py
     |
     v
Requirement Guardrails
guardrails/requirements.py
     |
     v
Agentic OS Runtime
app/core/agentic_os.py
app/core/control_loop.py
     |
     v
Repository + SQLite
database/repository.py
database/models.py
agent_team.db
     |
     v
LangGraph Workflow
workflows/software_team_graph.py
     |
     +--> Backend Agent
     |    agents/backend_agent.py
     |
     +--> Frontend Agent
     |    agents/frontend_agent.py
     |
     +--> Tester Agent
     |    agents/tester_agent.py
     |
     +--> Human Approval Gate
     |
     +--> Deployment Agent
          agents/deployment_agent.py

Agents call:
     |
     +--> Agent Catalog
     |    agents/catalog.py
     |
     +--> Context Builder
     |    context/context_builder.py
     |
     +--> Memory
     |    memory/short_term_memory.py
     |    memory/long_term_memory.py
     |
     +--> LLM Provider
     |    llm_providers/factory.py
     |    llm_providers/langchain_client.py
     |    llm_providers/catalog.py
     |
     +--> Tool Registry / MCP Descriptor
     |    tools/registry.py
     |    tools/mcp.py
     |
     +--> File Writer
          tools/file_writer.py
```

## Core Request Flow

```text
1. User enters requirement in Streamlit.
2. Dashboard calls POST /api/runs.
3. FastAPI creates a run in SQLite.
4. FastAPI starts SoftwareTeamWorkflow in a background thread.
5. Agentic OS control-loop state tracks sense/plan/act/evaluate/refine/finalize phases.
6. LangGraph runs Backend -> Frontend -> Tester.
7. Tester output and evaluator decide whether a revision loop is needed.
8. Workflow waits for human deployment approval.
9. Dashboard calls approve-deployment.
10. Deployment Agent creates Docker/local deployment artifacts.
11. Dashboard reads logs, traces, statuses, memory, context, evaluation, and generated files.
```

## Directory Map

```text
.
├── agents/              Agent classes and agent IO schemas
├── app/                 Uvicorn entrypoint and Agentic OS core contracts
├── backend/app/         FastAPI API server
├── config/              Active shared constants
├── context/             Focused context builder for agents
├── dashboard/           Streamlit Mission Control UI
├── database/            SQLAlchemy models, sessions, repository facade
├── diagrams/            ASCII architecture diagrams
├── docs/                Human-facing guides
├── evaluation/          Artifact scoring/evaluation logic
├── guardrails/          Manager input validation before workflow execution
├── generated_projects/  Runtime output folder for generated project files
├── llm_providers/       LangChain provider abstraction
├── memory/              Short-term and long-term memory wrappers
├── observability/       Trace recording helpers
├── prompts/             Prompt templates loaded by agents
├── samples/             Demo prompt content
├── scripts/             Local helper scripts
├── skills/              Skill registry and fallback artifacts
├── tests/               Unit tests
├── tools/               Shared infrastructure utilities and tool registry
└── workflows/           LangGraph workflow orchestration
```

## Application Entrypoints

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `app/main.py` | Compatibility entrypoint for `uvicorn app.main:app --reload`. Imports the real FastAPI app. | Uvicorn command, Dockerfile, local setup docs. |
| `app/__init__.py` | Marks `app` as a Python package. | Python import system. |
| `app/core/__init__.py` | Exports Agentic OS core contracts. | Imported by API/tests/future runtime code. |
| `app/core/control_loop.py` | Defines reusable control-loop phases and retry/refinement policy state. | Used by `workflows/software_team_graph.py` and Agentic OS tests. |
| `app/core/agentic_os.py` | Runtime capability facade exposing agents, tools, providers, memory layers, and MCP readiness. | Used by `backend/app/main.py` for `/api/os/capabilities`. |
| `backend/app/main.py` | Main FastAPI application. Defines health check, provider list, OS capabilities, requirement validation, run create/list/detail, logs/status/outputs, stop/restart, and deployment approval endpoints. | Imported by `app/main.py`; called by `dashboard/app.py`. |
| `dashboard/app.py` | Streamlit Mission Control dashboard. Lets the human manager start runs, choose provider/model, view status cards, inspect logs/files/messages/memory/evaluation, stop/restart, and approve deployment. | Started with `streamlit run dashboard/app.py`; calls FastAPI endpoints. |
| `scripts/run_local.sh` | Convenience script that starts FastAPI and Streamlit locally. | Developer local workflow. |

## Backend API Files

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `backend/app/config.py` | Loads runtime settings from environment variables and `.env`, including DB path, generated output path, default provider/model, and API keys. | Imported by FastAPI, database session, LLM provider, workflow. |
| `backend/app/schemas.py` | Pydantic API response/request schemas for requirement validation, runs, logs, statuses, files, memory, context, evaluation, providers, and actions. | Used by `backend/app/main.py` as FastAPI response models. |
| `backend/app/__init__.py` | Marks `backend.app` as a package. | Python import system. |
| `backend/__init__.py` | Marks `backend` as a package. | Python import system. |

## Workflow Files

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `workflows/software_team_graph.py` | Central LangGraph orchestration. Defines `SoftwareTeamState`, initial workflow, deployment workflow, revision routing, agent execution, persistence, memory updates, context snapshots, and evaluation routing. | Instantiated by `backend/app/main.py`; calls agents, repository, context, memory, evaluator, LLM provider, and file writer. |
| `workflows/__init__.py` | Marks `workflows` as a package. | Python import system. |

## Agent Files

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `agents/base.py` | Shared agent base class. Builds prompt payloads, wires LangChain prompt/model/parser chain, parses structured output, and falls back if output is invalid. | Subclassed by all agents; called by workflow. |
| `agents/catalog.py` | Declarative Agentic OS catalog for Planner, Research, Coder, Backend, Frontend, Debugger, Tester, Reviewer, Security, Deployment, Evaluator, and Memory agents. | Used by `app/core/agentic_os.py` to expose OS capabilities. |
| `agents/schemas.py` | Pydantic `AgentInput` and `AgentOutput` models. Defines the contract agents receive and return. | Used by `agents/base.py`, concrete agents, tests, and workflow. |
| `agents/backend_agent.py` | Backend Agent. Sets role/task prompt/skills and returns backend fallback artifacts when needed. | Instantiated by `SoftwareTeamWorkflow`. |
| `agents/frontend_agent.py` | Frontend Agent. Sets role/task prompt/skills and returns frontend fallback artifacts when needed. | Instantiated by `SoftwareTeamWorkflow`. |
| `agents/tester_agent.py` | Tester Agent. Sets testing/review skills and returns test fallback artifacts when needed. | Instantiated by `SoftwareTeamWorkflow`; its bugs feed the revision loop. |
| `agents/deployment_agent.py` | Deployment Agent. Sets deployment skill and returns Docker/local deployment fallback artifacts when needed. | Instantiated by deployment graph after human approval. |
| `agents/__init__.py` | Marks `agents` as a package. | Python import system. |

## Prompt Files

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `prompts/system.md` | System prompt shared by agents. Defines broad behavior and constraints. | Loaded by `prompts/loader.py` in `BaseAgent.prompt_template()`. |
| `prompts/agent_task.md` | Main human-message prompt template. Receives agent name, role, task, skills, focused context, and format instructions. | Loaded by `BaseAgent.prompt_template()`. |
| `prompts/backend_task.md` | Backend-specific task instructions. | Referenced by `BackendAgent.task_prompt`. |
| `prompts/frontend_task.md` | Frontend-specific task instructions. | Referenced by `FrontendAgent.task_prompt`. |
| `prompts/tester_task.md` | Tester-specific task instructions. | Referenced by `TesterAgent.task_prompt`. |
| `prompts/deployment_task.md` | Deployment-specific task instructions. | Referenced by `DeploymentAgent.task_prompt`. |
| `prompts/assembler.py` | Dynamic prompt assembly from agent role, user goal, task, skills, memory, granted tools, guardrails, and runtime context. | Tested by `tests/test_agentic_os_core.py`; intended for future agent runtime expansion. |
| `prompts/loader.py` | Reads prompt templates from the `prompts/` directory. | Used by `agents/base.py`. |
| `prompts/__init__.py` | Marks `prompts` as a package. | Python import system. |

## LLM Provider Files

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `llm_providers/factory.py` | Normalizes provider/model names, exposes provider options, and builds `LangChainChatProvider`. | Used by FastAPI provider endpoint and `SoftwareTeamWorkflow`. |
| `llm_providers/langchain_client.py` | Creates provider-specific LangChain chat models for Ollama, OpenAI, and Anthropic. Validates provider readiness, discovers local Ollama models, and checks API key requirements. | Used by `llm_providers/factory.py`. |
| `llm_providers/catalog.py` | Provider capability metadata for Ollama, LM Studio, OpenAI, Anthropic, Gemini, Groq, OpenRouter, and Together AI. | Used by `app/core/agentic_os.py`. |
| `llm_providers/base.py` | Defines shared LLM/provider exception classes. | Imported by provider client. |
| `llm_providers/__init__.py` | Marks `llm_providers` as a package. | Python import system. |

## Database Files

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `database/models.py` | SQLAlchemy ORM models for runs, statuses, logs, messages, generated files, context snapshots, short-term memory, long-term memory, and evaluations. | Used by `database/session.py` and `database/repository.py`. |
| `database/session.py` | Creates SQLAlchemy engine/session factory and initializes tables. | Used by FastAPI startup and repository. |
| `database/repository.py` | Persistence facade for the rest of the app. Creates/updates runs, logs, statuses, files, context snapshots, memory items, and evaluation results. | Used by FastAPI, workflow, memory classes. |
| `database/__init__.py` | Marks `database` as a package. | Python import system. |

## Guardrails, Context, Memory, Evaluation

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `guardrails/requirements.py` | Deterministic manager-input guardrail. Blocks greetings, very short fragments, non-software requests, unsafe intent, prompt injection language, and possible PII before a run starts. | Used by `dashboard/app.py`, `backend/app/main.py`, and Agentic OS capability/classification code. |
| `guardrails/__init__.py` | Exports public guardrail helpers. | Python imports. |
| `context/context_builder.py` | Builds focused context for each agent by selecting relevant artifacts, feedback, constraints, and retrieved long-term memory. | Used by `SoftwareTeamWorkflow._run_agent()`. |
| `context/__init__.py` | Marks `context` as a package. | Python import system. |
| `memory/short_term_memory.py` | Stores run-scoped summaries such as context, outputs, and latest evaluation. | Used by `SoftwareTeamWorkflow`. Persists through repository into SQLite. |
| `memory/long_term_memory.py` | Stores sanitized reusable summaries across runs and retrieves relevant memories by simple text matching. | Used by `SoftwareTeamWorkflow` and `ContextBuilder` flow. |
| `memory/__init__.py` | Marks `memory` as a package. | Python import system. |
| `evaluation/schemas.py` | Shared evaluation models for score results, LLM judge findings, and deterministic checklist details. | Imported by all evaluation modules and persisted through `repository.add_evaluation()`. |
| `evaluation/deterministic.py` | Checklist evaluator for required artifacts, obvious quality signals, placeholders, secrets, and basic runnable app expectations. | Called by `evaluation/scorer.py` during the Tester stage. |
| `evaluation/llm_judge.py` | Optional LLM-as-judge evaluator. Builds a compact artifact preview, asks the selected chat model for JSON scoring, and parses the response. | Called by `evaluation/scorer.py` when a chat model is available. |
| `evaluation/scorer.py` | Hybrid evaluation orchestrator. Combines deterministic scoring and optional LLM-as-judge review into one conservative pass/fail result. | Used by Tester stage in `SoftwareTeamWorkflow`. |
| `evaluation/__init__.py` | Exports the public evaluation classes and models. | Python imports and future extension code. |

## Skills and Fallbacks

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `skills/registry.py` | Defines reusable skill file names and renders selected Markdown skill files into the agent prompt. | Used by `agents/base.py`. |
| `skills/planning.md` | Planning skill for task decomposition and approval checkpoints. | Loaded by the skill registry for future Planner Agent prompts. |
| `skills/code_generation.md` | Prompt-facing code generation skill instructions. | Loaded by `skills/registry.py` for Backend and Frontend agents. |
| `skills/debugging.md` | Debugging skill for failure diagnosis and repair planning. | Loaded by the skill registry for future Debugger Agent prompts. |
| `skills/testing.md` | Testing skill for generated software validation. | Loaded by the skill registry for Tester Agent prompts/future runtime. |
| `skills/evaluation.md` | Evaluation skill for scoring, alignment, and repair decisions. | Loaded by the skill registry for future Evaluator Agent prompts. |
| `skills/deployment.md` | Deployment skill for local/container deployment artifacts. | Loaded by the skill registry for Deployment Agent prompts/future runtime. |
| `skills/rag.md` | Retrieval/memory skill for grounding context in prior runs and documents. | Loaded by the skill registry for future Research/Memory agents. |
| `skills/research.md` | Research skill for local/official documentation discovery. | Loaded by the skill registry for future Research Agent prompts. |
| `skills/security_review.md` | Security review skill for secrets, unsafe actions, and permission risks. | Loaded by the skill registry for future Security Agent prompts. |
| `skills/test_generation.md` | Prompt-facing test generation skill instructions. | Loaded by `skills/registry.py` for Tester Agent. |
| `skills/code_review.md` | Prompt-facing code review skill instructions. | Loaded by `skills/registry.py` for Tester Agent. |
| `skills/dockerfile_generation.md` | Prompt-facing deployment artifact skill instructions. | Loaded by `skills/registry.py` for Deployment Agent. |
| `skills/fallback_artifacts.py` | Executable fallback artifact factories for backend, frontend, tester, and deployment outputs. Includes requirement-aware fallback for Rock Paper Scissors instead of always generating task tracker artifacts. | Imported by concrete agent classes when LLM output is missing/invalid. |
| `skills/__init__.py` | Marks `skills` as a package. | Python import system. |
| `skills.md` | Human-readable skills reference. | Documentation only; referenced from README. |

## Tools

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `tools/artifact_sanitizer.py` | Normalizes generated artifacts before persistence. Python files are stripped of accidental Markdown/code-block indentation and compile-checked before being stored or written. | Used by `agents/base.py` and `tools/file_writer.py`; tested by `tests/test_artifact_sanitizer.py`. |
| `tools/file_writer.py` | Safely writes generated artifacts under the run directory and blocks path traversal. Makes `.sh` files executable. | Used by `SoftwareTeamWorkflow._run_agent()`; tested by `tests/test_file_writer.py`. |
| `tools/registry.py` | Permissioned Agentic OS tool catalog with risk level, approval requirement, timeout, and MCP compatibility metadata. | Used by `app/core/agentic_os.py` and tests. |
| `tools/mcp.py` | Converts local tool definitions into MCP-compatible descriptors/manifests. | Used by `app/core/agentic_os.py`. |
| `tools/__init__.py` | Marks `tools` as a package. | Python import system. |

## Observability

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `observability/tracing.py` | Defines structured `TraceEvent` and `TraceRecorder`, persisting control-loop/agent events through the existing log table. | Used by `workflows/software_team_graph.py`. |
| `observability/__init__.py` | Exports tracing helpers. | Python import system. |

## Configuration and Defaults

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `config/defaults.py` | Active shared constants for default provider/model and provider defaults. | Used by `backend/app/config.py`, schemas, database models, provider factory. |
| `config/__init__.py` | Marks `config` as a package. | Python import system. |
| `.env.example` | Example environment variables for local configuration. | Copied to `.env` during setup. |
| `.gitignore` | Git ignore rules for env files, caches, DB, generated projects, and local artifacts. | Git. |
| `requirements.txt` | Python dependencies for API, dashboard, LangGraph/LangChain, database, and tests. | `pip install -r requirements.txt`. |
| `pytest.ini` | Pytest configuration. | Test runner. |

## Docker and Local Deployment

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `Dockerfile` | Container image for the API/dashboard project code. | Used by Docker Compose. |
| `docker-compose.yml` | Containerized API/dashboard/Ollama-style local setup depending on current compose contents. | Developer local deployment. |
| `scripts/run_local.sh` | Starts API and dashboard together locally. | Developer convenience script. |

## Dashboard and Diagrams

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `diagrams/SystemFlow.md` | ASCII system flow diagram. | Documentation. |
| `diagrams/LLMProviderFlow.md` | ASCII provider switching / LLM flow diagram. | Documentation. |
| `diagrams/DatabaseMemoryArchitecture.md` | ASCII architecture diagram for database, context, memory, evaluation, and generated files. | Documentation. |
| `docs/AGENTIC_OS_ARCHITECTURE.md` | Agentic OS migration plan, target architecture, module map, and roadmap. | Human developers. |
| `docs/PROJECT_GUIDE.md` | Detailed user/developer guide moved out of the README to keep the README short. | Human developers. |

## Tests

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `tests/test_agent_parser.py` | Tests tolerant parsing of LLM JSON output. | `pytest`. |
| `tests/test_agentic_os_core.py` | Tests control-loop policy, guardrail classification, dynamic prompt assembly, tool permissions, provider catalog, and OS capabilities. | `pytest`. |
| `tests/test_artifact_sanitizer.py` | Tests Python artifact normalization, Markdown fence stripping, compile checks, and validation failures. | `pytest`. |
| `tests/test_context_builder.py` | Tests focused context selection by agent/task. | `pytest`. |
| `tests/test_evaluation_scorer.py` | Tests evaluation scoring behavior. | `pytest`. |
| `tests/test_fallback_artifacts.py` | Tests requirement-aware fallback artifacts, including Rock Paper Scissors backend/frontend/test outputs. | `pytest`. |
| `tests/test_file_writer.py` | Tests artifact writing and path traversal protection. | `pytest`. |
| `tests/test_langchain_agent.py` | Tests agent invocation with a fake LangChain chat model. | `pytest`. |
| `tests/test_provider_factory.py` | Tests provider normalization and model naming. | `pytest`. |
| `tests/test_workflow_routing.py` | Tests workflow routing decisions such as blocking deployment approval after final failed evaluation. | `pytest`. |

## Samples and Generated Output

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `samples/demo_prompt.md` | Task tracker example manager requirement for manual demo runs. | User copies into dashboard. |
| `samples/rock_paper_scissors_prompt.md` | Rock Paper Scissors example manager requirement. | User copies into dashboard. |
| `samples/rock_paper_scissors_backend_test.py` | Example pytest file for a generated Rock Paper Scissors backend. | Reference for Tester Agent expectations. |
| `generated_projects/.gitkeep` | Keeps the generated output directory in git. | Git placeholder. |
| `generated_projects/run_<id>/...` | Runtime generated project artifacts. | Created by workflow; ignored by git. |
| `agent_team.db` | Local SQLite runtime database. | Created by app; should usually be ignored, not committed. |

## Main Documentation

| File | Purpose | Used By / Where |
| --- | --- | --- |
| `README.md` | Short start-here guide for setup, running, demo prompt, and links to deeper docs. | Human developers. |
| `CODE_PATTERNS.md` | Code pattern/reference notes, including examples from production-oriented refactors. | Documentation/reference. |
| `LANGCHAIN_GUIDE.md` | LangChain usage guide and patterns. | Documentation/reference. |
| `MIGRATION_GUIDE.md` | Migration notes from earlier/non-LangChain style to the current or intended production style. | Documentation/reference. |
| `PRODUCTION_CHECKLIST.md` | Production readiness checklist. | Documentation/reference. |
| `REFACTORING_SUMMARY.md` | Summary of refactor changes and intended architecture improvements. | Documentation/reference. |
| `FILES_CREATED.md` | Inventory of files from an earlier generation/refactor pass. | Documentation/reference; may mention legacy files. |

## Legacy / Optional Prototype Files

These files are present but are not part of the current FastAPI -> LangGraph runtime path. Keep them only if you want the older production-refactor prototype/reference material.

| File | Purpose | Current Use |
| --- | --- | --- |
| `config.py` | Older production-style config module with nested app/LLM/database/logging settings. | Shadowed by the `config/` package in normal imports; not used by current runtime. |
| `logging_config.py` | Older structlog setup. | Referenced by legacy prototype files; not used by current runtime. |
| `llm_provider_langchain.py` | Older LiteLLM-to-LangChain adapter. | Not used by current runtime, which uses `llm_providers/langchain_client.py`. |
| `error_handling.py` | Older retry/error recovery utilities. | Referenced by legacy prototype files; not used by current runtime. |
| `state_management.py` | Older TypedDict/dataclass workflow state definitions. | Referenced by legacy prototype files; not used by current runtime. |
| `workflow_orchestrator.py` | Older LCEL/production orchestrator concept. | Not used by FastAPI. It also references missing `agents.langchain_agents` and older repository method names. |
| `example_usage.py` | Example script for older production-style modules. | Not used by current runtime; depends on older config imports. |

## Data Persistence Diagram

```text
FastAPI endpoints
     |
     v
Repository
     |
     +--> runs
     +--> agent_statuses
     +--> agent_logs
     +--> agent_messages
     +--> generated_files
     +--> context_snapshots
     +--> short_term_memory
     +--> long_term_memory
     +--> evaluation_results
```

## Agent Context Diagram

```text
Workflow stage
     |
     +--> Load current run
     +--> Load generated artifacts
     +--> Retrieve long-term memory
     +--> Add tester feedback if any
     |
     v
ContextBuilder
     |
     v
Focused context snapshot
     |
     +--> saved to context_snapshots
     +--> summarized into short_term_memory
     +--> sent to agent prompt
```

## Generated File Flow

```text
AgentOutput.artifacts
     |
     +--> database.generated_files
     |
     +--> generated_projects/run_<id>/
             |
             +--> generated_backend/
             +--> generated_frontend/
             +--> generated_tests/
             +--> deployment/
```

## Notes For Cleanup

Runtime cleanup candidates:

```text
__pycache__/
*.pyc
.DS_Store
agent_team.db
generated_projects/run_*/
```

Potential architecture cleanup candidates:

```text
config.py
logging_config.py
llm_provider_langchain.py
error_handling.py
state_management.py
workflow_orchestrator.py
example_usage.py
```

Before deleting architecture cleanup candidates, decide whether you want to keep the older production-refactor reference docs that mention them.
