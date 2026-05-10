# LangChain Production-Ready Agentic Application

## Overview

This is a complete refactoring of the Software Development Agents Team to use **LangChain** as the core agentic framework with production-ready best practices.

## Architecture

### Core Components

```
config.py                      # Configuration management (12-factor app)
logging_config.py              # Structured logging with structlog
llm_provider_langchain.py       # LangChain-compatible LLM wrapper
error_handling.py               # Error handling and recovery strategies
state_management.py             # Type-safe state management (TypedDict)
agents/langchain_agents.py      # Production-ready LangChain agents
workflow_orchestrator.py        # LCEL-based workflow coordination
tools/langchain_tools.py        # Structured tool definitions
```

### Key Design Principles

1. **Type Safety**: Full type hints with Pydantic and TypedDict
2. **Error Handling**: Structured exceptions with recovery strategies
3. **Logging**: Context-aware structured logging via structlog
4. **Modularity**: Clear separation of concerns
5. **Testability**: Dependency injection and composable runnables
6. **Monitoring**: Comprehensive error tracking and metrics
7. **Persistence**: Database integration for audit trails
8. **Configuration**: Environment-based config (12-factor app)

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your LLM provider credentials
```

### Basic Usage

```python
from workflow_orchestrator import get_orchestrator
from config import get_config
from logging_config import setup_logging

# Initialize logging
setup_logging()

# Get orchestrator
orchestrator = get_orchestrator()

# Run development workflow
report = orchestrator.run_development_workflow(
    run_id=1,
    requirement="Build a task management API with React frontend",
    provider="gpt-4-turbo",
)

print(f"Status: {report.status}")
print(f"Duration: {report.total_duration_seconds}s")
print(f"Stages: {report.stages_executed}")
```

## Configuration

### Environment Variables

```bash
# LLM Configuration
LLM__PROVIDER=gpt-4-turbo      # or: anthropic, ollama, litellm
LLM__MODEL=gpt-4-turbo
LLM__TEMPERATURE=0.2
LLM__MAX_TOKENS=2000
LLM__TIMEOUT_SECONDS=60
LLM__RETRY_COUNT=3

# Database Configuration
DATABASE__URL=sqlite:///./agent_team.db
DATABASE__ECHO=false
DATABASE__POOL_SIZE=10

# Logging Configuration
LOGGING__LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGGING__FORMAT=json            # json or text
LOGGING__INCLUDE_TIMESTAMPS=true

# App Configuration
APP__ENVIRONMENT=production     # development, staging, production
APP__DEBUG=false
```

## Agents

### BaseProductionAgent

All agents inherit from `BaseProductionAgent` and provide:

- **Tool Integration**: Automatic tool binding via LangChain
- **ReAct Pattern**: Reason-Act-Observe pattern for complex tasks
- **Error Handling**: Built-in retry logic and fallbacks
- **Output Parsing**: Structured JSON parsing with validation
- **Logging**: Comprehensive execution logging

### Available Agents

#### BackendAgent
- Designs and implements backend architecture
- Creates API routes and database schemas
- Generates FastAPI code with SQLAlchemy ORM

#### FrontendAgent
- Designs responsive UI components
- Implements React/TypeScript code
- Ensures accessibility (WCAG 2.1)

#### TesterAgent
- Analyzes code for bugs and issues
- Designs comprehensive test strategies
- Generates unit and integration tests

#### DeploymentAgent
- Creates Docker containers
- Generates deployment scripts
- Sets up environment configuration

### Creating Custom Agents

```python
from agents.langchain_agents import BaseProductionAgent
from tools.langchain_tools import get_all_tools

class CustomAgent(BaseProductionAgent):
    name = "Custom Agent"
    role = "Domain Expert"
    tools = get_all_tools()
    
    def _role_description(self) -> str:
        return "Your specific role and responsibilities"
    
    def _build_task_prompt(self, context) -> str:
        return f"""
        Your task:
        {context.requirement}
        
        Existing artifacts: {list(context.artifacts.keys())}
        """
```

## State Management

### WorkflowState

Type-safe state object passed through workflow:

```python
from state_management import WorkflowState, init_workflow_state

