# Agentic Software Development Team

Production-style local demo where you are the human manager and four AI agents act as a software team:

- Backend Agent
- Frontend Agent
- Tester Agent
- Deployment Agent

The first version runs locally with Ollama by default, uses FastAPI for the backend, Streamlit for Mission Control, LangGraph for workflow orchestration, LiteLLM for provider switching, and SQLite for run history.

## Folder Structure

```text
.
├── agents/              # Backend, Frontend, Tester, Deployment agents
├── app/                 # uvicorn compatibility entrypoint
├── backend/app/         # FastAPI application
├── dashboard/           # Streamlit Mission Control dashboard
├── database/            # SQLite models, session, repository
├── generated_projects/  # Per-run generated code output
├── llm_providers/       # LiteLLM provider abstraction
├── samples/             # Demo prompt
├── scripts/             # Local helper scripts
├── tests/               # Unit tests
├── tools/               # Shared utilities
└── workflows/           # LangGraph workflow
```

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
4. Watch agent status cards and the live activity log.
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

Agents communicate through a shared LangGraph state and persistent SQLite records.

- The Backend Agent writes backend artifacts and a summary.
- The Frontend Agent receives existing artifact paths and creates UI artifacts.
- The Tester Agent reviews all artifacts, writes tests, and returns bugs if found.
- If bugs are found, LangGraph sends feedback back to Backend and Frontend for one revision pass.
- After testing, the workflow pauses at `waiting_approval`.
- The Deployment Agent only runs after the human manager approves deployment.

Every step is persisted as:

- agent status
- activity log
- agent message
- generated file

## API Endpoints

```text
GET  /health
GET  /api/providers
POST /api/runs
GET  /api/runs
GET  /api/runs/{run_id}
POST /api/runs/{run_id}/approve-deployment
POST /api/runs/{run_id}/stop
POST /api/runs/{run_id}/restart
```

## Docker Compose

For containerized Mission Control:

```bash
cp .env.example .env
docker compose up --build
```

When running Docker on macOS or Windows, the compose file points `OLLAMA_BASE_URL` to `http://host.docker.internal:11434` so containers can reach the host Ollama service.

## Add A New Agent

1. Create `agents/security_agent.py` and subclass `BaseAgent`.
2. Implement `task_instructions()` and `fallback_output()`.
3. Add the agent name to `database/repository.py`.
4. Add a node in `workflows/software_team_graph.py`.
5. Add edges or conditional routing for where the agent belongs.
6. Add a status card label in `dashboard/app.py`.

The important contract is `AgentResult`: a summary, artifacts, notes, and optional bugs.

## Tests

```bash
pytest
```

