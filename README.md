# Agentic Software Development Team

Local Mission Control for an AI software team. You are the human manager: you enter a software requirement, choose an LLM provider/model, and the agents plan, build, review, test, evaluate, and prepare deployment files.

The current stack is:

- Ollama by default, with optional OpenAI and Anthropic providers
- FastAPI backend
- React/Vite Mission Control dashboard
- LangChain agents
- LangGraph workflow orchestration
- SQLite persistence
- Short-term and long-term memory
- Context snapshots, structured logs, and evaluation scores

## What Is Agentic AI?

Agentic AI means the system does more than answer one prompt. It breaks a goal into steps, gives specialist agents clear responsibilities, passes focused context between them, evaluates their work, and asks for human approval before sensitive actions like deployment.

In this project, the agents act like a small software delivery team.

## Agents

- Planner Agent creates the plan and acceptance criteria.
- Backend Agent creates backend code and API artifacts.
- Frontend Agent creates UI artifacts.
- Reviewer Agent checks architecture and consistency.
- Security Agent checks secrets and risky behavior.
- Tester Agent creates/reviews tests and reports bugs.
- Evaluator Agent scores correctness, completeness, and code quality.
- Deployment Agent creates Docker and local deployment files after approval.

## Quick Start

Create the Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start Ollama:

```bash
ollama pull qwen2.5-coder
ollama serve
```

Start the API and React dashboard:

```bash
bash scripts/run_local.sh
```

Open:

- Dashboard: http://localhost:3000
- API health: http://localhost:8000/health

The local script uses a scoped reload watcher. This matters because generated projects contain Python files; broad project-root reload watching can restart FastAPI during a run and mark the run as interrupted.

By default, Mission Control allows up to five active runs at the same time. Change `MAX_PARALLEL_RUNS` in `.env` if you want a different local limit.

## Manual Local Start

Start the API:

```bash
uvicorn app.main:app --reload \
  --reload-dir agents \
  --reload-dir app \
  --reload-dir backend \
  --reload-dir config \
  --reload-dir context \
  --reload-dir database \
  --reload-dir evaluation \
  --reload-dir guardrails \
  --reload-dir llm_providers \
  --reload-dir memory \
  --reload-dir observability \
  --reload-dir prompts \
  --reload-dir skills \
  --reload-dir tools \
  --reload-dir workflows \
  --reload-exclude 'generated_projects/*' \
  --reload-exclude 'frontend/*' \
  --reload-exclude '.venv/*'
```

Start the React dashboard in another terminal:

```bash
cd frontend
npm install
npm run dev
```

The previous Streamlit dashboard is still available for compatibility:

```bash
streamlit run dashboard/app.py
```

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
docker compose exec ollama ollama pull qwen2.5-coder
```

Docker Compose starts:

- React dashboard: http://localhost:3000
- FastAPI backend: http://localhost:8000
- Ollama: http://localhost:11434
- Legacy Streamlit dashboard: http://localhost:8501

## Try A Demo

Paste this into Mission Control:

```text
Build a Rock Paper Scissors game.

Requirements:
- FastAPI backend with an endpoint to play one round.
- Player chooses rock, paper, or scissors.
- Backend randomly chooses computer move.
- Return winner, player move, and computer move.
- Frontend with three buttons: Rock, Paper, Scissors.
- Show round result.
- Tester writes API tests.
- Deployment Agent creates Docker/local run files.
```

More samples:

- [Rock Paper Scissors prompt](samples/rock_paper_scissors_prompt.md)
- [Rock Paper Scissors backend test example](samples/rock_paper_scissors_backend_test.py)
- [Task tracker prompt](samples/demo_prompt.md)

## How A Run Works

```text
Requirement
  -> Planner
  -> Backend
  -> Frontend
  -> Review
  -> Security
  -> Testing
  -> Evaluation
  -> Human Approval
  -> Deployment