state = init_workflow_state(
    run_id=1,
    execution_id="uuid-here",
    requirement="Build a REST API",
    llm_provider="gpt-4-turbo",
)

# Strongly typed access
state["artifacts"]["backend/main.py"] = "..."
state["messages"].append("Backend Agent: Done")
state["bugs_found"].extend(["bug1", "bug2"])
```

### AgentExecutionContext

Context provided to each agent:

```python
from state_management import AgentExecutionContext

context = AgentExecutionContext(
    run_id=1,
    execution_id="uuid",
    agent_name="Backend Agent",
    requirement="Build API",
    artifacts={},
    messages=[],
    revision=False,
)
```

### AgentExecutionResult

Structured result from agent execution:

```python
from state_management import AgentExecutionResult

result = AgentExecutionResult(
    agent_name="Backend Agent",
    success=True,
    summary="Created FastAPI backend with 3 endpoints",
    artifacts={"backend/main.py": "...code..."},
    bugs=[],
    execution_time_seconds=45.2,
)
```

## Tools

### Defining Tools

```python
from langchain_core.tools import tool

@tool
def my_tool(input_param: str) -> str:
    """
    Tool description for LLM.
    
    Args:
        input_param: Description
        
    Returns:
        Result
    """
    return "result"

# Tools are auto-discovered by LangChain's schema
```

### Tool Collections

```python
from tools.langchain_tools import (
    get_backend_tools,
    get_frontend_tools,
    get_tester_tools,
    get_all_tools,
)

# Each agent gets appropriate tools
backend_agent.tools = get_backend_tools()
frontend_agent.tools = get_frontend_tools()
```

## Error Handling

### Exception Types

```python
from error_handling import (
    AgentException,
    ToolExecutionError,
    ParsingError,
    ValidationError,
    RetryableError,
)

# Usage
try:
    agent.execute(context)
except ParsingError as e:
    recovery_action = get_error_recovery().handle(e)
    print(recovery_action["recommendation"])
```

### Retry Decorator

```python
from error_handling import with_retry

@with_retry(
    max_attempts=3,
    backoff_factor=2.0,
    recoverable_exceptions=(RetryableError, TimeoutError),
)
def risky_operation():
    pass
```

### Error Recovery

```python
from error_handling import get_error_recovery, get_error_tracker

recovery = get_error_recovery()
tracker = get_error_tracker()

try:
    operation()
except Exception as e:
    action = recovery.handle(e, context={"stage": "backend"})
    tracker.track_error(e, {"stage": "backend"})
    
    summary = tracker.get_summary()
    print(f"Total errors: {summary['total_errors']}")
```

## Logging

### Setup

```python
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

logger.info("workflow_started", run_id=1, requirement_length=100)
```

### Log Context

```python
from logging_config import LogContext

with LogContext(run_id=1, agent="backend"):
    logger.info("processing")  # Includes run_id and agent in log
```

### Log Output

```json
{
  "event": "workflow_started",
  "run_id": 1,
  "requirement_length": 100,
  "timestamp": "2024-05-10T10:30:00",
  "level": "info"
}
```

## Workflow Orchestration

### Development Workflow

```python
from workflow_orchestrator import get_orchestrator

orchestrator = get_orchestrator()

report = orchestrator.run_development_workflow(
    run_id=1,
    requirement="Build a task management system",
    provider="gpt-4-turbo",
)

# Analyze results
print(f"Status: {report.status}")
print(f"Stages: {report.stages_executed}")
print(f"Duration: {report.total_duration_seconds}s")

for agent_name, result in report.agent_results.items():
    print(f"\n{agent_name}:")
    print(f"  Success: {result.success}")
    print(f"  Artifacts: {len(result.artifacts)}")
    print(f"  Time: {result.execution_time_seconds}s")
```

### Deployment Workflow

```python
report = orchestrator.run_deployment_workflow(run_id=1)

print(f"Deployment status: {report.status}")
print(f"Artifacts: {list(report.final_artifacts.keys())}")
```

## Database Persistence

### Repository Integration

```python
from database.repository import Repository

repo = Repository()

# Save run
run = repo.create_run(
    requirement="Build API",
    provider="gpt-4-turbo",
    model="gpt-4",
)

