#!/usr/bin/env python3

"""Run mini-SWE-agent on all OpenHarmony projects and issues."""

import concurrent.futures
import json
import threading
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
from minisweagent.utils.log import add_file_handler, logger

_HELP_TEXT = """Run mini-SWE-agent on all OpenHarmony projects and issues.

[not dim]
Automatically discovers all projects in the dataset and processes all issues.
This is the top-level batch processing command for OpenHarmony.
[/not dim]
"""

app = typer.Typer(rich_markup_mode="rich", add_completion=False)

_OUTPUT_FILE_LOCK = threading.Lock()


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


def update_results_file(output_path: Path, instance_id: str, model_name: str, result: str):
    """Update the output JSON file with results from a single instance."""
    with _OUTPUT_FILE_LOCK:
        output_data = {}
        if output_path.exists():
            output_data = json.loads(output_path.read_text())
        output_data[instance_id] = {
            "model_name_or_path": model_name,
            "instance_id": instance_id,
            "result": result,
        }
        output_path.write_text(json.dumps(output_data, indent=2))


def remove_from_results_file(output_path: Path, instance_id: str):
    """Remove an instance from the results file."""
    if not output_path.exists():
        return
    with _OUTPUT_FILE_LOCK:
        output_data = json.loads(output_path.read_text())
        if instance_id in output_data:
            del output_data[instance_id]
            output_path.write_text(json.dumps(output_data, indent=2))


def process_instance(
    instance: dict,
    output_dir: Path,
    config: dict,
    progress_manager: RunBatchProgressManager,
    working_path: str,
) -> None:
    """Process a single OpenHarmony instance."""
    instance_id = instance["instance_id"]
    instance_dir = output_dir / instance_id
    
    # Avoid inconsistent state if something fails
    remove_from_results_file(output_dir / "results.json", instance_id)
    (instance_dir / f"{instance_id}.traj.json").unlink(missing_ok=True)
    
    model = get_model(config=config.get("model", {}))
    task = format_openharmony_issue(instance)

    progress_manager.on_instance_start(instance_id)
    progress_manager.update_instance_status(instance_id, "Starting...")

    agent = None
    extra_info = None

    try:
        # Use local environment with shared working directory as cwd
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
        save_traj(
            agent,
            instance_dir / f"{instance_id}.traj.json",
            exit_status=exit_status,
            result=result,
            extra_info=extra_info,
            instance_id=instance_id,
            print_fct=logger.info,
        )
        update_results_file(output_dir / "results.json", instance_id, model.config.model_name, result)
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
    output: str = typer.Option("", "-o", "--output", help="Output directory", rich_help_panel="Basic"),
    workers: int = typer.Option(1, "-w", "--workers", help="Number of worker threads for parallel processing", rich_help_panel="Basic"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "--model-class", help="Model class to use", rich_help_panel="Advanced"),
    redo_existing: bool = typer.Option(False, "--redo-existing", help="Redo existing instances", rich_help_panel="Data selection"),
    config_spec: Path = typer.Option(builtin_config_dir / "extra" / "openharmony.yaml", "-c", "--config", help="Path to a config file", rich_help_panel="Basic"),
    project_filter: str = typer.Option("", "--project", help="Filter by project name (e.g., 'vendor_telink')", rich_help_panel="Data selection"),
) -> None:
    # fmt: on
    """Run mini-SWE-agent on all OpenHarmony projects and issues.
    
    This command automatically discovers all projects in the dataset directory
    and processes all issues from each project.
    """
    
    # Setup output directory
    if not output:
        output = f"openharmony_full_results_{time.strftime('%Y%m%d_%H%M%S')}"
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results will be saved to {output_path}")
    add_file_handler(output_path / "minisweagent.log")

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
    
    # Skip existing instances if requested
    if not redo_existing and (output_path / "results.json").exists():
        existing_instances = list(json.loads((output_path / "results.json").read_text()).keys())
        logger.info(f"Skipping {len(existing_instances)} existing instances")
        all_instances = [inst for inst in all_instances if inst["instance_id"] not in existing_instances]
    
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

    # Prepare working directory for full processing
    # All instances share the same working directory
    logger.info("Preparing working directory...")
    working_path = prepare_working_directory(all_instances[0], mode="full")
    logger.info(f"Working directory: {working_path}")

    # Setup progress manager
    progress_manager = RunBatchProgressManager(
        len(all_instances), output_path / f"exit_statuses_{time.time()}.yaml"
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
                executor.submit(process_instance, instance, output_path, config, progress_manager, working_path): instance[
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
    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Results file: {output_path / 'results.json'}")
    logger.info(f"Log file: {output_path / 'minisweagent.log'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    app()