```

If testing or evaluation finds issues, the workflow gets one refinement pass:

```text
Tester/Evaluator -> Backend revision -> Frontend revision -> Retest
```

If the final evaluation fails, deployment approval is blocked. If a run is stopped, fails, or gets interrupted by a server restart, the Resume action continues from the best saved workflow stage instead of starting from the beginning.

Generated files are written to:

```text
generated_projects/run_<id>/
```

## Context Engineering

Context engineering means deciding what information each agent should see.

This project does not send the full history blindly. `context/context_builder.py` builds focused context like:

```json
{
  "user_requirement": "...",
  "current_task": "...",
  "agent_role": "...",
  "relevant_outputs": "...",
  "constraints": "...",
  "errors_or_feedback": "..."
}
```

That keeps prompts smaller, easier to understand, and less likely to confuse the model.

## Memory

Short-term memory stores run-level information:

- current task
- agent outputs
- logs
- workflow state
- test/evaluation results

Long-term memory stores reusable knowledge:

- successful solution summaries
- reusable patterns
- common errors and fixes
- evaluation summaries

Memory is stored in SQLite and is designed so a vector/RAG store can be added later. Secrets and API keys should not be stored in memory.

## LLM Providers

Default local provider:

- Provider: Ollama
- Endpoint: `http://localhost:11434`
- Recommended model: `qwen2.5-coder`
- Supported local models include `llama3.1` and `qwen2.5-coder`

Optional cloud providers:

- OpenAI with `OPENAI_API_KEY`
- Anthropic/Claude with `ANTHROPIC_API_KEY`

Provider selection is controlled by environment variables and the dashboard selector. Keys are never hardcoded in source.

## Mission Control Dashboard

The React dashboard includes:

- manager requirement input
- LLM provider/model selector
- recent runs in a bounded list with running-run indicators
- workflow progress
- agent status cards
- live logs
- generated files
- agent messages
- evaluation scores
- Memory and Context tab
- stop, resume, restart, and approve deployment controls

The dashboard allows five parallel active workflows by default. Active runs are pinned to the top of Recent Runs. If the active-run limit is reached, the prompt box stays usable for drafting, but launching another run is disabled until one active run finishes, stops, or moves out of the active set.

On a fresh dashboard load, no previous run is auto-opened. Logs, files, memory, and context views stay clean until you start or select a run.

## Backend API

Main endpoints:

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
POST /api/runs/{run_id}/approve-deployment
POST /api/runs/{run_id}/stop
POST /api/runs/{run_id}/resume
POST /api/runs/{run_id}/restart
```

## Project Structure

```text
agents/              LangChain-based agent definitions
app/                 Uvicorn entrypoint and Agentic OS core contracts
backend/app/         FastAPI API server
config/              Shared defaults
context/             Focused context builder
dashboard/           Legacy Streamlit dashboard
database/            SQLite models, session, repository
diagrams/            Architecture notes and diagrams
docs/                Human-facing guides
evaluation/          Deterministic and LLM-as-judge scoring
frontend/            React/Vite dashboard
generated_projects/  Per-run generated code output
guardrails/          Manager input validation
llm_providers/       Provider/model abstraction
memory/              Short-term and long-term memory
observability/       Structured trace helpers
prompts/             Agent prompt templates
samples/             Demo prompts
scripts/             Local helper scripts
skills/              Skills registry and reusable capability docs
tests/               Unit tests
tools/               Artifact sanitizer, file writer, tool registry
workflows/           LangGraph orchestration
```

## Useful Commands

Run tests:

```bash
python -m pytest
```

Build the React dashboard:

```bash
cd frontend
npm run build
```

Run only the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Future: Multi-User Support

Authentication and per-user isolation are planned for a later phase after the single-user local workflow is stable.

Planned:

- user login/register
- per-user runs, logs, files, memory, and evaluations
- role-based deployment approval
- audit trail for sensitive actions
- optional per-user provider/model preferences

## More Documentation

- [Project guide](docs/PROJECT_GUIDE.md)
- [Agentic OS architecture](docs/AGENTIC_OS_ARCHITECTURE.md)
- [LangChain guide](diagrams/LANGCHAIN_GUIDE.md)
- [File-by-file project info](diagrams/PROJECTINFO.md)
- [System flow](diagrams/SystemFlow.md)
- [Database and memory architecture](diagrams/DatabaseMemoryArchitecture.md)
- [LLM provider flow](diagrams/LLMProviderFlow.md)
