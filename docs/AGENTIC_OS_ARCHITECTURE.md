# Agentic OS Architecture

This project is evolving from a software-development agent team into a local-first Agentic OS. The existing Mission Control flow remains backward compatible while the platform gains reusable contracts for orchestration, tools, memory, guardrails, evaluation, observability, and MCP integration.

## Current Architecture

```text
Streamlit Mission Control
        |
FastAPI Backend
        |
LangGraph SoftwareTeamWorkflow
        |
Backend -> Frontend -> Tester -> Human Approval -> Deployment
        |
SQLite Repository + generated_projects/run_<id>/
```

## Architectural Gaps Found

- The control loop existed implicitly inside one workflow, not as a reusable runtime contract.
- The system had four concrete agents, but no catalog for planner, research, coder, debugger, reviewer, security, evaluator, or memory roles.
- Tool access was not centrally described with permissions, approval requirements, timeout metadata, or MCP compatibility.
- Prompt assembly was static instead of dynamically composing role, task, memory, skills, tools, and guardrails.
- Observability was stored as logs, but workflow phases and trace events were not first-class.
- Provider switching was practical for Ollama/OpenAI/Anthropic, but broader provider capability metadata was missing.
- MCP should be an adapter over the local tool registry, not a replacement for the model provider layer.

## Target Architecture

```text
Mission Control Dashboard
        |
FastAPI API
        |
Requirement Guardrails
        |
Agentic OS Runtime
        |
LangGraph Workflow Engine
        |
+-------------------+--------------------+
| Agent Catalog     | Tool Registry      |
| planner/research  | permissions        |
| backend/frontend  | approval metadata  |
| tester/security   | MCP descriptors    |
+-------------------+--------------------+
        |
Memory + Evaluation + Artifact Management
        |
Observability + Trace Events
```

## Migration Strategy

1. Preserve the working four-agent pipeline.
2. Add Agentic OS contracts without forcing a large folder rename.
3. Expose platform capabilities through API so the dashboard can inspect agents, tools, models, and MCP readiness.
4. Wire control-loop phases into the existing LangGraph workflow.
5. Keep Planner, Reviewer, Security, and Evaluator nodes inside the compatibility graph while expanding their capabilities.
6. Add real MCP server/client adapters after local permissions are stable.

## First Increment Implemented

- `app/core/control_loop.py`: reusable control-loop state and policy.
- `app/core/agentic_os.py`: capability facade for APIs and UI.
- `agents/catalog.py`: full Agentic OS agent catalog.
- `tools/registry.py`: permissioned tool registry.
- `tools/mcp.py`: MCP-compatible local tool manifest.
- `llm_providers/catalog.py`: provider capability catalog for Ollama, LM Studio, OpenAI, Claude, Gemini, Groq, OpenRouter, and Together AI.
- `prompts/assembler.py`: dynamic prompt assembly.
- `observability/tracing.py`: structured trace recorder.
- `guardrails/requirements.py`: stronger intent, prompt-injection, unsafe request, and PII checks.
- `skills/*.md`: expanded modular skills registry.
- `GET /api/os/capabilities`: runtime capability endpoint.
- `agents/planner_agent.py`: execution planning node before implementation.
- `agents/reviewer_agent.py`: architecture/code consistency review node.
- `agents/security_agent.py`: security and permission review node.
- `agents/evaluator_agent.py`: explicit quality-gate node after testing.
- `evaluation/test_execution.py`: generated pytest execution with captured output.
- `evaluation/consistency.py`: backend/frontend/test endpoint consistency checks.
- `llm_providers/router.py`: LiteLLM-style routing and token/cost/latency metric facade.
- `tools/permissions.py`: approval policy gate for registered tools.

## Diagram Index

- `diagrams/SystemFlow.md`: full Agentic OS runtime flow.
- `diagrams/DatabaseMemoryArchitecture.md`: database, memory, artifacts, and trace storage.
- `diagrams/LLMProviderFlow.md`: provider discovery, model routing, and future router path.
- `diagrams/PROJECTINFO.md`: file-by-file map of the current project.

## Roadmap

### Completed In Current Increment

- Planner Agent runs before Backend Agent.
- Reviewer and Security Agents run before Tester Agent.
- Evaluator Agent runs as an explicit quality gate after Tester Agent.
- Generated project tests execute in an isolated temporary run directory.
- Endpoint consistency checks compare backend routes against frontend/test references.
- Dashboard shows expanded agent cards and Agentic OS capability panels.
- Model router facade exposes fallback, token estimate, cost estimate, and latency metric contracts.
- Tool permission policy blocks approval-required tools until human approval is provided.

### Later

- Add model-router fallback execution, streaming, and persisted token/cost metrics.
- Add artifact manifests and immutable artifact versions per run.
- Add PostgreSQL and Qdrant/ChromaDB deployment profiles.
- Add RBAC, API key vaulting, rate limiting, concurrency limits, and sandboxed tool execution.
- Add MCP adapters for GitHub, browser testing, filesystem, database, and deployment providers.
