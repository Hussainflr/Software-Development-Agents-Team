# Project Guide

This guide holds the details that used to live in the README. Keep the README short and use this file when you want the fuller system map.

## What The App Does

You enter a software requirement, choose an LLM provider/model, and start a run. Mission Control coordinates the agents through a backend -> frontend -> testing -> approval -> deployment workflow.

The system stores every run in SQLite, including logs, generated files, agent messages, context snapshots, memory, and evaluation scores.

The project is now evolving into an Agentic OS: a local-first platform with a reusable control loop, expanded agent catalog, tool registry, MCP-compatible tool descriptors, dynamic prompt assembly, guardrails, observability, memory, and evaluation loops.

## How A Run Works

```text
Human Manager
     |
     v
Mission Control Dashboard
     |
     v
Requirement Guardrail
     |
     v
Agentic OS Control Loop
sense -> plan -> act -> evaluate -> refine/retry -> finalize
     |
     v
Planner Agent
     |
     v
Backend Agent -> Frontend Agent -> Reviewer Agent -> Security Agent
                                                     |
                                                     v
                                               Tester Agent
                                                     |
                                                     v
                                              Evaluator Agent
                                                     |
                           revision loop <----------+
                                                     |
                                                     v
                                           Human Deployment Approval
                                                     |
                                                     v
                                             Deployment Agent
```

Run behavior:

1. The dashboard validates your requirement.
2. Planner Agent creates an execution plan and acceptance criteria.
3. Backend Agent creates backend artifacts.
4. Frontend Agent creates UI artifacts.
5. Reviewer Agent checks architecture and consistency.
6. Security Agent checks secrets, unsafe actions, and permission risks.
7. Tester Agent writes/reviews tests and runs generated pytest files when present.
8. Evaluation scores correctness, completeness, code quality, endpoint consistency, and requirement alignment.
9. If issues are found, the workflow gets up to two revision passes.
10. If evaluation still fails, deployment approval is blocked.
11. If evaluation passes, you can approve deployment.
12. Generated files appear in `generated_projects/run_<id>/`.

## Requirement Guardrails

Short chat inputs like `hello`, vague fragments, and non-software requests are blocked before the LLM or workflow runs.

The dashboard calls:

```text
POST /api/requirements/validate
```

The API also enforces the same guardrail before creating a run, so direct API calls cannot accidentally start the full pipeline with non-software input.

Write requirements as concrete build tasks:

```text
Build a FastAPI task tracker with a Streamlit dashboard, SQLite storage, tests, and Docker setup.
```

## LLM Providers

Default local provider:

- Provider: Ollama
- Endpoint: `http://localhost:11434`
- Recommended local model: `qwen2.5-coder`

Mission Control checks Ollama through:

```text
http://localhost:11434/api/tags
```

If Ollama is running and has installed models, the dashboard selects a detected local model automatically. If Ollama is not running, it tells you to run `ollama serve`.

Cloud providers:

- OpenAI
- Claude/Anthropic

Set keys in `.env` or your shell:

```bash
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
```

Mission Control detects whether those keys are configured and disables cloud runs when a required key is missing. Keys are never hardcoded in source.

## Quality Gates

The system has several layers to avoid bad generated projects:

- Requirement guardrail blocks non-build requests.
- Python artifact sanitizer removes accidental whole-file indentation and code fences.
- Python artifacts are compile-checked before being stored or written.
- Tester Agent reports bugs and suggestions.
- Deterministic evaluation checks required artifacts, routes, tests, quality signals, and requirement-specific behavior.
- Optional LLM-as-judge evaluation checks whether the generated app actually matches the user requirement.
- Deployment approval is blocked when final evaluation fails.

The evaluation modules live in:

- `evaluation/schemas.py`
- `evaluation/deterministic.py`
- `evaluation/llm_judge.py`
- `evaluation/scorer.py`

## Generated Output

Generated projects are written under:

```text
generated_projects/run_<id>/
```

Typical output:

```text
generated_projects/run_<id>/
├── generated_backend/
├── generated_frontend/
├── generated_tests/
└── deployment/
```

Deployment artifacts usually include:

- `deployment/Dockerfile.backend`
- `deployment/docker-compose.generated.yml`
- `deployment/run_local.sh`
- `deployment/DEPLOYMENT.md`

## Dashboard Features

Mission Control shows:

- Provider/model selector
- Requirement input
- Recent runs
- Agent status cards
- Workflow progress
- Live activity log
- Generated files
- Agent messages
- Memory and context snapshots
- Evaluation scores
- Run-scoped read-only chat
- Stop, resume, restart, and approve deployment controls

On a fresh dashboard load, no previous run is auto-opened. You can select a run from Recent Runs when you want to inspect history.

