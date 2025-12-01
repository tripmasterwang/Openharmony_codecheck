"""HarmoCheck - Fix code quality issues in any directory."""

import concurrent.futures
import json
import logging
import shutil
import time
import traceback
from pathlib import Path

import typer
import yaml
from rich.live import Live

from minisweagent.agents.default import DefaultAgent
from minisweagent.config import builtin_config_dir, get_config_path
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models import get_model
from minisweagent.run.extra.openharmony_single import (
    ensure_issue_file_exists,
    format_openharmony_issue,
)
from minisweagent.run.extra.utils.batch_progress import RunBatchProgressManager
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import logger

app = typer.Typer(add_completion=False)


def load_issues_from_directory(project_dir: Path) -> list[dict]:
    """Load issues from a directory containing ISSUE_DESP.js or ISSUE_DESP.xlsx.
    
    Args:
        project_dir: Directory containing the issue file
        
    Returns:
        List of issue dictionaries
    """
    issue_file = ensure_issue_file_exists(project_dir)
    issues = json.loads(issue_file.read_text())
    return issues


def prepare_working_directory(
    source_dir: Path,
    output_dir: Path,
    project_name: str | None = None,
) -> Path:
    """Copy project to working directory with timestamped naming.
    
    Args:
        source_dir: Source directory to copy
        output_dir: Base output directory
        project_name: Optional project name (defaults to source_dir.name)
        
    Returns:
        Path to the working directory
    """
    if project_name is None:
        project_name = source_dir.name
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    dir_name = f"{timestamp}_{project_name}"
    
    working_path = output_dir / dir_name
    working_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not working_path.exists():
        logger.info(f"Copying project from {source_dir} to {working_path}...")
        
        # Check if output_dir is inside source_dir to avoid recursive copying
        try:
            output_dir_relative = output_dir.resolve().relative_to(source_dir.resolve())
            # Output directory is inside source directory, need to exclude it
            output_dir_name = output_dir_relative.parts[0] if output_dir_relative.parts else None
            
            def ignore_func(directory, contents):
                """Ignore the output directory to prevent recursive copying."""
                ignored = []
                if output_dir_name and output_dir_name in contents:
                    ignored.append(output_dir_name)
                return ignored
            
            shutil.copytree(source_dir, working_path, ignore=ignore_func)
        except ValueError:
            # Output directory is not inside source directory, copy normally
            shutil.copytree(source_dir, working_path)
        
        logger.info(f"✓ Project copied to: {working_path}")
    else:
        logger.info(f"Working directory already exists: {working_path}")
    
    return working_path


def create_instance_from_issue(
    issue: dict,
    list_index: int,
    project_name: str,
    project_path: str,
) -> dict:
    """Create an instance dictionary from an issue.
    
    Args:
        issue: Issue dictionary from ISSUE_DESP.js
        list_index: Index in the issues list (0-based)
        project_name: Name of the project
        project_path: Path to the project directory
        
    Returns:
        Instance dictionary
    """
    instance_id = f"harmocheck__{project_name}-{list_index}"
    return {
        "instance_id": instance_id,
        "project_name": project_name,
        "project_path": project_path,
        "list_index": list_index,
        "issue_index": issue.get("index", list_index + 1),
        "issue_file": issue.get("文件路径", issue.get("issue_file", "")),
        "rule_id": issue.get("规范", issue.get("rule_id", "")),
        "description": issue.get("缺陷描述", issue.get("description", "")),
        "line_number": issue.get("代码行数", issue.get("line_no", 0)),
        "code_content": issue.get("创建时间", issue.get("code", "")),
        "error_level": issue.get("问题级别", issue.get("error_level", "")),
        "defect_id": issue.get("缺陷id", ""),
        "problem_number": issue.get("问题编号", ""),
    }


