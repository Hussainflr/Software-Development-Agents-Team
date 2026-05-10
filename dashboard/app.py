import os
import json
import time
from datetime import datetime

import requests
import streamlit as st


API_URL = os.getenv("MISSION_CONTROL_API_URL", "http://localhost:8000").rstrip("/")
AGENT_ORDER = ["Backend Agent", "Frontend Agent", "Tester Agent", "Deployment Agent"]
STAGES = ["Requirement", "Backend", "Frontend", "Testing", "Deployment"]
STAGE_PROGRESS = {
    "requirement": 5,
    "backend": 20,
    "backend_revision": 35,
    "frontend": 45,
    "frontend_revision": 60,
    "testing": 75,
    "deployment_approval": 85,
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
      .block-container { padding-top: 1.4rem; max-width: 1280px; }
      .agent-card {
        border: 1px solid #d5dbe3;
        border-radius: 8px;
        padding: 0.85rem;
        background: #fbfcfe;
        min-height: 108px;
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
      .status-dot { width: 0.65rem; height: 0.65rem; border-radius: 999px; display: inline-block; }
      .stage-row {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.5rem;
        margin: 0.4rem 0 1rem 0;
      }
      .stage {
        border: 1px solid #d5dbe3;
        border-radius: 8px;
        padding: 0.6rem;
        text-align: center;
        font-size: 0.86rem;
        background: #ffffff;
      }
      .stage.active { border-color: #2563eb; background: #eff6ff; color: #1d4ed8; font-weight: 700; }
      .stage.done { border-color: #047857; background: #ecfdf5; color: #047857; font-weight: 700; }
      .small-muted { color: #6b7280; font-size: 0.85rem; }
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
    return data


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


def status_card(agent_name: str, status: str) -> str:
    color = STATUS_COLORS.get(status, "#6b7280")
    role = {
        "Backend Agent": "APIs and data model",
        "Frontend Agent": "UI and API integration",
        "Tester Agent": "Tests and review",
        "Deployment Agent": "Docker and local deploy",
    }.get(agent_name, "Agent")
    return f"""
    <div class="agent-card">
      <div class="agent-name">{agent_name}</div>
      <div class="agent-role">{role}</div>
      <div class="agent-status">
        <span class="status-dot" style="background:{color}"></span>
        {status}
      </div>
    </div>
    """


def progress_html(run: dict, statuses: dict[str, str]) -> str:
    current = run.get("current_stage", "requirement")
    completed = {
        "Requirement": True,
        "Backend": statuses.get("Backend Agent") == "completed",
        "Frontend": statuses.get("Frontend Agent") == "completed",
        "Testing": statuses.get("Tester Agent") == "completed",
        "Deployment": statuses.get("Deployment Agent") == "completed",
    }
    active_map = {
        "backend": "Backend",
        "backend_revision": "Backend",
        "frontend": "Frontend",
        "frontend_revision": "Frontend",
        "testing": "Testing",
        "deployment": "Deployment",
        "deployment_approval": "Deployment",
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
        "backend": "Backend Agent running",
        "backend_revision": "Backend revision running",
        "frontend": "Frontend Agent running",
        "frontend_revision": "Frontend revision running",
        "testing": "Tester Agent running",
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
provider_options = providers["options"]
provider_ids = [item["id"] for item in provider_options]
provider_labels = {item["id"]: item["label"] for item in provider_options}
default_provider = providers.get("default_provider", "ollama")
ollama_running = bool(providers.get("ollama_running"))
ollama_models = providers.get("ollama_models", [])
detected_ollama_model = providers.get("detected_model")
model_recommendations = providers.get("model_recommendations", [])

st.title("Mission Control")
st.caption("Human-managed AI software team running locally first with Ollama.")

with st.sidebar:
    st.header("LLM Provider")
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
    st.header("Local Commands")
    st.code("ollama serve\nollama pull qwen2.5-coder\nuvicorn app.main:app --reload\nstreamlit run dashboard/app.py")

if "current_run_id" not in st.session_state:
    st.session_state.current_run_id = None

recent_runs = api_request("GET", "/api/runs", params={"limit": 20}) or []

left, right = st.columns([1.05, 0.95])
with left:
    st.subheader("Manager Requirement")
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
    st.subheader("Recent Runs")
    if recent_runs:
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
        st.subheader(f"Run {detail['id']} Control")
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
        st.progress(progress_value, text=f"{progress_label} - {progress_value}%")
        st.markdown(progress_html(detail, statuses), unsafe_allow_html=True)

        agent_cols = st.columns(4)
        for index, agent_name in enumerate(AGENT_ORDER):
            with agent_cols[index]:
                st.markdown(status_card(agent_name, statuses.get(agent_name, "idle")), unsafe_allow_html=True)

        log_tab, file_tab, message_tab, memory_tab, eval_tab = st.tabs(
            ["Live Activity Log", "Generated Files", "Agent Messages", "Memory & Context", "Evaluation"]
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

        if detail.get("error"):
            st.error(detail["error"])

        if detail["status"] == "running":
            time.sleep(2)
            st.rerun()
