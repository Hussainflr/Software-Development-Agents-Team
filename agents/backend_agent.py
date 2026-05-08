from textwrap import dedent

from agents.base import AgentContext, AgentResult, BaseAgent


class BackendAgent(BaseAgent):
    name = "Backend Agent"
    role = "Backend Architect"

    def task_instructions(self) -> str:
        return (
            "Design the backend architecture, API routes, and persistence model. "
            "Generate FastAPI backend code and include comments around non-obvious choices."
        )

    def fallback_output(self, context: AgentContext, raw_response: str) -> AgentResult:
        requirement = context.requirement.replace('"""', "'").strip()
        main_py = dedent(
            f'''
            from datetime import datetime
            from uuid import uuid4

            from fastapi import FastAPI, HTTPException
            from pydantic import BaseModel


            app = FastAPI(title="Generated Project API")

            # In the demo artifact we keep storage in memory. The Mission Control app
            # itself uses SQLite, so this generated backend can be replaced with a
            # real database-backed service when the requirement is finalized.
            REQUIREMENT = """{requirement}"""
            TASKS: dict[str, dict] = {{}}


            class TaskCreate(BaseModel):
                title: str
                description: str = ""


            class TaskUpdate(BaseModel):
                status: str


            @app.get("/health")
            def health() -> dict:
                return {{"status": "ok", "requirement": REQUIREMENT}}


            @app.post("/tasks")
            def create_task(payload: TaskCreate) -> dict:
                task_id = str(uuid4())
                task = {{
                    "id": task_id,
                    "title": payload.title,
                    "description": payload.description,
                    "status": "open",
                    "created_at": datetime.utcnow().isoformat(),
                }}
                TASKS[task_id] = task
                return task


            @app.get("/tasks")
            def list_tasks() -> list[dict]:
                return list(TASKS.values())


            @app.patch("/tasks/{{task_id}}")
            def update_task(task_id: str, payload: TaskUpdate) -> dict:
                if task_id not in TASKS:
                    raise HTTPException(status_code=404, detail="Task not found")
                TASKS[task_id]["status"] = payload.status
                return TASKS[task_id]
            '''
        ).strip()
        readme = dedent(
            f"""
            # Generated Backend Plan

            Requirement:
            {requirement}

            API surface:
            - `GET /health`
            - `POST /tasks`
            - `GET /tasks`
            - `PATCH /tasks/{{task_id}}`

            This fallback artifact was produced after the LLM returned non-JSON text.
            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentResult(
            summary="Created a FastAPI backend scaffold with health and task APIs.",
            artifacts={
                "generated_backend/main.py": main_py,
                "generated_backend/README.md": readme,
            },
            notes=["Fallback backend uses in-memory storage for the demo artifact."],
        )

