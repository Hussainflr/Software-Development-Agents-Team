# Code Patterns: Old vs New

Quick reference for common patterns when using the new LangChain-based architecture.

## 1. Initializing Agents

### ❌ Old Pattern
```python
from agents.backend_agent import BackendAgent
from llm_providers.litellm_client import LiteLLMClient

agent = BackendAgent()
llm = LiteLLMClient("gpt-4-turbo")
context = AgentContext(
    run_id=1,
    requirement="Build API",
    artifacts={},
    messages=[],
)
result = agent.execute(context, llm)
```

### ✅ New Pattern
```python
from agents.langchain_agents import BackendAgent
from state_management import AgentExecutionContext

agent = BackendAgent()  # LLM auto-configured
context = AgentExecutionContext(
    run_id=1,
    execution_id="uuid",
    agent_name="Backend",
    requirement="Build API",
    artifacts={},
    messages=[],
)
result = agent.execute(context)
```

**Benefits**: Simpler initialization, auto-configured LLM, type-safe context

---

## 2. Logging

### ❌ Old Pattern
```python
print(f"Agent {agent.name} completed with {len(artifacts)} artifacts")
logger.info(f"Stage: {stage}, Duration: {duration}s")
```

### ✅ New Pattern
```python
from logging_config import get_logger

logger = get_logger(__name__)
logger.info(
    "agent_completed",
    agent=agent.name,
    artifact_count=len(artifacts),
    duration=duration,
)
```

**Benefits**: Structured logs, JSON output, context binding, better analysis

---

## 3. Error Handling

### ❌ Old Pattern
```python
try:
    result = agent.execute(context)
except Exception as e:
    print(f"Error: {e}")
    # Manual recovery
```

### ✅ New Pattern
```python
from error_handling import (
    get_error_recovery,
    get_error_tracker,
    AgentException,
)

try:
    result = agent.execute(context)
except AgentException as e:
    recovery = get_error_recovery().handle(e)
    tracker = get_error_tracker()
    tracker.track_error(e, {"stage": "backend"})
    logger.error("agent_failed", error=str(e))
```

**Benefits**: Structured exceptions, automatic recovery, error tracking

---

## 4. State Management

### ❌ Old Pattern
```python
state = {
    "run_id": 1,
    "requirement": "...",
    "artifacts": {},
    "messages": [],
    "bugs_found": False,
}
# Weak typing, no IDE support
state["typo"] = value  # Would be caught at runtime
```

### ✅ New Pattern
```python
from state_management import WorkflowState, init_workflow_state

state: WorkflowState = init_workflow_state(
    run_id=1,
    execution_id="uuid",
    requirement="...",
)
# Strong typing, IDE support
state["artifacts"]["path"] = content  # IDE knows all fields
# state["typo"] = value  # IDE catches typo immediately
```

**Benefits**: Type safety, IDE autocomplete, catch errors early

---

## 5. Configuration

### ❌ Old Pattern
```python
import os

provider = os.getenv("LLM_PROVIDER", "gpt-4")
model = os.getenv("LLM_MODEL", "gpt-4")
temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
# Manual defaults and type conversion
```

### ✅ New Pattern
```python
from config import get_config

config = get_config()
provider = config.llm.provider  # From environment, type-validated
model = config.llm.model
temperature = config.llm.temperature
# Automatic defaults and validation
```

**Benefits**: Hierarchical config, validation, type safety, easy overrides

---

## 6. Workflow Execution

### ❌ Old Pattern
```python
from workflows.software_team_graph import SoftwareTeamWorkflow

workflow = SoftwareTeamWorkflow(repository)
state = {
    "run_id": 1,
    "requirement": "...",
    "provider": "gpt-4",
    "model": "gpt-4",
    "artifacts": {},
    "messages": [],
    "bug_report": "",
    "bugs_found": False,
    "revision_count": 0,
}
final_state = workflow.initial_graph.invoke(state)
# Manual state management
```

