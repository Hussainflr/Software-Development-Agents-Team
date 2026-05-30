import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.agentic_os import AgenticOSRuntime
from backend.app.config import get_settings
from backend.app.schemas import (
    ActionResponse,
    AgentLogResponse,
    AgentStatusResponse,
    EvaluationResponse,
    GeneratedFileResponse,
    ProvidersResponse,
    RequirementValidationRequest,
    RequirementValidationResponse,
    RunCreate,
    RunDetailResponse,
    RunResponse,
)
from database.repository import Repository
from database.session import init_db
from guardrails import validate_requirement
from llm_providers.base import ProviderConnectionError, ProviderModelNotFoundError
from llm_providers.factory import (
    api_key_configured,
    cloud_provider_status,
    model_recommendations,
    normalize_provider,
    ollama_discovery_status,
    provider_options,
    resolve_model,
    suggested_provider_model,
)
from workflows.software_team_graph import SoftwareTeamWorkflow


settings = get_settings()
repository = Repository()
workflow = SoftwareTeamWorkflow(repository=repository)
agentic_os = AgenticOSRuntime()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    settings.generated_root.mkdir(parents=True, exist_ok=True)
    repository.interrupt_active_runs()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def launch_background(target, run_id: int) -> None:
    thread = threading.Thread(target=target, args=(run_id,), daemon=True)
    thread.start()


def run_detail(run_id: int) -> RunDetailResponse:
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunDetailResponse(
        **RunResponse.model_validate(run).model_dump(),
        statuses=repository.list_agent_statuses(run_id),
        logs=repository.list_logs(run_id),
        files=repository.list_files(run_id),
        messages=repository.list_messages(run_id),
        contexts=repository.list_context_snapshots(run_id),
        short_term_memory=repository.list_short_term_memory(run_id),
        long_term_memory=repository.list_long_term_memory(limit=20),
        evaluations=repository.list_evaluations(run_id),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/providers", response_model=ProvidersResponse)
def providers() -> ProvidersResponse:
    discovery = ollama_discovery_status()
    suggested_provider, suggested_model = suggested_provider_model(discovery)
    return ProvidersResponse(
        default_provider=suggested_provider,
        default_model=suggested_model,
        options=provider_options(),
        suggested_provider=suggested_provider,
        suggested_model=suggested_model,
        model_recommendations=model_recommendations(discovery),
        max_parallel_runs=settings.max_parallel_runs,
        active_run_count=repository.count_active_runs(),
        **cloud_provider_status(),
        **discovery,
    )


@app.get("/api/os/capabilities")
def os_capabilities() -> dict[str, object]:
    return agentic_os.capabilities()


@app.post("/api/requirements/validate", response_model=RequirementValidationResponse)
def validate_manager_requirement(payload: RequirementValidationRequest) -> RequirementValidationResponse:
    return RequirementValidationResponse(**validate_requirement(payload.requirement).model_dump())


def enforce_parallel_run_limit() -> None:
    active_count = repository.count_active_runs()
    if active_count >= settings.max_parallel_runs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{active_count} runs are already active. Finish, stop, or approve one before starting another.",
        )


@app.post("/api/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate) -> RunResponse:
    requirement_validation = validate_requirement(payload.requirement)
    if not requirement_validation.allowed:
        raise HTTPException(
            status_code=422,
            detail=requirement_validation.model_dump(),
        )
    enforce_parallel_run_limit()

    try:
        provider = normalize_provider(payload.provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if provider in {"openai", "anthropic"} and not api_key_configured(provider):
        key_name = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{key_name} is not configured. Add it to .env or your shell environment and restart the API.",
        )
    try:
        model = resolve_model(provider, payload.model)
    except ProviderConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ProviderModelNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    run = repository.create_run(
        requirement=payload.requirement.strip(),
        provider=provider,
        model=model,
    )
    launch_background(workflow.run_until_approval, run.id)
    return RunResponse.model_validate(run)


@app.get("/api/runs", response_model=list[RunResponse])
def list_runs(limit: int = 20) -> list[RunResponse]:
    return [RunResponse.model_validate(run) for run in repository.list_runs(limit=limit)]


@app.get("/api/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: int) -> RunDetailResponse:
    return run_detail(run_id)


@app.get("/api/runs/{run_id}/logs")
def get_logs(run_id: int) -> list[AgentLogResponse]:
    if not repository.get_run(run_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return [AgentLogResponse.model_validate(row) for row in repository.list_logs(run_id)]


@app.get("/api/runs/{run_id}/status")
def get_status(run_id: int):
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return {
        "run": RunResponse.model_validate(run),
        "agents": [AgentStatusResponse.model_validate(row) for row in repository.list_agent_statuses(run_id)],
        "evaluations": [EvaluationResponse.model_validate(row) for row in repository.list_evaluations(run_id)],
    }


@app.get("/api/runs/{run_id}/outputs")
def get_outputs(run_id: int) -> list[GeneratedFileResponse]:
    if not repository.get_run(run_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return [GeneratedFileResponse.model_validate(row) for row in repository.list_files(run_id)]


@app.post("/api/runs/{run_id}/approve-deployment", response_model=ActionResponse)
def approve_deployment(run_id: int) -> ActionResponse:
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if run.status != "waiting_approval":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run is '{run.status}', not waiting for deployment approval.",
        )

    updated = repository.update_run(
        run_id,
        approved_for_deployment=True,
        stop_requested=False,
        status="running",
        current_stage="deployment",
    )
    repository.add_log(
        run_id,
        "Human Manager",
        "Deployment approved",
        "Human manager approved deployment. Deployment Agent is preparing artifacts.",
        status="success",
    )
    launch_background(workflow.run_deployment, run_id)
    return ActionResponse(message="Deployment approved.", run=RunResponse.model_validate(updated))


@app.post("/api/runs/{run_id}/stop", response_model=ActionResponse)
def stop_run(run_id: int) -> ActionResponse:
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    updated = repository.update_run(run_id, stop_requested=True, status="stopped")
    repository.add_log(
        run_id,
        "Human Manager",
        "Stop requested",
        "The run will stop at the next workflow boundary. You can resume it from the current stage.",
        status="warning",
    )
    return ActionResponse(message="Stop requested.", run=RunResponse.model_validate(updated))


@app.post("/api/runs/{run_id}/resume", response_model=ActionResponse)
def resume_run(run_id: int) -> ActionResponse:
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if run.status not in {"failed", "stopped", "interrupted"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run is '{run.status}', not failed, stopped, or interrupted.",
        )
    enforce_parallel_run_limit()

    updated = repository.update_run(run_id, stop_requested=False)
    repository.add_log(
        run_id,
        "Human Manager",
        "Resume requested",
        f"Resume requested from stage '{run.current_stage}'.",
        status="success",
    )
    launch_background(workflow.resume_run, run_id)
    return ActionResponse(message="Resume requested.", run=RunResponse.model_validate(updated))


@app.post("/api/runs/{run_id}/restart", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def restart_run(run_id: int) -> RunResponse:
    run = repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    enforce_parallel_run_limit()
    restarted = repository.create_run(run.requirement, run.provider, run.model)
    repository.add_log(
        restarted.id,
        "Human Manager",
        "Run restarted",
        f"Restarted from run {run_id}.",
        status="info",
    )
    launch_background(workflow.run_until_approval, restarted.id)
    return RunResponse.model_validate(restarted)
