#!/usr/bin/env python
"""
Production-ready example: Running the software development agents workflow.

This script demonstrates best practices for using the LangChain-based
multi-agent system in a production setting.
"""

import sys
from typing import Any

from config import get_config, set_config, AppConfig
from database.repository import Repository
from error_handling import get_error_tracker
from logging_config import LogContext, get_logger, setup_logging
from state_management import WorkflowExecutionReport
from workflow_orchestrator import ProductionWorkflowOrchestrator

# Initialize logging first
setup_logging()
logger = get_logger(__name__)


def configure_environment() -> AppConfig:
    """Load and validate configuration from environment."""
    config = get_config()
    
    logger.info(
        "configuration_loaded",
        environment=config.environment,
        app_name=config.app_name,
        version=config.version,
    )
    
    return config


def run_example(
    requirement: str,
    run_id: int | None = None,
    provider: str = "gpt-4-turbo",
    enable_deployment: bool = False,
) -> tuple[WorkflowExecutionReport, Any]:
    """
    Run the complete development workflow example.
    
    Args:
        requirement: What to build
        run_id: Database run ID (auto-generated if None)
        provider: LLM provider to use
        enable_deployment: Whether to run deployment after development
        
    Returns:
        Tuple of (development report, deployment report or None)
    """
    config = get_config()
    repository = Repository()
    orchestrator = ProductionWorkflowOrchestrator(repository)
    
    # Create or use provided run ID
    if run_id is None:
        run = repository.create_run(
            requirement=requirement,
            provider=provider,
            model="gpt-4-turbo",
        )
        run_id = run.id
    
    logger.info(
        "example_start",
        run_id=run_id,
        requirement=requirement[:100],
    )
    
    # Execute development workflow
    with LogContext(
        run_id=run_id,
        workflow="development",
        provider=provider,
    ):
        logger.info("running_development_workflow")
        
        dev_report = orchestrator.run_development_workflow(
            run_id=run_id,
            requirement=requirement,
            provider=provider,
        )
        
        # Print development results
        print_workflow_report(dev_report, "Development")
    
    # Optionally run deployment
    deployment_report = None
    if enable_deployment and dev_report.status == "completed":
        with LogContext(run_id=run_id, workflow="deployment"):
            logger.info("running_deployment_workflow")
            
            deployment_report = orchestrator.run_deployment_workflow(run_id)
            print_workflow_report(deployment_report, "Deployment")
    
    return dev_report, deployment_report


def print_workflow_report(report: WorkflowExecutionReport, workflow_name: str) -> None:
    """Pretty print workflow execution report."""
    print("\n" + "=" * 80)
    print(f"{workflow_name} Workflow Report".center(80))
    print("=" * 80)
    
    print(f"\nRun ID: {report.run_id}")
    print(f"Execution ID: {report.execution_id}")
    print(f"Status: {report.status}")
    print(f"Total Duration: {report.total_duration_seconds:.2f}s")
    
    print(f"\nStages Executed: {', '.join(report.stages_executed)}")
    print(f"Total Artifacts: {len(report.final_artifacts)}")
    print(f"Errors Encountered: {len(report.errors_encountered)}")
    
    if report.agent_results:
        print("\nAgent Results:")
        print("-" * 80)
        for agent_name, result in report.agent_results.items():
            print(f"\n  {agent_name}:")
            print(f"    Success: {result.success}")
            print(f"    Summary: {result.summary}")
            print(f"    Artifacts: {len(result.artifacts)}")
            print(f"    Bugs Found: {len(result.bugs)}")
            print(f"    Execution Time: {result.execution_time_seconds:.2f}s")
            
            if result.bugs:
                print(f"    Bugs: {', '.join(result.bugs[:3])}")
    
    if report.final_artifacts:
        print("\nGenerated Artifacts:")
        print("-" * 80)
        for path in sorted(report.final_artifacts.keys())[:10]:
            print(f"  - {path}")
        if len(report.final_artifacts) > 10:
            print(f"  ... and {len(report.final_artifacts) - 10} more")
    
    if report.errors_encountered:
        print("\nErrors:")
        print("-" * 80)
        for error in report.errors_encountered:
            print(f"  - {error['type']}: {error['message']}")
    
    print("\n" + "=" * 80 + "\n")


def print_error_summary() -> None:
    """Print error tracking summary."""
    tracker = get_error_tracker()
    summary = tracker.get_summary()
    
    if summary["total_errors"] > 0:
        print("\nError Summary:")
        print("-" * 80)
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Unique Types: {summary['unique_error_types']}")
        print(f"Error Counts: {summary['error_counts']}")
        print()


def main() -> int:
    """Main entry point."""
    try:
        # Configure
        config = configure_environment()
        
        # Example 1: Simple API Development
        print("\n📦 Example 1: Building a Simple Task Management API\n")
        
        requirement_1 = """
        Build a task management REST API with:
        - FastAPI backend with PostgreSQL
        - React/TypeScript frontend with Tailwind CSS
        - User authentication with JWT
        - Task CRUD operations
        - Real-time notifications
        """
        
        dev_report, deploy_report = run_example(
            requirement=requirement_1,
            run_id=1,
            provider="gpt-4-turbo",
            enable_deployment=True,
        )
        
        # Example 2: Microservice Architecture
        print("\n🏗️ Example 2: Microservice Architecture (Development Only)\n")
        
        requirement_2 = """
        Create a microservice-based e-commerce platform:
        - Order service (FastAPI)
        - Payment service (FastAPI)
        - Inventory service (FastAPI)
        - Frontend dashboard (React)
        - Docker compose setup
        """
        
        dev_report_2, _ = run_example(
            requirement=requirement_2,
            run_id=2,
            provider="gpt-4-turbo",
            enable_deployment=False,
        )
        
        # Print error summary
        print_error_summary()
        
        # Success
        logger.info("examples_completed_successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("execution_interrupted_by_user")
        print("\n\n⚠️ Execution interrupted by user")
        return 130
        
    except Exception as exc:
        logger.error(
            "example_execution_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        print(f"\n❌ Error: {exc}")
        print_error_summary()
        return 1


if __name__ == "__main__":
    sys.exit(main())