### ✅ New Pattern
```python
from workflow_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
report = orchestrator.run_development_workflow(
    run_id=1,
    requirement="...",
    provider="gpt-4-turbo",
)
# Automatic state management and execution
print(report.status)  # "completed" or "failed"
print(report.stages_executed)
print(report.agent_results)
```

**Benefits**: Simpler interface, comprehensive reporting, better error handling

---

## 7. Tool Definition

### ❌ Old Pattern
```python
# No formal tool definition
# Tools passed as description strings to LLM
```

### ✅ New Pattern
```python
from langchain_core.tools import tool

@tool
def generate_code(requirement: str, language: str) -> str:
    """
    Generate code for the given requirement.
    
    Args:
        requirement: What to build
        language: Programming language
        
    Returns:
        Generated code
    """
    return f"# Code for {requirement} in {language}"

# Tools auto-discover schema and type hints
```

**Benefits**: Type-safe tools, auto schema generation, LLM-aware tools

---

## 8. Result Processing

### ❌ Old Pattern
```python
raw_response = agent.execute(context, llm)
try:
    parsed = json.loads(raw_response)
except ValueError:
    # Fallback to manual parsing
    parsed = parse_agent_json(raw_response)
# Manual result handling
```

### ✅ New Pattern
```python
from state_management import AgentExecutionResult

result: AgentExecutionResult = agent.execute(context)
if result.success:
    artifacts = result.artifacts
    bugs = result.bugs
    summary = result.summary
else:
    errors = result.errors
    # Structured result handling
```

**Benefits**: Type-safe results, structured error info, automatic parsing

---

## 9. Retry Logic

### ❌ Old Pattern
```python
def retry_operation(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

retry_operation(lambda: agent.execute(context))
```

### ✅ New Pattern
```python
from error_handling import with_retry

@with_retry(
    max_attempts=3,
    backoff_factor=2.0,
    recoverable_exceptions=(TimeoutError, RetryableError),
)
def execute_agent():
    return agent.execute(context)

result = execute_agent()
```

**Benefits**: Declarative, type-safe, automatic backoff

---

## 10. Monitoring

### ❌ Old Pattern
```python
# Manual metrics collection
start_time = time.time()
try:
    result = agent.execute(context)
    duration = time.time() - start_time
    print(f"Success: {duration}s")
except Exception:
    print("Failed")
```

### ✅ New Pattern
```python
from error_handling import get_error_tracker

result = agent.execute(context)  # Duration auto-tracked
tracker = get_error_tracker()
summary = tracker.get_summary()

metrics = {
    "execution_time": result.execution_time_seconds,
    "success": result.success,
    "artifact_count": len(result.artifacts),
    "errors": len(result.errors),
    "total_errors_tracked": summary["total_errors"],
}
```

**Benefits**: Automatic metrics, comprehensive tracking, easy analysis

---

## 11. Context Management

### ❌ Old Pattern
```python
logger.info(f"Processing run {run_id} with agent {agent_name}")
# Manual context in every log
result = agent.execute(context)
logger.info(f"Completed run {run_id} with agent {agent_name}")
```

### ✅ New Pattern
```python
from logging_config import LogContext

with LogContext(run_id=run_id, agent=agent_name):
    logger.info("processing")  # Auto includes context
    result = agent.execute(context)
    logger.info("completed")  # Auto includes context
# Output: {"event": "processing", "run_id": run_id, "agent": agent_name}
```

**Benefits**: Less repetition, automatic context propagation, cleaner code

---

## 12. Multi-Agent Workflows

### ❌ Old Pattern
```python
state = init_state()
state = backend_agent.execute(state)
if not state["failed"]:
    state = frontend_agent.execute(state)
if not state["failed"]:
    state = tester_agent.execute(state)
# Manual workflow coordination
```

