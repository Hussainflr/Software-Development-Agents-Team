# Migration Guide: Software Development Agents Team -> Agentic OS

This guide tracks the migration from a focused four-agent software generator into a production-ready Agentic OS platform.

## Current Stable Runtime

```text
Human Manager
  -> Streamlit Mission Control
  -> FastAPI
  -> Requirement Guardrails
  -> LangGraph Workflow
  -> Backend Agent
  -> Frontend Agent
  -> Tester Agent
  -> Evaluation + Revision Loop
  -> Human Approval
  -> Deployment Agent
  -> generated_projects/run_<id>/
```

This path remains the compatibility baseline. New Agentic OS modules should extend it without breaking local demos.

## Target Runtime

```text
Human Manager
  -> Mission Control
  -> FastAPI API
  -> Guardrails + Intent Classification
  -> Planner Agent
  -> Research Agent
  -> Parallel Build Agents
  -> Reviewer + Security Agents
  -> Tester Agent
  -> Evaluator Agent
  -> Debugger/Repair Loop
  -> Human Approval Gate
  -> Deployment Agent
  -> Memory Agent
  -> Observability + Artifact Store
```

## Migration Principles

- Keep the app local-first with Ollama as the default provider.
- Preserve the existing API and dashboard where reasonable.
- Add contracts before moving behavior.
- Prefer small graph changes over one large rewrite.
- Every new OS layer needs tests.
- MCP is a tool adapter layer, not an LLM provider replacement.

## Completed Foundation

```text
app/core/
  control_loop.py      control-loop phases and retry/refinement policy
  agentic_os.py        capability facade for API/UI

agents/
  catalog.py           full Agentic OS agent catalog

tools/
  registry.py          permissioned tool registry
  mcp.py               MCP-compatible descriptors

llm_providers/
  catalog.py           provider capability metadata

prompts/
  assembler.py         dynamic prompt assembly

observability/
  tracing.py           structured trace events

skills/
  planning.md
  debugging.md
  testing.md
  evaluation.md
  deployment.md
  rag.md
  research.md
  security_review.md

backend/app/main.py
  GET /api/os/capabilities
```

## Next Migration Steps

### Step 1: API and Dashboard Visibility

```text
GET /api/os/capabilities
        |
        v
Dashboard panels:
- control-loop policy
- agent catalog
- tool permissions
- provider capabilities
- MCP readiness
```

### Step 2: Planner Node

Add a Planner Agent node before Backend/Frontend.

```text
Requirement
   |
   v
Planner
   |
   +--> build plan
   +--> acceptance criteria
   +--> risk/approval notes
   |
   v
Backend / Frontend
```

### Step 3: Reviewer and Security Nodes

Add review gates before testing/deployment.

```text
Backend + Frontend
       |
       +--> Reviewer Agent
       |
       +--> Security Agent
       |
       v
Tester Agent
```

### Step 4: Evaluator-Driven Repair Loop

Move evaluation from a helper call into a graph node.

```text
Tester
  |
  v
Evaluator
  |
  +-- pass --> Human Approval
  |
  +-- fail and budget remains --> Debugger/Repair
  |
  +-- fail final --> blocked deployment
```

### Step 5: Tool Execution Policy

Route tool calls through `tools/registry.py`.

```text
Agent requests tool
     |
     v
Tool Registry
     |
     +--> allowed read tool -> execute
     +--> approval-required tool -> pause for human
     +--> blocked tool -> log and fail safely
```

### Step 6: MCP Adapters

Expose approved local tools through MCP-compatible descriptors first, then add real MCP client/server integration.

```text
Tool Registry
    |
    v
MCP Manifest
    |
    +--> Claude MCP
    +--> OpenAI Agents SDK compatible tools
    +--> external tool providers
```

## Future Enterprise Track

- FastAPI lifespan startup instead of deprecated `on_event`.
- Background task queue and concurrency limits.
- Token, cost, and latency metrics.
- PostgreSQL deployment profile.
- ChromaDB/Qdrant vector memory profile.
- RBAC and API key vaulting.
- Sandboxed terminal/Python execution.
- WebSocket streaming for live workflow events.
