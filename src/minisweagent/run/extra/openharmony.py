#!/usr/bin/env python3

"""Run mini-SWE-agent on all OpenHarmony projects and issues."""

import concurrent.futures
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
    format_openharmony_issue,
    load_openharmony_dataset,
    prepare_working_directory,
)
from minisweagent.run.extra.utils.batch_progress import RunBatchProgressManager
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import logger

_HELP_TEXT = """Run mini-SWE-agent on all OpenHarmony projects and issues.

[not dim]
Automatically discovers all projects in the dataset and processes all issues.
This is the top-level batch processing command for OpenHarmony.
[/not dim]
"""

app = typer.Typer(rich_markup_mode="rich", add_completion=False)


class ProgressTrackingAgent(DefaultAgent):
    """Simple wrapper around DefaultAgent that provides progress updates."""

    def __init__(self, *args, progress_manager: RunBatchProgressManager, instance_id: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_manager: RunBatchProgressManager = progress_manager
        self.instance_id = instance_id

    def step(self) -> dict:
        """Override step to provide progress updates."""
        self.progress_manager.update_instance_status(
            self.instance_id, f"Step {self.model.n_calls + 1:3d}"
        )
        return super().step()


def process_instance(
    instance: dict,
    config: dict,
    progress_manager: RunBatchProgressManager,
    working_paths: dict[str, str],
) -> None:
    """Process a single OpenHarmony instance."""
    instance_id = instance["instance_id"]
    
    model = get_model(config=config.get("model", {}))
    task = format_openharmony_issue(instance)

    progress_manager.on_instance_start(instance_id)
    progress_manager.update_instance_status(instance_id, "Starting...")

    agent = None
    extra_info = None

    try:
        # Use local environment with project-specific working directory as cwd
        project_name = instance["project_name"]
        working_path = working_paths[project_name]
        env_config = config.get("environment", {})
        env_config["cwd"] = working_path
        env = LocalEnvironment(**env_config)
        
        agent = ProgressTrackingAgent(
            model,
            env,
            progress_manager=progress_manager,
            instance_id=instance_id,
            **config.get("agent", {}),
        )
        exit_status, result = agent.run(task)
    except Exception as e:
        logger.error(f"Error processing instance {instance_id}: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    finally:
        # Save trajectory to working directory (with fixed project)
        # Create a dedicated trajectory folder
        project_prefix = instance_id.rsplit("-", 1)[0]  # Extract project prefix (e.g., "openharmony__distributedschedule_samgr")
        traj_dir = Path(working_path) / f"{project_prefix}_traj"
        traj_dir.mkdir(parents=True, exist_ok=True)
        working_traj_path = traj_dir / f"{instance_id}.traj.json"
        save_traj(
            agent,
            working_traj_path,
            exit_status=exit_status,
            result=result,
            extra_info=extra_info,
            instance_id=instance_id,
            print_path=False,
        )
        progress_manager.on_instance_end(instance_id, exit_status)


def discover_all_instances(subset: str, split: str) -> dict[str, list[dict]]:
    """Discover all instances from all projects in the dataset.
    
    Returns:
        Dict mapping project_name -> list of instances
    """
    instances_dict = load_openharmony_dataset(subset, split)
    
    # Group instances by project
    projects = {}
    for instance in instances_dict.values():
        project_name = instance["project_name"]
        if project_name not in projects:
            projects[project_name] = []
        projects[project_name].append(instance)
    
    # Sort instances within each project by list_index
    for project_name in projects:
        projects[project_name].sort(key=lambda x: x["list_index"])
    
    return projects


# fmt: off
@app.command(help=_HELP_TEXT)
def main(
    subset: str = typer.Option("dataset1", "--subset", help="Dataset path", rich_help_panel="Data selection"),
    split: str = typer.Option("test", "--split", help="Dataset split (test/train)", rich_help_panel="Data selection"),
    workers: int = typer.Option(1, "-w", "--workers", help="Number of worker threads for parallel processing", rich_help_panel="Basic"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "--model-class", help="Model class to use", rich_help_panel="Advanced"),
    config_spec: Path = typer.Option(builtin_config_dir / "extra" / "openharmony.yaml", "-c", "--config", help="Path to a config file", rich_help_panel="Basic"),
    project_filter: str = typer.Option("", "--project", help="Filter by project name (e.g., 'vendor_telink')", rich_help_panel="Data selection"),
) -> None:
    # fmt: on
    """Run mini-SWE-agent on all OpenHarmony projects and issues.
    
    This command automatically discovers all projects in the dataset directory
    and processes all issues from each project.
    """

    # Discover all projects and instances
    logger.info(f"Discovering projects in {subset}/{split}...")
    projects = discover_all_instances(subset, split)
    
    # Filter projects if specified
    if project_filter:
        projects = {k: v for k, v in projects.items() if project_filter in k}
        logger.info(f"Filtered to projects matching '{project_filter}'")
    
    # Log project summary
    logger.info(f"Found {len(projects)} project(s):")
    total_instances = 0
    for project_name, instances in sorted(projects.items()):
        logger.info(f"  - {project_name}: {len(instances)} issues")
        total_instances += len(instances)
    logger.info(f"Total: {total_instances} issues across {len(projects)} project(s)")
    
    if total_instances == 0:
        logger.warning("No instances to process!")
        return

    # Collect all instances
    all_instances = []
    for project_name in sorted(projects.keys()):
        all_instances.extend(projects[project_name])
    
    
    logger.info(f"Processing {len(all_instances)} instances...")
    
    if not all_instances:
        logger.warning("No instances to process after filtering!")
        return

    # Load config
    config_path = get_config_path(config_spec)
    logger.info(f"Loading agent config from '{config_path}'")
    config = yaml.safe_load(config_path.read_text())
    
    if model is not None:
        config.setdefault("model", {})["model_name"] = model
    if model_class is not None:
        config.setdefault("model", {})["model_class"] = model_class

    # Prepare working directories for all projects
    # Each project gets its own working directory
    logger.info("Preparing working directories for all projects...")
    working_paths = {}
    for project_name in sorted(projects.keys()):
        # Use the first instance of each project to prepare its working directory
        project_instances = projects[project_name]
        working_path = prepare_working_directory(project_instances[0], mode="full")
        working_paths[project_name] = working_path
        logger.info(f"  {project_name}: {working_path}")

    # Setup progress manager
    progress_manager = RunBatchProgressManager(
        len(all_instances), None
    )

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
                executor.submit(process_instance, instance, config, progress_manager, working_paths): instance[
                    "instance_id"
                ]
                for instance in all_instances
            }
            try:
                process_futures(futures)
            except KeyboardInterrupt:
                logger.info("Cancelling all pending jobs. Press ^C again to exit immediately.")
                for future in futures:
                    if not future.running() and not future.done():
                        future.cancel()
                process_futures(futures)
    
    # Summary
    logger.info("=" * 60)
    logger.info("Processing complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    app()

