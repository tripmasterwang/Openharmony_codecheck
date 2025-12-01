#!/usr/bin/env python3

"""Run mini-SWE-agent on OpenHarmony instances in batch mode."""

import concurrent.futures
import json
import re
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

_HELP_TEXT = """Run mini-SWE-agent on OpenHarmony instances in batch mode.

[not dim]
Process multiple code quality issues from OpenHarmony projects.
Supports parallel processing and progress tracking.
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
    
    # Avoid inconsistent state if something fails
    remove_from_results_file(output_dir / "results.json", instance_id)
    
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
        update_results_file(output_dir / "results.json", instance_id, model.config.model_name, result)
        progress_manager.on_instance_end(instance_id, exit_status)


def parse_instance_range(range_spec: str, all_instance_ids: list[str]) -> list[str]:
    """Parse instance range specification like 'openharmony__vendor_telink-0:10' or '0:10'."""
    if ":" not in range_spec:
        # Single instance
        return [range_spec] if range_spec in all_instance_ids else []
    
    # Range specification
    if range_spec.count("__") == 1 and "-" in range_spec:
        # Format: openharmony__vendor_telink-0:10
        prefix, range_part = range_spec.rsplit("-", 1)
        if ":" in range_part:
            start_str, end_str = range_part.split(":", 1)
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else None
            
            # Filter instances matching the prefix
            matching = [iid for iid in all_instance_ids if iid.startswith(prefix + "-")]
            
            # Extract indices and sort
            instance_dict = {}
            for iid in matching:
                idx = int(iid.split("-")[-1])
                instance_dict[idx] = iid
            
            # Select range
            sorted_indices = sorted(instance_dict.keys())
            if end is None:
                selected_indices = [i for i in sorted_indices if i >= start]
            else:
                selected_indices = [i for i in sorted_indices if start <= i < end]
            
            return [instance_dict[i] for i in selected_indices]
    
    # Simple numeric range: 0:10
    if range_spec.replace(":", "").replace("-", "").isdigit():
        parts = range_spec.split(":")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else len(all_instance_ids)
        
        # Sort by numeric suffix
        sorted_ids = sorted(all_instance_ids, key=lambda x: int(x.split("-")[-1]) if x.split("-")[-1].isdigit() else 0)
        return sorted_ids[start:end]
    
    return []


def filter_instances(
    instances: list[dict], *, filter_spec: str = "", slice_spec: str = "", instance_range: str = ""
) -> list[dict]:
    """Filter and slice a list of OpenHarmony instances."""
    before_filter = len(instances)
    
    # Apply regex filter
    if filter_spec:
        instances = [instance for instance in instances if re.match(filter_spec, instance["instance_id"])]
        if (after_filter := len(instances)) != before_filter:
            logger.info(f"Instance filter: {before_filter} -> {after_filter} instances")
            before_filter = after_filter
    
    # Apply instance range (priority over slice)
    if instance_range:
        all_ids = [inst["instance_id"] for inst in instances]
        selected_ids = parse_instance_range(instance_range, all_ids)
        instances = [inst for inst in instances if inst["instance_id"] in selected_ids]
        logger.info(f"Instance range '{instance_range}': selected {len(instances)} instances")
    elif slice_spec:
        # Apply slice specification
        values = [int(x) if x else None for x in slice_spec.split(":")]
        instances = instances[slice(*values)]
        if (after_slice := len(instances)) != before_filter:
            logger.info(f"Instance slice: {before_filter} -> {after_slice} instances")
    
    return instances


# fmt: off
@app.command(help=_HELP_TEXT)
def main(
    subset: str = typer.Option("dataset1", "--subset", help="Dataset path", rich_help_panel="Data selection"),
    split: str = typer.Option("test", "--split", help="Dataset split (test/train)", rich_help_panel="Data selection"),
    instance_range: str = typer.Option("", "-i", "--instance", help="Instance range (e.g., 'openharmony__vendor_telink-0:10' or '0:10')", rich_help_panel="Data selection"),
    slice_spec: str = typer.Option("", "--slice", help="Slice specification (e.g., '0:5' for first 5 instances)", rich_help_panel="Data selection"),
    filter_spec: str = typer.Option("", "--filter", help="Filter instance IDs by regex", rich_help_panel="Data selection"),
    output: str = typer.Option("", "-o", "--output", help="Output directory", rich_help_panel="Basic"),
    workers: int = typer.Option(1, "-w", "--workers", help="Number of worker threads for parallel processing", rich_help_panel="Basic"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "--model-class", help="Model class to use", rich_help_panel="Advanced"),
    redo_existing: bool = typer.Option(False, "--redo-existing", help="Redo existing instances", rich_help_panel="Data selection"),
    config_spec: Path = typer.Option(builtin_config_dir / "extra" / "openharmony.yaml", "-c", "--config", help="Path to a config file", rich_help_panel="Basic"),
) -> None:
    # fmt: on
    """Run mini-SWE-agent on OpenHarmony instances in batch mode."""
    
    # Setup output directory
    if not output:
        output = f"openharmony_batch_results_{time.strftime('%Y%m%d_%H%M%S')}"
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results will be saved to {output_path}")
    add_file_handler(output_path / "minisweagent.log")

    # Load dataset
    logger.info(f"Loading OpenHarmony dataset from {subset}, split {split}...")
    instance_dict = load_openharmony_dataset(subset, split)
    instances = list(instance_dict.values())
    logger.info(f"Loaded {len(instances)} instances")

    # Filter instances
    instances = filter_instances(
        instances,
        filter_spec=filter_spec,
        slice_spec=slice_spec,
        instance_range=instance_range,
    )
    
    # Skip existing instances if requested
    if not redo_existing and (output_path / "results.json").exists():
        existing_instances = list(json.loads((output_path / "results.json").read_text()).keys())
        logger.info(f"Skipping {len(existing_instances)} existing instances")
        instances = [instance for instance in instances if instance["instance_id"] not in existing_instances]
    
    logger.info(f"Running on {len(instances)} instances...")
    
    if not instances:
        logger.warning("No instances to process!")
        return

    # Load config
    config_path = get_config_path(config_spec)
    logger.info(f"Loading agent config from '{config_path}'")
    config = yaml.safe_load(config_path.read_text())
    
    if model is not None:
        config.setdefault("model", {})["model_name"] = model
    if model_class is not None:
        config.setdefault("model", {})["model_class"] = model_class

    # Prepare working directory for batch processing
    # All instances in a batch share the same working directory
    logger.info("Preparing working directory...")
    working_path = prepare_working_directory(instances[0], mode="batch", instance_range=instance_range or slice_spec or "batch")
    logger.info(f"Working directory: {working_path}")

    # Setup progress manager
    progress_manager = RunBatchProgressManager(
        len(instances), output_path / f"exit_statuses_{time.time()}.yaml"
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
    with Live(progress_manager.render_group, refresh_per_second=4):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_instance, instance, output_path, config, progress_manager, working_path): instance[
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


if __name__ == "__main__":
    app()

