# Agentic Software Development Team

Production-style local demo where you are the human manager and four AI agents act as a software team:

- Backend Agent
- Frontend Agent
- Tester Agent
- Deployment Agent

The app runs locally with Ollama by default, uses FastAPI for the backend, Streamlit for Mission Control, LangChain for agent internals, LangGraph for workflow control, and SQLite for run history.

## Folder Structure

```text
.
├── agents/              # LangChain-based agent definitions
├── app/                 # uvicorn compatibility entrypoint
├── backend/app/         # FastAPI application
├── config/              # Shared defaults
├── context/             # Context engineering
├── dashboard/           # Streamlit Mission Control dashboard
├── database/            # SQLite models, session, repository
├── evaluation/          # Correctness/completeness/code-quality scoring
├── generated_projects/  # Per-run generated code output
├── llm_providers/       # LangChain provider abstraction
├── memory/              # Short-term and long-term memory
├── prompts/             # Prompt templates
├── samples/             # Demo prompt
├── scripts/             # Local helper scripts
├── skills/              # Reusable agent skills and fallback artifacts
├── tests/               # Unit tests
├── tools/               # Infrastructure utilities
└── workflows/           # LangGraph workflow
```

## What Is Agentic AI?

Agentic AI means the system splits work across specialized AI workers. In this project, one agent handles backend code, one handles frontend code, one tests/reviews, and one prepares deployment files. The human manager still controls the run and must approve deployment.

## How LangChain Is Used

LangChain is the core agent layer:

- prompt templates are loaded from `prompts/`
- model providers are wrapped in `llm_providers/langchain_client.py`
- agent outputs are parsed with Pydantic output parsers
- reusable skills are described in `skills/`

LangGraph remains the workflow controller. It decides which agent runs next and when to loop back for fixes.

## Context Engineering

Context engineering means each agent receives a focused brief instead of the entire history. `context/context_builder.py` builds this shape:

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

This keeps prompts smaller, clearer, and easier to debug.

## Memory System

Short-term memory stores run-specific summaries such as agent outputs, latest evaluation, and context snapshots. It is tied to one run.

Long-term memory stores reusable summaries from successful runs, such as useful patterns and artifact sets. It avoids secrets and is designed so a vector database/RAG layer can replace the simple SQLite search later.

Mission Control has a `Memory & Context` tab that shows both memory layers and the exact context sent to each agent.

## Evaluation

The evaluation layer scores:

- correctness
- completeness
- code quality

If testing or evaluation fails, the workflow triggers the refinement loop before waiting for deployment approval.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Install and start Ollama:

```bash
ollama pull qwen2.5-coder
ollama serve
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Run Mission Control in another terminal:

```bash
streamlit run dashboard/app.py
```

Open:

- API health: http://localhost:8000/health
- Dashboard: http://localhost:8501

## Demo Flow

1. Paste a requirement into Mission Control, or use `samples/demo_prompt.md`.
2. Select provider `Ollama` and model `qwen2.5-coder` or `llama3.1`.
3. Click `Start Run`.
4. Watch agent status cards, the live log, memory, context, and evaluation tabs.
5. Review generated files after Backend, Frontend, and Tester complete.
6. Click `Approve Deployment` to let the Deployment Agent create Docker/local deployment artifacts.
7. Generated code is written to `generated_projects/run_<id>/`.

If Ollama is not running, the run fails with a clear message telling you to run `ollama serve` and pull a model.

## Provider Switching

Mission Control can switch between:

- Ollama
- OpenAI
- Claude/Anthropic

The selected provider and model are stored on each run. API keys are read only from environment variables:

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Never place API keys in source code.

## How Agents Communicate

Agents communicate through shared LangGraph state, focused context snapshots, short-term memory, and persistent SQLite records.

- The Backend Agent writes backend artifacts and a summary.
- The Frontend Agent receives relevant backend context and creates UI artifacts.
- The Tester Agent reviews generated artifacts, writes tests, and returns bugs if found.
- The evaluator scores correctness, completeness, and code quality.
- If bugs or evaluation failures are found, the workflow sends feedback back for one revision pass.
- After testing, the workflow pauses at `waiting_approval`.
- The Deployment Agent only runs after the human manager approves deployment.

Every step is persisted as:

- agent status
- structured activity log
- agent message
- generated file
- context snapshot
- memory summary
- evaluation score

## API Endpoints

```text
GET  /health
GET  /api/providers
POST /api/runs
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/runs/{run_id}/logs
GET  /api/runs/{run_id}/status
GET  /api/runs/{run_id}/outputs
POST /api/runs/{run_id}/approve-deployment
POST /api/runs/{run_id}/stop
POST /api/runs/{run_id}/restart
```

## Docker Compose

For containerized Mission Control with Ollama, API, and dashboard:

```bash
cp .env.example .env
docker compose up --build
```

Pull the default model inside the Ollama container before your first run:

```bash
docker compose exec ollama ollama pull qwen2.5-coder
```

## Add A New Agent

1. Create a prompt file in `prompts/`.
2. Add any reusable ability to `skills/` and document it in `skills.md`.
3. Create an agent class in `agents/` using `BaseAgent`.
4. Add the agent name to `database/repository.py`.
5. Add a node and routing rule in `workflows/software_team_graph.py`.
6. Add a status card label in `dashboard/app.py`.

The important contract is the Pydantic `AgentOutput`: a summary, artifacts, notes, and optional bugs.

## Tests

```bash
pytest
```
