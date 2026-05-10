# Dockerfile Generation

Generate local deployment artifacts for the generated project.

Rules:
- Include Dockerfile and Docker Compose artifacts when deployment is requested.
- Keep ports explicit and documented.
- Prefer local-first commands that run on a developer machine.
- Include a short deployment README with setup and troubleshooting notes.