class ProgressTrackingAgent(DefaultAgent):
    """Simple wrapper around DefaultAgent that provides progress updates."""

    def __init__(self, *args, progress_manager: RunBatchProgressManager, instance_id: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_manager: RunBatchProgressManager = progress_manager
        self.instance_id = instance_id

    def step(self) -> dict:
        """Override step to provide progress updates."""
        self.progress_manager.update_instance_status(
            self.instance_id, f"Step {self.model.n_calls + 1:3d} (${self.model.cost:.2f})"
        )
        return super().step()


def process_issue(
    instance: dict,
    config: dict,
    progress_manager: RunBatchProgressManager,
    working_path: Path,
) -> None:
    """Process a single issue."""
    instance_id = instance["instance_id"]
    
    progress_manager.on_instance_start(instance_id)
    progress_manager.update_instance_status(instance_id, "Starting...")
    
    agent = None
    extra_info = None
    
    try:
        # Use local environment with working directory as cwd
        env_config = config.get("environment", {}).copy()
        env_config["cwd"] = str(working_path)
        env = LocalEnvironment(**env_config)
        
        # Use model from config (which may have been overridden by env var)
        model_config = config.get("model", {}).copy()
        
        # Ensure model registry is loaded from environment variable if not in config
        import os
        if "litellm_model_registry" not in model_config:
            registry_path = os.getenv("LITELLM_MODEL_REGISTRY_PATH")
            if registry_path:
                model_config["litellm_model_registry"] = registry_path
        
        agent = ProgressTrackingAgent(
            get_model(model_config.get("model_name"), model_config),
            env,
            progress_manager=progress_manager,
            instance_id=instance_id,
            **config.get("agent", {}),
        )
        
        task = format_openharmony_issue(instance)
        exit_status, result = agent.run(task)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error processing issue {instance_id}: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    finally:
        # Save trajectory to working directory
        traj_dir = working_path / "harmocheck_traj"
        traj_dir.mkdir(parents=True, exist_ok=True)
        traj_path = traj_dir / f"{instance_id}.traj.json"
        save_traj(
            agent,
            traj_path,
            exit_status=exit_status,
            result=result,
            extra_info=extra_info,
            instance_id=instance_id,
            print_path=False,
        )
        progress_manager.on_instance_end(instance_id, exit_status)


# fmt: off
@app.command()
def main(
    input_dir: Path = typer.Option(..., "-i", "--input", help="Directory containing code to fix (must contain ISSUE_DESP.js or ISSUE_DESP.xlsx)"),
    output_dir: Path = typer.Option(..., "-o", "--output", help="Directory to save fixed code"),
    model_name: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "-c", "--model-class", help="Model class to use", rich_help_panel="Advanced"),
    config_path: Path = typer.Option(builtin_config_dir / "extra" / "openharmony.yaml", "--config", help="Path to a config file", rich_help_panel="Basic"),
    exit_immediately: bool = typer.Option(False, "--exit-immediately", help="Exit immediately when the agent wants to finish", rich_help_panel="Basic"),
    issue_index: int | None = typer.Option(None, "--issue", help="Fix only a specific issue by index (0-based). If not specified, fixes all issues.", rich_help_panel="Data selection"),
    workers: int = typer.Option(1, "-w", "--workers", help="Number of worker threads for parallel processing", rich_help_panel="Basic"),
) -> None:
    # fmt: on
    """Fix code quality issues in a directory.
    
    This command:
    1. Reads ISSUE_DESP.js or ISSUE_DESP.xlsx from the input directory
    2. Fixes all issues (or a specific issue if -i is specified)
    3. Saves the fixed code to the output directory
    """
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    if not input_dir.is_dir():
        logger.error(f"Input path is not a directory: {input_dir}")
        return
    
    logger.info(f"Loading issues from {input_dir}...")
    try:
        issues = load_issues_from_directory(input_dir)
    except FileNotFoundError as e:
        logger.error(f"Failed to load issues: {e}")
        return
    except Exception as e:
        logger.error(f"Error loading issues: {e}", exc_info=True)
        return
    
    if not issues:
        logger.warning("No issues found in the issue file")
        return
    
    project_name = input_dir.name
    logger.info(f"Found {len(issues)} issue(s) in project '{project_name}'")
    
    # Filter issues if specific index is requested
    if issue_index is not None:
        if issue_index < 0 or issue_index >= len(issues):
            logger.error(f"Issue index {issue_index} is out of range (0-{len(issues)-1})")
            return
        issues = [issues[issue_index]]
        logger.info(f"Processing only issue at index {issue_index}")
    
    # Prepare working directory
    working_path = prepare_working_directory(input_dir, output_dir, project_name)
    logger.info(f"Working directory: {working_path}")
    
    # Load config
    config_path = get_config_path(config_path)
    logger.info(f"Loading agent config from '{config_path}'")
    config = yaml.safe_load(config_path.read_text())
    
    # If model_name is not specified, use environment variable or keep config default
    # But if model_name is explicitly None and env var exists, prefer env var over config
    if model_name is None:
        import os
        env_model = os.getenv("MSWEA_MODEL_NAME")
        if env_model:
            config.setdefault("model", {})["model_name"] = env_model
            logger.info(f"Using model from environment variable: {env_model}")
        else:
            # Warn user if using config default (which might be Anthropic)
            default_model = config.get("model", {}).get("model_name", "unknown")
            if "anthropic" in default_model.lower() or "claude" in default_model.lower():
                logger.warning(
                    f"⚠️  No model specified and MSWEA_MODEL_NAME not set. "
                    f"Using config default: {default_model}\n"
                    f"   If you encounter API errors, please either:\n"
                    f"   1. Set MSWEA_MODEL_NAME in ~/.config/mini-swe-agent/.env\n"
                    f"   2. Or use -m flag: harmocheck -i ./ -o ./output -m openai/deepseek-v3.2-exp"
                )
    elif model_name:
        # Explicitly specified model takes precedence
        config.setdefault("model", {})["model_name"] = model_name
    
    if model_class is not None:
        config.setdefault("model", {})["model_class"] = model_class
    
    # Remove InteractiveAgent-specific config options (confirm_exit, mode)
    # DefaultAgent doesn't need these - it always executes automatically
    agent_config = config.get("agent", {}).copy()
    agent_config.pop("confirm_exit", None)
    agent_config.pop("mode", None)
    config["agent"] = agent_config
    
    # Reduce logging verbosity - only show errors and warnings
    logging.getLogger("minisweagent").setLevel(logging.WARNING)
    
    # Create instances from issues
    instances = []
    for list_index, issue in enumerate(issues):
        # Adjust list_index if we're processing a filtered subset
        if issue_index is not None:
            list_index = issue_index
        
        instance = create_instance_from_issue(
            issue,
            list_index,
            project_name,
            str(working_path),
        )
        instances.append(instance)
    
    # Setup progress manager
    progress_manager = RunBatchProgressManager(len(instances), None)
    
    def process_futures(futures: dict[concurrent.futures.Future, str]):
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except concurrent.futures.CancelledError:
                pass
            except Exception as e:
                instance_id = futures[future]
                logger.error(f"Error in future for instance {instance_id}: {e}", exc_info=True)
                progress_manager.on_uncaught_exception(instance_id, e)
    
    # Process instances
    logger.info(f"Starting processing with {workers} worker(s)...")
    with Live(progress_manager.render_group, refresh_per_second=4):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_issue, instance, config, progress_manager, working_path): instance[
                    "instance_id"
                ]
                for instance in instances
            }
            try:
                process_futures(futures)
            except KeyboardInterrupt:
                logger.info("Cancelling all pending jobs. Press ^C again to exit immediately.")
                for future in futures:
                    if not future.running() and not future.done():
                        future.cancel()
                process_futures(futures)
    
    logger.info("=" * 60)
    logger.info(f"Processing complete! Fixed code saved to: {working_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    app()

