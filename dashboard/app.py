import os
import time
from datetime import datetime

import requests
import streamlit as st


API_URL = os.getenv("MISSION_CONTROL_API_URL", "http://localhost:8000").rstrip("/")
AGENT_ORDER = ["Backend Agent", "Frontend Agent", "Tester Agent", "Deployment Agent"]
STAGES = ["Requirement", "Backend", "Frontend", "Testing", "Deployment"]
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
            "options": [{"id": "ollama", "label": "Ollama", "default_model": "qwen2.5-coder"}],
        }
    return data


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
            "summary": row["output_summary"],
        }
        for row in reversed(logs[-80:])
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


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
    default_model = next((item["default_model"] for item in provider_options if item["id"] == provider), "qwen2.5-coder")
    model = st.text_input("Model", value=default_model)
    st.divider()
    st.header("Local Commands")
    st.code("ollama pull qwen2.5-coder\nollama serve\nuvicorn app.main:app --reload\nstreamlit run dashboard/app.py")

recent_runs = api_request("GET", "/api/runs", params={"limit": 20}) or []
if "current_run_id" not in st.session_state and recent_runs:
    st.session_state.current_run_id = recent_runs[0]["id"]

left, right = st.columns([1.05, 0.95])
with left:
    st.subheader("Manager Requirement")
    requirement = st.text_area(
        "What should the team build?",
        height=180,
        placeholder="Example: Build a small FastAPI task tracker with a Streamlit dashboard and Docker setup.",
    )
    if st.button("Start Run", type="primary", use_container_width=True):
        payload = {"requirement": requirement, "provider": provider, "model": model}
        if not requirement.strip():
            st.warning("Enter a software requirement first.")
        else:
            created = api_request("POST", "/api/runs", json=payload)
            if created:
                st.session_state.current_run_id = created["id"]
                st.rerun()

with right:
    st.subheader("Recent Runs")
    if recent_runs:
        labels = {run["id"]: f"Run {run['id']} - {run['status']} - {format_time(run['created_at'])}" for run in recent_runs}
        selected = st.selectbox(
            "Open run",
            [run["id"] for run in recent_runs],
            index=0,
            format_func=lambda run_id: labels[run_id],
        )
        if st.button("Open Selected Run", use_container_width=True):
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
                if st.button("Approve Deployment", type="primary", use_container_width=True):
                    api_request("POST", f"/api/runs/{run_id}/approve-deployment")
                    st.rerun()
        with control_cols[1]:
            if detail["status"] in {"running", "waiting_approval"}:
                if st.button("Stop Run", use_container_width=True):
                    api_request("POST", f"/api/runs/{run_id}/stop")
                    st.rerun()
        with control_cols[2]:
            if st.button("Restart Run", use_container_width=True):
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

        st.markdown(progress_html(detail, statuses), unsafe_allow_html=True)

        agent_cols = st.columns(4)
        for index, agent_name in enumerate(AGENT_ORDER):
            with agent_cols[index]:
                st.markdown(status_card(agent_name, statuses.get(agent_name, "idle")), unsafe_allow_html=True)

        log_tab, file_tab, message_tab = st.tabs(["Live Activity Log", "Generated Files", "Agent Messages"])
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

        if detail.get("error"):
            st.error(detail["error"])

        if detail["status"] == "running":
            time.sleep(2)
            st.rerun()

