# Agentic Software Development Team

Local Mission Control for an AI software team. You are the human manager; the agents build, test, review, and prepare deployment files.

Agents:

- Backend Agent
- Frontend Agent
- Tester Agent
- Deployment Agent

Default stack: Ollama, FastAPI, React/Vite, LangChain, LangGraph, and SQLite.

The project is now being refactored toward an Agentic OS: a local-first platform for multi-agent orchestration, skills, tools, memory, guardrails, evaluation, observability, and MCP-compatible integrations.

## Quick Start

Create the environment:

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

Start the API:

```bash
uvicorn app.main:app --reload
```

Install and start the React dashboard in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Dashboard: http://localhost:3000
- API health: http://localhost:8000/health

The previous Streamlit dashboard is still available for compatibility:

```bash
streamlit run dashboard/app.py
```

You can also use:

```bash
bash scripts/run_local.sh
```

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

## What Happens

```text
Requirement -> Backend -> Frontend -> Testing -> Human Approval -> Deployment
```

Mission Control validates your requirement before starting. If testing or evaluation fails, the workflow gets one revision pass. If evaluation still fails, deployment approval is blocked. Stopped, failed, or interrupted runs can be resumed from their saved stage.

The workflow now records Agentic OS control-loop phases:

```text
sense -> plan -> act -> evaluate -> refine -> retry -> finalize
```

Generated files are written to:

```text
generated_projects/run_<id>/
```

## LLM Providers

Default local provider:

- Ollama endpoint: `http://localhost:11434`
- Recommended model: `qwen2.5-coder`

Optional cloud providers:

- OpenAI with `OPENAI_API_KEY`
- Claude/Anthropic with `ANTHROPIC_API_KEY`

Mission Control detects installed Ollama models and configured API keys automatically.

## Useful Commands

Run tests:

```bash
python -m pytest
```

Run with Docker Compose:

```bash
cp .env.example .env
docker compose up --build
docker compose exec ollama ollama pull qwen2.5-coder
```

Docker Compose starts:

- React dashboard: http://localhost:3000
- Legacy Streamlit dashboard: http://localhost:8501
- FastAPI backend: http://localhost:8000

## More Documentation

- [Project guide](docs/PROJECT_GUIDE.md)
- [Agentic OS architecture](docs/AGENTIC_OS_ARCHITECTURE.md)
- [File-by-file project info](diagrams/PROJECTINFO.md)
- [System flow](diagrams/SystemFlow.md)
- [Database and memory architecture](diagrams/DatabaseMemoryArchitecture.md)
- [LLM provider flow](diagrams/LLMProviderFlow.md)