# Update progress
repo.update_run(run.id, status="running", current_stage="backend")

# Store artifacts
repo.upsert_file(run.id, "backend/main.py", code_content, agent="backend")

# Add logs
repo.add_log(
    run.id,
    agent_name="backend",
    event="completed",
    message="Backend code generated",
    status="success",
)
```

## Monitoring and Metrics

### Error Tracking

```python
from error_handling import get_error_tracker

tracker = get_error_tracker()
summary = tracker.get_summary()

print(f"Total errors: {summary['total_errors']}")
print(f"Error types: {summary['unique_error_types']}")
print(f"Counts: {summary['error_counts']}")
print(f"Recent: {summary['recent_errors']}")
```

### Workflow Metrics

```python
report = orchestrator.run_development_workflow(...)

metrics = {
    "success_rate": 1.0 if report.status == "completed" else 0.0,
    "total_duration": report.total_duration_seconds,
    "stages_completed": len(report.stages_executed),
    "artifacts_generated": len(report.final_artifacts),
    "errors": len(report.errors_encountered),
}
```

## Testing

### Unit Testing

```python
import pytest
from state_management import init_workflow_state
from agents.langchain_agents import BackendAgent

def test_backend_agent():
    agent = BackendAgent()
    context = AgentExecutionContext(
        run_id=1,
        execution_id="test",
        agent_name="Backend",
        requirement="Simple API",
        artifacts={},
        messages=[],
    )
    
    result = agent.execute(context)
    assert result.success
    assert len(result.artifacts) > 0
```

### Integration Testing

```python
def test_workflow():
    orchestrator = get_orchestrator()
    report = orchestrator.run_development_workflow(
        run_id=1,
        requirement="Test requirement",
    )
    
    assert report.status in ["completed", "failed"]
    assert len(report.stages_executed) > 0
```

## Best Practices

### 1. Always Use Configuration

```python
# Good
config = get_config()
llm = get_llm(config)

# Avoid
llm = get_llm()  # Uses global config
```

### 2. Structured Logging

```python
# Good
logger.info("stage_completed", stage="backend", duration=45.2, artifacts=3)

# Avoid
logger.info(f"Stage backend completed in 45.2s with 3 artifacts")
```

### 3. Type Hints

```python
# Good
def process(state: WorkflowState) -> AgentExecutionResult:
    pass

# Avoid
def process(state, context):
    pass
```

### 4. Error Handling

```python
# Good
try:
    result = agent.execute(context)
except AgentException as e:
    recovery = get_error_recovery().handle(e)
    logger.error("agent_failed", error=str(e), recovery=recovery)

# Avoid
try:
    result = agent.execute(context)
except Exception:
    pass
```

### 5. Context Management

```python
# Good
with LogContext(run_id=run.id, agent=agent_name):
    result = agent.execute(context)

# Avoid
result = agent.execute(context)
logger.info(f"Agent {agent_name} for run {run.id} completed")
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DATABASE__URL=postgresql://user:pass@db:5432/agents
ENV LLM__PROVIDER=gpt-4-turbo

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Environment Setup

```bash
# Production
export LLM__PROVIDER=gpt-4-turbo
export LLM__MODEL=gpt-4
export LOGGING__LEVEL=INFO
export APP__ENVIRONMENT=production

# Development
export APP__ENVIRONMENT=development
export LOGGING__LEVEL=DEBUG
export LLM__MODEL=gpt-3.5-turbo  # Cheaper for testing
```

## Troubleshooting

### Common Issues

**LLM Call Fails**
- Check API keys in environment
- Verify provider credentials
- Check rate limits and quota

**Database Issues**
- Ensure database URL is correct
- Check database permissions
- Verify SQLAlchemy compatibility

**Parsing Errors**
- Check LLM response format
- Verify prompt engineering
- Use fuzzy matching for robustness

### Debug Mode

```bash
export LOGGING__LEVEL=DEBUG
export APP__DEBUG=true
```

## Contributing

1. Follow the established patterns
2. Add type hints to all functions
3. Write structured logs for debugging
4. Test error cases
5. Document new features

## License

MIT