### ✅ New Pattern
```python
orchestrator = get_orchestrator()
report = orchestrator.run_development_workflow(
    run_id=1,
    requirement="...",
)
# Automatic workflow, error handling, state management
for agent_name, result in report.agent_results.items():
    print(f"{agent_name}: {result.success}")
```

**Benefits**: Automatic coordination, error recovery, comprehensive reporting

---

## 13. Database Integration

### ❌ Old Pattern
```python
# Manual database updates
repo.update_run(run_id, status="running")
repo.add_log(run_id, agent_name, "event", message)
# Manual synchronization
```

### ✅ New Pattern
```python
# Automatic database updates through orchestrator
report = orchestrator.run_development_workflow(...)
# All updates handled automatically
# Manual access still available
repo.get_run(run_id)
repo.list_files(run_id)
```

**Benefits**: Automatic persistence, less boilerplate, transactional updates

---

## 14. Testing

### ❌ Old Pattern
```python
def test_agent():
    agent = BackendAgent()
    llm = MockLLM()
    context = AgentContext(...)
    result = agent.execute(context, llm)
    assert result.success
```

### ✅ New Pattern
```python
def test_agent():
    agent = BackendAgent()
    # LLM is mocked automatically via config
    context = AgentExecutionContext(...)
    result = agent.execute(context)
    assert isinstance(result, AgentExecutionResult)
    assert result.success or result.errors
```

**Benefits**: Cleaner tests, type safety, fixture support

---

## 15. Custom Agents

### ❌ Old Pattern
```python
class CustomAgent(BaseAgent):
    name = "Custom"
    role = "Custom Role"
    
    def task_instructions(self) -> str:
        return "Do something"
    
    def fallback_output(self, context, response) -> AgentResult:
        return AgentResult(...)
```

### ✅ New Pattern
```python
class CustomAgent(BaseProductionAgent):
    name = "Custom"
    role = "Custom Role"
    tools = get_all_tools()
    
    def _role_description(self) -> str:
        return "Your role and responsibilities"
    
    def _build_task_prompt(self, context) -> str:
        return "Your task prompt"
```

**Benefits**: Better structure, tool integration, less boilerplate

---

## Comparison Table

| Aspect | Old | New |
|--------|-----|-----|
| **Type Safety** | Weak (dicts) | Strong (TypedDict) |
| **Error Handling** | Basic try-catch | Structured + recovery |
| **Logging** | Print statements | Structured JSON logs |
| **Configuration** | Manual env vars | Pydantic validation |
| **Tools** | String descriptions | LangChain tools |
| **Retry Logic** | Manual code | Decorator |
| **Monitoring** | Manual tracking | Automatic metrics |
| **State Management** | Dict passing | TypedDict + helpers |
| **Workflow** | Manual coordination | Orchestrator |
| **Database** | Manual sync | Automatic persistence |

---

## Migration Checklist

- [ ] Install new dependencies
- [ ] Update imports to use new modules
- [ ] Replace agent initialization
- [ ] Update logging calls
- [ ] Update error handling
- [ ] Replace state initialization
- [ ] Update workflow calls
- [ ] Test with example
- [ ] Verify logs and metrics
- [ ] Deploy to production

---

## Quick Reference

```python
# Import essentials
from config import get_config
from logging_config import setup_logging, get_logger
from workflow_orchestrator import get_orchestrator
from state_management import AgentExecutionContext, init_workflow_state
from error_handling import get_error_recovery, with_retry
from agents.langchain_agents import BackendAgent, FrontendAgent, TesterAgent

# Setup
setup_logging()
config = get_config()
logger = get_logger(__name__)

# Run workflow
orchestrator = get_orchestrator()
report = orchestrator.run_development_workflow(run_id=1, requirement="...")

# Check results
print(f"Status: {report.status}")
print(f"Stages: {report.stages_executed}")
for agent, result in report.agent_results.items():
    print(f"{agent}: {result.success}")
```

---

**Happy coding with the new production-ready LangChain architecture! 🚀**