## API Endpoints

```text
GET  /health
GET  /api/providers
GET  /api/os/capabilities
POST /api/requirements/validate
POST /api/runs
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/runs/{run_id}/logs
GET  /api/runs/{run_id}/status
GET  /api/runs/{run_id}/outputs
GET  /api/runs/{run_id}/chat
POST /api/runs/{run_id}/chat
POST /api/runs/{run_id}/approve-deployment
POST /api/runs/{run_id}/stop
POST /api/runs/{run_id}/resume
POST /api/runs/{run_id}/restart
```

## Project Structure

```text
.
├── agents/              LangChain-based agent definitions
├── app/                 Uvicorn entrypoint and Agentic OS core contracts
├── backend/app/         FastAPI API server
├── config/              Shared defaults
├── context/             Focused context builder
├── dashboard/           Streamlit Mission Control dashboard
├── database/            SQLite models, session, repository
├── diagrams/            Architecture notes and ASCII diagrams
├── docs/                Human-facing guides
├── evaluation/          Deterministic and LLM-as-judge scoring
├── generated_projects/  Per-run generated code output
├── guardrails/          Manager input validation
├── llm_providers/       Provider/model abstraction
├── memory/              Short-term and long-term memory
├── observability/       Structured trace helpers
├── prompts/             Agent prompt templates
├── samples/             Demo prompts
├── scripts/             Local helper scripts
├── skills/              Markdown skills and fallback artifacts
├── tests/               Unit tests
├── tools/               Artifact sanitizer, file writer, tool registry, MCP descriptors
└── workflows/           LangGraph orchestration
```

## Agentic OS Modules

```text
app/core/control_loop.py      reusable execution phases and retry/refinement policy
app/core/agentic_os.py        capability facade for API and dashboard
agents/catalog.py             full future agent catalog
tools/registry.py             permissioned local tool registry
tools/permissions.py          human approval policy for registered tools
tools/mcp.py                  MCP-compatible manifest/descriptors
llm_providers/catalog.py      model provider capability metadata
llm_providers/router.py       fallback/metrics router facade
prompts/assembler.py          dynamic prompt composition
observability/tracing.py      structured trace events persisted through logs
evaluation/consistency.py     backend/frontend/test route consistency
evaluation/test_execution.py  generated pytest execution
```

## How Agents Communicate

Agents communicate through LangGraph state and persisted records:

- Backend Agent writes backend artifacts and a summary.
- Frontend Agent receives backend context and writes UI artifacts.
- Reviewer Agent writes an architecture/code review report.
- Security Agent writes a security review report and can report blockers.
- Tester Agent reviews artifacts and writes tests.
- Generated tests are executed in an isolated temporary directory when possible.
- Evaluator Agent writes quality-gate notes.
- Evaluation records pass/fail scores.
- If needed, the workflow sends feedback into up to two revision passes.
- Deployment Agent runs only after evaluation passes and the human manager approves.

The Agentic OS control-loop snapshot also tracks phase, current agent, retry/refinement counters, and metadata so future dashboard views can show graph state and repair loops directly.

Persistence includes:

- run status
- agent status
- activity logs
- generated files
- agent messages
- context snapshots
- short-term memory
- long-term memory
- evaluation results

## Add A New Agent

1. Create a prompt file in `prompts/`.
2. Add any reusable ability as a Markdown file in `skills/`.
3. Register the skill in `skills/registry.py`.
4. Create an agent class in `agents/` using `BaseAgent`.
5. Add the agent name to `database/repository.py`.
6. Add a node and route in `workflows/software_team_graph.py`.
7. Add dashboard labels/status display in `dashboard/app.py`.
8. Add tests for routing, fallback behavior, and generated artifacts.

The core contract is `AgentOutput`: `summary`, `artifacts`, `notes`, and `bugs`.

## Troubleshooting

If Ollama is not detected:

```bash
ollama serve
ollama pull qwen2.5-coder
```

If cloud provider buttons are disabled, add the matching key to `.env` and restart FastAPI.

If a run is stopped, fails, or is interrupted by a FastAPI restart, select it from Recent Runs and click Resume. Mission Control keeps the last stage, existing artifacts, memory, logs, and context snapshots, then continues from that stage instead of starting over.

If generated Python has indentation issues, new runs should be normalized automatically by `tools/artifact_sanitizer.py`.

If a generated app does not match the requirement, check the Evaluation tab. Failed final evaluation blocks deployment approval.

## Tests

```bash
python -m pytest
```

Current coverage includes provider detection, requirement guardrails, artifact sanitizing, skill loading, workflow routing, file writing, agent parsing, sample examples, and evaluation scoring.
