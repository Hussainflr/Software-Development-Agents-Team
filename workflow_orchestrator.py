"""
Production-ready workflow orchestration using LCEL and LangChain patterns.

Implements multi-agent coordination with proper error handling, logging,
and state management.
"""

import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from langchain_core.runnables import Runnable, RunnableConfig

from agents.langchain_agents import (
    BackendAgent,
    DeploymentAgent,
    FrontendAgent,
    TesterAgent,
    get_agent,
)
from config import get_config
from database.repository import Repository
from error_handling import ErrorSeverity, get_error_recovery, get_error_tracker
from logging_config import LogContext, get_logger
from state_management import (
    WorkflowExecutionReport,
    WorkflowState,
    add_agent_output,
    init_workflow_state,
    AgentExecutionContext,
)
from tools.file_writer import write_artifacts

logger = get_logger(__name__)


class ProductionWorkflowOrchestrator:
    """
    Production-ready workflow orchestrator using LangChain patterns.
    
    Coordinates multi-agent workflows with:
    - Proper error handling and recovery
    - Comprehensive logging and monitoring
    - Database persistence
    - Artifact management
    - State machine transitions
    """

    def __init__(self, repository: Repository | None = None):
        """Initialize orchestrator."""
        self.repository = repository or Repository()
        self.config = get_config()
        self.error_recovery = get_error_recovery()
        self.error_tracker = get_error_tracker()

    def run_development_workflow(
        self, run_id: int, requirement: str, provider: str = "gpt-4-turbo"
    ) -> WorkflowExecutionReport:
        """
        Run complete development workflow: Backend → Frontend → Testing.
        
        Args:
            run_id: Unique run identifier
            requirement: User requirement to implement
            provider: LLM provider to use
            
        Returns:
            Comprehensive execution report
        """
        execution_id = str(uuid4())
        
        with LogContext(
            run_id=run_id,
            execution_id=execution_id,
            workflow="development",
        ):
            logger.info(
                "workflow_start",
                run_id=run_id,
                requirement_length=len(requirement),
            )

            start_time = datetime.utcnow()
            
            try:
                # Initialize workflow state
                state = init_workflow_state(
                    run_id=run_id,
                    execution_id=execution_id,
                    requirement=requirement,
                    llm_provider=provider,
                )

                # Execute agent pipeline
                stages_executed = []
                agent_results = {}

                # Backend stage
                logger.info("stage_start", stage="backend")
                backend_result = self._execute_agent_stage(
                    state=state,
                    agent_type="backend",
                    stage_name="backend",
                )
                state = add_agent_output(state, "Backend Agent", backend_result)
                agent_results["backend"] = backend_result
                stages_executed.append("backend")
                
                if backend_result.success:
                    # Frontend stage
                    logger.info("stage_start", stage="frontend")
                    frontend_result = self._execute_agent_stage(
                        state=state,
                        agent_type="frontend",
                        stage_name="frontend",
                    )
                    state = add_agent_output(state, "Frontend Agent", frontend_result)
                    agent_results["frontend"] = frontend_result
                    stages_executed.append("frontend")
                    
                    if frontend_result.success:
                        # Testing stage
                        logger.info("stage_start", stage="testing")
                        tester_result = self._execute_agent_stage(
                            state=state,
                            agent_type="tester",
                            stage_name="testing",
                        )
                        state = add_agent_output(state, "Tester Agent", tester_result)
                        agent_results["tester"] = tester_result
                        stages_executed.append("testing")

                # Update database with artifacts
                self.repository.update_run(
                    run_id,
                    status="waiting_approval",
                    current_stage="deployment_approval",
                )
                
                for path, content in state["artifacts"].items():
                    self.repository.upsert_file(run_id, path, content, "system")

                # Generate report
                total_duration = (datetime.utcnow() - start_time).total_seconds()
                report = WorkflowExecutionReport(
                    run_id=run_id,
                    execution_id=execution_id,
                    status="completed",
                    total_duration_seconds=total_duration,
                    stages_executed=stages_executed,
                    agent_results=agent_results,
                    final_artifacts=state["artifacts"],
                    errors_encountered=[],
                    revision_cycles=state.get("revision_count", 0),
                    total_tokens_used=0,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                )

                logger.info(
                    "workflow_completed",
                    run_id=run_id,
                    total_duration_seconds=total_duration,
                    stages=len(stages_executed),
                )

                return report

            except Exception as exc:
                logger.error("workflow_failed", error=str(exc), run_id=run_id)
                
                # Generate failure report
                recovery_action = self.error_recovery.handle(
                    exc, {"run_id": run_id, "stage": stages_executed[-1] if stages_executed else "initialization"}
                )
                
                return WorkflowExecutionReport(
                    run_id=run_id,
                    execution_id=execution_id,
                    status="failed",
                    total_duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    stages_executed=stages_executed,
                    agent_results=agent_results,
                    final_artifacts={},
                    errors_encountered=[{
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "recovery_action": recovery_action,
                    }],
                    revision_cycles=0,
                    total_tokens_used=0,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                )

    def run_deployment_workflow(
        self, run_id: int
    ) -> WorkflowExecutionReport:
        """
        Run deployment workflow to containerize and deploy.
        
        Args:
            run_id: Run to deploy
            
        Returns:
            Execution report
        """
        execution_id = str(uuid4())
        
        with LogContext(run_id=run_id, execution_id=execution_id, workflow="deployment"):
            logger.info("deployment_workflow_start", run_id=run_id)
            
            start_time = datetime.utcnow()
            
            try:
                # Load existing artifacts and state
                state = self._load_workflow_state(run_id)
                
                # Execute deployment
                logger.info("stage_start", stage="deployment")
                deployment_result = self._execute_agent_stage(
                    state=state,
                    agent_type="deployment",
                    stage_name="deployment",
                )
                
                agent_results = {"deployment": deployment_result}
                
                # Persist deployment artifacts
                for path, content in deployment_result.artifacts.items():
                    self.repository.upsert_file(run_id, path, content, "deployment")
                
                # Update database
                self.repository.update_run(
                    run_id,
                    status="completed",
                    current_stage="completed",
                    completed_at=datetime.utcnow(),
                )
                
                total_duration = (datetime.utcnow() - start_time).total_seconds()
                
                return WorkflowExecutionReport(
                    run_id=run_id,
                    execution_id=execution_id,
                    status="completed",
                    total_duration_seconds=total_duration,
                    stages_executed=["deployment"],
                    agent_results=agent_results,
                    final_artifacts=deployment_result.artifacts,
                    errors_encountered=[],
                    revision_cycles=0,
                    total_tokens_used=0,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                )
                
            except Exception as exc:
                logger.error("deployment_workflow_failed", error=str(exc), run_id=run_id)
                
                return WorkflowExecutionReport(
                    run_id=run_id,
                    execution_id=execution_id,
                    status="failed",
                    total_duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    stages_executed=["deployment"],
                    agent_results={},
                    final_artifacts={},
                    errors_encountered=[{
                        "type": type(exc).__name__,
                        "message": str(exc),
                    }],
                    revision_cycles=0,
                    total_tokens_used=0,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                )

    def _execute_agent_stage(
        self,
        state: WorkflowState,
        agent_type: str,
        stage_name: str,
    ) -> Any:
        """
        Execute a single agent stage.
        
        Args:
            state: Current workflow state
            agent_type: Type of agent to execute
            stage_name: Name of the stage for logging
            
        Returns:
            Agent execution result
        """
        try:
            # Create execution context
            context = AgentExecutionContext(
                run_id=state["run_id"],
                execution_id=state["execution_id"],
                agent_name=agent_type.title(),
                requirement=state["requirement"],
                artifacts=state["artifacts"],
                messages=state["messages"],
                bug_report=state.get("bug_report", ""),
                revision_count=state.get("revision_count", 0),
            )
            
            # Execute agent
            agent = get_agent(agent_type)
            result = agent.execute(context)
            
            logger.info(
                "agent_stage_completed",
                stage=stage_name,
                agent=agent_type,
                success=result.success,
                artifact_count=len(result.artifacts),
            )
            
            return result
            
        except Exception as exc:
            logger.error(
                "agent_stage_failed",
                stage=stage_name,
                agent=agent_type,
                error=str(exc),
            )
            self.error_tracker.track_error(exc, {"stage": stage_name, "agent": agent_type})
            raise

    def _load_workflow_state(self, run_id: int) -> WorkflowState:
        """Load workflow state from database."""
        run = self.repository.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        artifacts = {
            file.path: file.content for file in self.repository.list_files(run_id)
        }
        
        return init_workflow_state(
            run_id=run.id,
            execution_id=str(uuid4()),
            requirement=run.requirement,
            artifacts=artifacts,
        )


# Global orchestrator instance
_orchestrator: ProductionWorkflowOrchestrator | None = None


def get_orchestrator() -> ProductionWorkflowOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ProductionWorkflowOrchestrator()
    return _orchestrator
