import os
import json
import time
from datetime import datetime
from html import escape

import requests
import streamlit as st


API_URL = os.getenv("MISSION_CONTROL_API_URL", "http://localhost:8000").rstrip("/")
AGENT_ORDER = [
    "Planner Agent",
    "Backend Agent",
    "Frontend Agent",
    "Reviewer Agent",
    "Security Agent",
    "Tester Agent",
    "Evaluator Agent",
    "Deployment Agent",
]
STAGES = ["Requirement", "Plan", "Backend", "Frontend", "Review", "Testing", "Approval", "Deployment"]
STAGE_PROGRESS = {
    "requirement": 5,
    "planning": 12,
    "backend": 24,
    "backend_revision": 30,
    "frontend": 40,
    "frontend_revision": 45,
    "review": 55,
    "security": 65,
    "testing": 75,
    "evaluation": 82,
    "deployment_approval": 88,
    "deployment": 92,
    "completed": 100,
    "stopped": 0,
}
STATUS_COLORS = {
    "idle": "#6b7280",
    "thinking": "#b7791f",
    "working": "#2563eb",
    "completed": "#047857",
    "failed": "#b91c1c",
}


st.set_page_config(page_title="Mission Control", layout="wide")
st.markdown(
    """
    <style>
      :root {
        --mc-ink: #111827;
        --mc-muted: #667085;
        --mc-line: #d7dde7;
        --mc-panel: #ffffff;
        --mc-soft: #f6f8fb;
        --mc-blue: #2563eb;
        --mc-green: #047857;
        --mc-red: #b91c1c;
        --mc-amber: #b7791f;
      }
      .stApp { background: #f5f7fb; }
      .block-container { padding-top: 1.1rem; max-width: 1360px; }
      div[data-testid="stSidebarContent"] {
        background: #ffffff;
        border-right: 1px solid #dde3ec;
      }
      h1, h2, h3 { letter-spacing: 0; color: var(--mc-ink); }
      .mc-topbar {
        border: 1px solid var(--mc-line);
        border-radius: 8px;
        padding: 1rem 1.15rem;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        margin-bottom: 1rem;
      }
      .mc-title {
        font-size: 1.55rem;
        line-height: 1.2;
        font-weight: 800;
        color: var(--mc-ink);
      }
      .mc-subtitle {
        margin-top: 0.25rem;
        color: var(--mc-muted);
        font-size: 0.92rem;
      }
      .mc-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border: 1px solid var(--mc-line);
        border-radius: 999px;
        padding: 0.22rem 0.55rem;
        font-size: 0.78rem;
        font-weight: 700;
        background: #ffffff;
        color: #344054;
        white-space: nowrap;
      }
      .mc-pill.success { border-color: #a7f3d0; background: #ecfdf5; color: #047857; }
      .mc-pill.warning { border-color: #fde68a; background: #fffbeb; color: #92400e; }
      .mc-pill.error { border-color: #fecaca; background: #fef2f2; color: #991b1b; }
      .mc-dot { width: 0.48rem; height: 0.48rem; border-radius: 999px; display: inline-block; background: currentColor; }
      .mc-panel {
        border: 1px solid var(--mc-line);
        border-radius: 8px;
        background: var(--mc-panel);
        padding: 0.95rem;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        min-height: 100%;
      }
      .mc-section-title {
        font-size: 0.92rem;
        font-weight: 800;
        color: var(--mc-ink);
        margin-bottom: 0.2rem;
      }
      .mc-section-subtitle {
        font-size: 0.82rem;
        color: var(--mc-muted);
        margin-bottom: 0.65rem;
      }
      .mc-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.7rem 0 1rem 0;
      }
      .mc-kpi {
        border: 1px solid var(--mc-line);
        border-radius: 8px;
        background: #ffffff;
        padding: 0.72rem 0.8rem;
      }
      .mc-kpi-label { color: var(--mc-muted); font-size: 0.76rem; font-weight: 700; }
      .mc-kpi-value { color: var(--mc-ink); font-size: 1.12rem; font-weight: 800; margin-top: 0.15rem; }
      .agent-card {
        border: 1px solid #d9e0ea;
        border-radius: 8px;
        padding: 0.8rem;
        background: #ffffff;
        min-height: 112px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
      }
      .agent-name { font-weight: 700; color: #111827; font-size: 0.98rem; }
      .agent-role { color: #5b6472; font-size: 0.82rem; margin-top: 0.15rem; }
      .agent-status {
        margin-top: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        font-weight: 600;
      }
      .status-dot { width: 0.62rem; height: 0.62rem; border-radius: 999px; display: inline-block; box-shadow: 0 0 0 3px rgba(37,99,235,0.08); }
      .stage-row {
        display: grid;
        grid-template-columns: repeat(8, minmax(0, 1fr));
        gap: 0.5rem;
        margin: 0.4rem 0 1rem 0;
      }
      .stage {
        border: 1px solid #d5dbe3;
        border-radius: 8px;
        padding: 0.58rem 0.45rem;
        text-align: center;
        font-size: 0.82rem;
        background: #ffffff;
        min-height: 58px;
      }
      .stage.active { border-color: #2563eb; background: #eff6ff; color: #1d4ed8; font-weight: 700; }
      .stage.done { border-color: #047857; background: #ecfdf5; color: #047857; font-weight: 700; }
      .small-muted { color: #6b7280; font-size: 0.76rem; }
      .mc-run-card {
        border: 1px solid var(--mc-line);
        border-radius: 8px;
        padding: 0.65rem 0.72rem;
        background: #ffffff;
        margin-bottom: 0.45rem;
      }
      .mc-run-title { font-weight: 800; color: var(--mc-ink); font-size: 0.9rem; }
      .mc-run-meta { color: var(--mc-muted); font-size: 0.78rem; margin-top: 0.12rem; }
      @media (max-width: 900px) {
        .mc-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .stage-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=15, **kwargs)
        if response.status_code >= 400:
            st.error(f"API error {response.status_code}: {response.text}")
            return None
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Could not reach Mission Control API at {API_URL}: {exc}")
        return None


def get_providers() -> dict:
    data = api_request("GET", "/api/providers")
    if not data:
        return {
            "api_connected": False,
            "default_provider": "ollama",
            "default_model": "qwen2.5-coder",
            "options": [
                {
                    "id": "ollama",
                    "label": "Ollama",
                    "default_model": "qwen2.5-coder",
                    "requires_api_key": False,
                    "api_key_configured": False,
                }
            ],
            "openai_configured": False,
            "anthropic_configured": False,
            "ollama_running": False,
            "ollama_models": [],
            "detected_model": None,
            "suggested_provider": "ollama",
            "suggested_model": "auto",
            "model_recommendations": [],
            "message": "Mission Control API is unavailable.",
        }
    return {**data, "api_connected": True}


def get_os_capabilities() -> dict:
    return api_request("GET", "/api/os/capabilities") or {}


def validate_requirement_with_api(requirement: str) -> dict:
    data = api_request("POST", "/api/requirements/validate", json={"requirement": requirement})
    if data:
        return data
    return {
        "allowed": False,
        "category": "api_unavailable",
        "reason": "Could not validate the requirement because the Mission Control API is unavailable.",
        "guidance": "Start FastAPI with `uvicorn app.main:app --reload`, then try again.",
    }


def unique_models(models: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for model_name in models:
        if model_name and model_name not in seen:
            seen.add(model_name)
            ordered.append(model_name)
    return ordered


def status_tone(status: str) -> str:
    if status in {"completed", "success", "online", "connected", "adapter-ready"}:
        return "success"
    if status in {"failed", "error", "offline", "unavailable"}:
        return "error"
    if status in {"running", "thinking", "working", "waiting_approval", "warning"}:
        return "warning"
    return ""


def status_pill(label: str, status: str) -> str:
    tone = status_tone(status)
    return (
        f'<span class="mc-pill {tone}">'
        f'<span class="mc-dot"></span>{escape(label)}: {escape(status)}</span>'
    )


def topbar_html(providers: dict, os_capabilities: dict) -> str:
    api_status = "connected" if providers.get("api_connected") else "offline"
    ollama_status = "online" if providers.get("ollama_running") else "offline"
    os_status = os_capabilities.get("mcp", {}).get("status", "unavailable") if os_capabilities else "unavailable"
    return f"""
    <div class="mc-topbar">
      <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; flex-wrap:wrap;">
        <div>
          <div class="mc-title">Mission Control</div>
          <div class="mc-subtitle">Agentic OS dashboard for planning, building, testing, reviewing, and deploying local-first software runs.</div>
        </div>
        <div style="display:flex; gap:0.45rem; flex-wrap:wrap; justify-content:flex-end;">
          {status_pill("API", api_status)}
          {status_pill("Ollama", ollama_status)}
          {status_pill("MCP", os_status)}
        </div>
      </div>
    </div>
    """


def kpi_strip_html(detail: dict, statuses: dict[str, str], progress_value: int) -> str:
    completed = sum(1 for value in statuses.values() if value == "completed")
    failed = sum(1 for value in statuses.values() if value == "failed")
    evaluations = detail.get("evaluations") or []
    latest_eval = evaluations[-1] if evaluations else None
    quality = "pending"
    if latest_eval:
        quality = "pass" if latest_eval.get("passed") else "review"
    return f"""
    <div class="mc-kpi-grid">
      <div class="mc-kpi"><div class="mc-kpi-label">Run Status</div><div class="mc-kpi-value">{escape(detail.get("status", "unknown"))}</div></div>
      <div class="mc-kpi"><div class="mc-kpi-label">Progress</div><div class="mc-kpi-value">{progress_value}%</div></div>
      <div class="mc-kpi"><div class="mc-kpi-label">Agents Done</div><div class="mc-kpi-value">{completed}/{len(AGENT_ORDER)}</div></div>
      <div class="mc-kpi"><div class="mc-kpi-label">Quality Gate</div><div class="mc-kpi-value">{quality}{f" / {failed} failed" if failed else ""}</div></div>
    </div>
    """


def status_card(agent_name: str, status: str) -> str:
    color = STATUS_COLORS.get(status, "#6b7280")
    role = {
        "Planner Agent": "Plan and acceptance criteria",
        "Backend Agent": "APIs and data model",
        "Frontend Agent": "UI and API integration",
        "Reviewer Agent": "Architecture and consistency",
        "Security Agent": "Safety and permissions",
        "Tester Agent": "Tests and review",
        "Evaluator Agent": "Quality gate decision",
        "Deployment Agent": "Docker and local deploy",
    }.get(agent_name, "Agent")
    tone = status_tone(status)
    return f"""
    <div class="agent-card" style="border-top: 3px solid {color};">
      <div class="agent-name">{agent_name}</div>
      <div class="agent-role">{role}</div>
      <div class="agent-status">
        <span class="status-dot" style="background:{color}"></span>
        <span class="mc-pill {tone}">{status}</span>
      </div>
    </div>
    """


def progress_html(run: dict, statuses: dict[str, str]) -> str:
    current = run.get("current_stage", "requirement")
    completed = {
        "Requirement": True,
        "Plan": statuses.get("Planner Agent") == "completed",
        "Backend": statuses.get("Backend Agent") == "completed",
        "Frontend": statuses.get("Frontend Agent") == "completed",
        "Review": statuses.get("Reviewer Agent") == "completed" and statuses.get("Security Agent") == "completed",
        "Testing": statuses.get("Tester Agent") == "completed",
        "Approval": run.get("status") in {"waiting_approval", "completed"} or statuses.get("Evaluator Agent") == "completed",
        "Deployment": statuses.get("Deployment Agent") == "completed",
    }
    active_map = {
        "planning": "Plan",
        "backend": "Backend",
        "backend_revision": "Backend",
        "frontend": "Frontend",
        "frontend_revision": "Frontend",
        "review": "Review",
        "security": "Review",
        "testing": "Testing",
        "evaluation": "Testing",
        "deployment_approval": "Approval",
        "deployment": "Deployment",
    }
    active = active_map.get(current, "Requirement")
    cells = []
    for stage in STAGES:
        css_class = "stage done" if completed.get(stage) else "stage active" if stage == active else "stage"
        label = "done" if completed.get(stage) else "active" if stage == active else "waiting"
        cells.append(f'<div class="{css_class}">{stage}<br><span class="small-muted">{label}</span></div>')
    return '<div class="stage-row">' + "".join(cells) + "</div>"


def workflow_progress(run: dict, statuses: dict[str, str]) -> tuple[int, str]:
    if run.get("status") == "completed":
        return 100, "Completed"
    if run.get("status") == "failed":
        return max(STAGE_PROGRESS.get(run.get("current_stage", "requirement"), 5), 5), "Failed"
    if run.get("status") == "stopped":
        return max(STAGE_PROGRESS.get(run.get("current_stage", "requirement"), 5), 5), "Stopped"

    completed_agents = sum(1 for status in statuses.values() if status == "completed")
    agent_bonus = min(completed_agents * 5, 20)
    stage = run.get("current_stage", "requirement")
    progress = min(STAGE_PROGRESS.get(stage, 5) + agent_bonus, 99)
    labels = {
        "requirement": "Requirement accepted",
        "planning": "Planner Agent running",
        "backend": "Backend Agent running",
        "backend_revision": "Backend revision running",
        "frontend": "Frontend Agent running",
        "frontend_revision": "Frontend revision running",
        "review": "Reviewer Agent running",
        "security": "Security Agent running",
        "testing": "Tester Agent running",
        "evaluation": "Evaluator Agent running",
        "deployment_approval": "Waiting for deployment approval",
        "deployment": "Deployment Agent running",
    }
    return progress, labels.get(stage, "Workflow running")


def render_logs(logs: list[dict]) -> None:
    if not logs:
        st.info("No activity yet.")
        return
    rows = [
        {
            "time": format_time(row["timestamp"]),
            "agent": row["agent_name"],
            "action": row["action"],
            "status": row["status"],
            "summary": display_log_summary(row["output_summary"]),
        }
        for row in reversed(logs[-80:])
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


def display_log_summary(value: str) -> str:
    try:
        payload = json.loads(value)
        return payload.get("summary", value)
    except (TypeError, ValueError):
        return value


def format_time(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M:%S")
    except ValueError:
        return value


def language_for(path: str) -> str:
    if path.endswith(".py"):
        return "python"
    if path.endswith((".yml", ".yaml")):
        return "yaml"
    if path.endswith(".md"):
        return "markdown"
    if path.endswith(".sh"):
        return "bash"
    if path.endswith("Dockerfile") or "Dockerfile" in path:
        return "dockerfile"
    return "text"


providers = get_providers()
os_capabilities = get_os_capabilities()
provider_options = providers["options"]
provider_ids = [item["id"] for item in provider_options]
provider_labels = {item["id"]: item["label"] for item in provider_options}
default_provider = providers.get("default_provider", "ollama")
ollama_running = bool(providers.get("ollama_running"))
ollama_models = providers.get("ollama_models", [])
detected_ollama_model = providers.get("detected_model")
model_recommendations = providers.get("model_recommendations", [])

st.markdown(topbar_html(providers, os_capabilities), unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### LLM Provider")
    provider = st.selectbox(
        "Provider",
        provider_ids,
        index=provider_ids.index(default_provider) if default_provider in provider_ids else 0,
        format_func=lambda item: provider_labels.get(item, item),
    )
    selected_provider_option = next((item for item in provider_options if item["id"] == provider), {})
    provider_needs_key = bool(selected_provider_option.get("requires_api_key"))
    provider_has_key = bool(selected_provider_option.get("api_key_configured"))
    default_model = selected_provider_option.get("default_model", "qwen2.5-coder")
    if provider == "ollama":
        if ollama_running and ollama_models:
            model_options = unique_models([detected_ollama_model, *ollama_models, "auto"])
            model = st.selectbox(
                "Model",
                model_options,
                index=0,
                help="Mission Control detected these models from your running Ollama instance.",
            )
            st.success(providers.get("message") or f"Detected local Ollama model: {model}")
        elif ollama_running:
            model = st.text_input("Model", value="auto")
            st.warning("Ollama is running, but no models are installed. Pull a model and refresh.")
            st.code("ollama pull qwen2.5-coder")
        else:
            model = st.text_input("Model", value="auto", disabled=True)
            st.warning(providers.get("message") or "Ollama is not running. Start it and refresh this dashboard.")
            st.code("ollama serve\nollama pull qwen2.5-coder")
    else:
        model = st.text_input("Model", value=default_model)
        if provider_has_key:
            st.success(f"{provider_labels.get(provider, provider)} API key detected from environment.")
        elif provider_needs_key:
            key_name = "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"
            st.warning(f"{key_name} is not configured in `.env` or your shell environment.")
    if model_recommendations:
        st.caption("Recommended models")
        for recommendation in model_recommendations[:3]:
            st.markdown(
                f"- `{recommendation['provider']}` / `{recommendation['model']}`: "
                f"{recommendation['reason']}"
            )
    st.divider()
    st.markdown("### Agentic OS")
    if os_capabilities:
        control_loop = os_capabilities.get("control_loop", {})
        st.caption(
            f"Agents: {len(os_capabilities.get('agents', []))} | "
            f"Tools: {len(os_capabilities.get('tools', []))} | "
            f"MCP: {os_capabilities.get('mcp', {}).get('status', 'unknown')}"
        )
        st.caption(
            "Refinements: "
            f"{control_loop.get('max_refinements', 'n/a')} | "
            "Retries/step: "
            f"{control_loop.get('max_retries_per_step', 'n/a')}"
        )
    else:
        st.caption("OS capability endpoint unavailable.")
    st.divider()
    st.markdown("### Local Commands")
    st.code("ollama serve\nollama pull qwen2.5-coder\nuvicorn app.main:app --reload\nstreamlit run dashboard/app.py")

if "current_run_id" not in st.session_state:
    st.session_state.current_run_id = None

recent_runs = api_request("GET", "/api/runs", params={"limit": 20}) or []

left, right = st.columns([1.05, 0.95])
with left:
    st.markdown(
        """
        <div class="mc-panel">
          <div class="mc-section-title">Manager Requirement</div>
          <div class="mc-section-subtitle">Describe the software outcome. Guardrails will check that it is actionable before agents start.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    requirement = st.text_area(
        "What should the team build?",
        height=180,
        placeholder="Example: Build a small FastAPI task tracker with a Streamlit dashboard and Docker setup.",
    )
    start_disabled = (provider == "ollama" and not ollama_running) or (provider_needs_key and not provider_has_key)
    if provider == "ollama" and not ollama_running:
        st.info("Start Ollama and refresh; Mission Control will detect the local model automatically.")
    elif provider_needs_key and not provider_has_key:
        st.info("Add the provider API key to `.env` or your shell environment, then restart the API.")
    if st.button("Start Run", type="primary", width="stretch", disabled=start_disabled):
        payload = {"requirement": requirement, "provider": provider, "model": model}
        requirement_validation = validate_requirement_with_api(requirement)
        if not requirement_validation["allowed"]:
            st.warning(f"{requirement_validation['reason']} {requirement_validation['guidance']}")
        else:
            created = api_request("POST", "/api/runs", json=payload)
            if created:
                st.session_state.current_run_id = created["id"]
                st.rerun()

with right:
    st.markdown(
        """
        <div class="mc-panel">
          <div class="mc-section-title">Recent Runs</div>
          <div class="mc-section-subtitle">Open a previous run to inspect artifacts, memory, traces, and evaluations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if recent_runs:
        for run in recent_runs[:3]:
            st.markdown(
                f"""
                <div class="mc-run-card">
                  <div style="display:flex; justify-content:space-between; gap:0.5rem; align-items:center;">
                    <div>
                      <div class="mc-run-title">Run {run["id"]}</div>
                      <div class="mc-run-meta">{escape(run["current_stage"])} | {format_time(run["created_at"])}</div>
                    </div>
                    {status_pill("status", run["status"])}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        run_ids = [run["id"] for run in recent_runs]
        current_run_id = st.session_state.get("current_run_id")
        selected_index = run_ids.index(current_run_id) if current_run_id in run_ids else 0
        labels = {run["id"]: f"Run {run['id']} - {run['status']} - {format_time(run['created_at'])}" for run in recent_runs}
        selected = st.selectbox(
            "Open run",
            run_ids,
            index=selected_index,
            format_func=lambda run_id: labels[run_id],
        )
        if st.button("Open Selected Run", width="stretch"):
            st.session_state.current_run_id = selected
            st.rerun()
    else:
        st.info("No runs yet.")

run_id = st.session_state.get("current_run_id")
if run_id:
    detail = api_request("GET", f"/api/runs/{run_id}")
    if detail:
        st.divider()
        st.markdown(
            f"""
            <div class="mc-panel">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; flex-wrap:wrap;">
                <div>
                  <div class="mc-section-title">Run {detail['id']} Control</div>
                  <div class="mc-section-subtitle">{escape(detail.get("current_stage", "unknown"))} | {escape(detail.get("provider", "unknown"))} / {escape(detail.get("model", "unknown"))}</div>
                </div>
                <div style="display:flex; gap:0.45rem; flex-wrap:wrap;">
                  {status_pill("run", detail.get("status", "unknown"))}
                  {status_pill("stage", detail.get("current_stage", "unknown"))}
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        statuses = {row["agent_name"]: row["status"] for row in detail["statuses"]}

        control_cols = st.columns([1, 1, 1, 2])
        with control_cols[0]:
            if detail["status"] == "waiting_approval":
                if st.button("Approve Deployment", type="primary", width="stretch"):
                    api_request("POST", f"/api/runs/{run_id}/approve-deployment")
                    st.rerun()
        with control_cols[1]:
            if detail["status"] in {"running", "waiting_approval"}:
                if st.button("Stop Run", width="stretch"):
                    api_request("POST", f"/api/runs/{run_id}/stop")
                    st.rerun()
        with control_cols[2]:
            if st.button("Restart Run", width="stretch"):
                restarted = api_request("POST", f"/api/runs/{run_id}/restart")
                if restarted:
                    st.session_state.current_run_id = restarted["id"]
                    st.rerun()
        with control_cols[3]:
            st.markdown(
                f"**Status:** `{detail['status']}`  \n"
                f"**Stage:** `{detail['current_stage']}`  \n"
                f"**Provider:** `{detail['provider']}` / `{detail['model']}`"
            )

        progress_value, progress_label = workflow_progress(detail, statuses)
        st.markdown(kpi_strip_html(detail, statuses, progress_value), unsafe_allow_html=True)
        st.progress(progress_value, text=f"{progress_label} - {progress_value}%")
        st.markdown(progress_html(detail, statuses), unsafe_allow_html=True)

        agent_cols = st.columns(4)
        for index, agent_name in enumerate(AGENT_ORDER):
            with agent_cols[index % 4]:
                st.markdown(status_card(agent_name, statuses.get(agent_name, "idle")), unsafe_allow_html=True)

        log_tab, file_tab, message_tab, memory_tab, eval_tab, os_tab = st.tabs(
            ["Live Activity Log", "Generated Files", "Agent Messages", "Memory & Context", "Evaluation", "Agentic OS"]
        )
        with log_tab:
            render_logs(detail["logs"])

        with file_tab:
            files = detail["files"]
            if files:
                paths = [file["path"] for file in files]
                selected_path = st.selectbox("Generated file", paths)
                selected_file = next(file for file in files if file["path"] == selected_path)
                st.caption(f"Generated by {selected_file['agent_name']}")
                st.code(selected_file["content"], language=language_for(selected_path))
            else:
                st.info("Files will appear here as agents complete their work.")

        with message_tab:
            if detail["messages"]:
                for message in detail["messages"]:
                    st.markdown(f"**{message['agent_name']}** - {format_time(message['timestamp'])}")
                    st.write(message["content"])
            else:
                st.info("No agent messages yet.")

        with memory_tab:
            st.markdown("#### Short-Term Memory")
            if detail.get("short_term_memory"):
                st.dataframe(
                    [
                        {"key": row["key"], "value": row["value"], "updated": format_time(row["updated_at"])}
                        for row in detail["short_term_memory"]
                    ],
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("Short-term memory will appear as agents run.")

            st.markdown("#### Long-Term Memory Retrieved")
            if detail.get("long_term_memory"):
                st.dataframe(
                    [
                        {
                            "category": row["category"],
                            "summary": row["summary"],
                            "source_run_id": row["source_run_id"],
                        }
                        for row in detail["long_term_memory"]
                    ],
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("No reusable long-term memory stored yet.")

            st.markdown("#### Context Sent To Agents")
            contexts = detail.get("contexts") or []
            if contexts:
                labels = {
                    row["id"]: f"{row['agent_name']} - {format_time(row['timestamp'])}"
                    for row in contexts
                }
                selected_context_id = st.selectbox(
                    "Context snapshot",
                    [row["id"] for row in contexts],
                    format_func=lambda context_id: labels[context_id],
                )
                selected_context = next(row for row in contexts if row["id"] == selected_context_id)
                st.code(selected_context["payload_json"], language="json")
            else:
                st.info("Context snapshots will appear before each agent call.")

        with eval_tab:
            evaluations = detail.get("evaluations") or []
            if evaluations:
                st.dataframe(
                    [
                        {
                            "time": format_time(row["timestamp"]),
                            "correctness": row["correctness"],
                            "completeness": row["completeness"],
                            "code_quality": row["code_quality"],
                            "passed": row["passed"],
                            "summary": row["summary"],
                        }
                        for row in evaluations
                    ],
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("Evaluation scores appear after the Tester Agent runs.")

        with os_tab:
            if os_capabilities:
                control_loop = os_capabilities.get("control_loop", {})
                st.markdown("#### Control Loop Policy")
                st.json(control_loop)

                st.markdown("#### Agent Catalog")
                st.dataframe(
                    [
                        {
                            "agent": agent.get("name"),
                            "implemented": agent.get("implemented"),
                            "parallel_safe": agent.get("parallel_safe"),
                            "skills": ", ".join(agent.get("default_skills", [])),
                            "tools": ", ".join(agent.get("allowed_tools", [])),
                        }
                        for agent in os_capabilities.get("agents", [])
                    ],
                    width="stretch",
                    hide_index=True,
                )

                st.markdown("#### Tool Permissions")
                st.dataframe(
                    [
                        {
                            "tool": tool.get("name"),
                            "risk": tool.get("risk"),
                            "approval": tool.get("requires_approval"),
                            "timeout": tool.get("timeout_seconds"),
                            "mcp": tool.get("mcp_compatible"),
                        }
                        for tool in os_capabilities.get("tools", [])
                    ],
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.info("Agentic OS capabilities are unavailable.")

        if detail.get("error"):
            st.error(detail["error"])

        if detail["status"] == "running":
            time.sleep(2)
            st.rerun()
