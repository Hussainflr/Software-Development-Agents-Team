from textwrap import dedent

from agents.base import AgentContext, AgentResult, BaseAgent


class DeploymentAgent(BaseAgent):
    name = "Deployment Agent"
    role = "DevOps Engineer"

    def task_instructions(self) -> str:
        return (
            "Prepare Docker and local deployment artifacts for the generated project. "
            "Include a Dockerfile, docker-compose file, and local run instructions."
        )

    def fallback_output(self, context: AgentContext, raw_response: str) -> AgentResult:
        dockerfile = dedent(
            """
            FROM python:3.12-slim

            WORKDIR /app
            COPY generated_backend /app/generated_backend
            RUN pip install --no-cache-dir fastapi uvicorn pydantic

            EXPOSE 9000
            CMD ["uvicorn", "generated_backend.main:app", "--host", "0.0.0.0", "--port", "9000"]
            """
        ).strip()
        compose = dedent(
            """
            services:
              generated-backend:
                build:
                  context: .
                  dockerfile: deployment/Dockerfile.backend
                ports:
                  - "9000:9000"
              generated-frontend:
                image: python:3.12-slim
                working_dir: /app
                volumes:
                  - .:/app
                environment:
                  GENERATED_API_URL: http://generated-backend:9000
                command: >
                  sh -c "pip install --no-cache-dir streamlit requests &&
                         streamlit run generated_frontend/app.py --server.port 8502 --server.address 0.0.0.0"
                ports:
                  - "8502:8502"
                depends_on:
                  - generated-backend
            """
        ).strip()
        run_local = dedent(
            """
            #!/usr/bin/env bash
            set -euo pipefail

            uvicorn generated_backend.main:app --host 0.0.0.0 --port 9000 &
            BACKEND_PID=$!

            GENERATED_API_URL=http://localhost:9000 streamlit run generated_frontend/app.py --server.port 8502

            kill "$BACKEND_PID"
            """
        ).strip()
        instructions = dedent(
            f"""
            # Deployment Instructions

            Local:
            1. `cd generated_projects/run_<id>`
            2. `bash deployment/run_local.sh`

            Docker Compose:
            1. `cd generated_projects/run_<id>`
            2. `docker compose -f deployment/docker-compose.generated.yml up --build`

            Raw model summary:
            {raw_response[:1200]}
            """
        ).strip()
        return AgentResult(
            summary="Prepared Docker Compose and local run artifacts for deployment.",
            artifacts={
                "deployment/Dockerfile.backend": dockerfile,
                "deployment/docker-compose.generated.yml": compose,
                "deployment/run_local.sh": run_local,
                "deployment/DEPLOYMENT.md": instructions,
            },
            notes=["Deployment artifacts target the generated project folder for this run."],
        )

