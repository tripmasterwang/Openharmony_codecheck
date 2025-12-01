"""Run on a single OpenHarmony instance."""

import json
import os
import shutil
import stat
import subprocess
import traceback
from pathlib import Path

import pandas as pd
import typer
import yaml

from minisweagent import global_config_dir
from minisweagent.agents.interactive import InteractiveAgent
from minisweagent.config import builtin_config_dir, get_config_path
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models import get_model
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import logger

app = typer.Typer(add_completion=False)

DEFAULT_OUTPUT = global_config_dir / "last_openharmony_single_run.traj.json"


def convert_xlsx_to_json(xlsx_path: Path) -> Path:
    """Convert Excel file to JSON using the same logic as xls2js.py.
    
    Args:
        xlsx_path: Path to Excel file
        
    Returns:
        Path to the generated JSON file
    """
    logger.info(f"Converting Excel to JSON: {xlsx_path}")
    
    # Read Excel (first row as header)
    df = pd.read_excel(xlsx_path)
    
    # Add index column starting from 0
    df.insert(0, "index", range(len(df)))
    
    # Convert to dict list
    data = df.to_dict(orient='records')
    
    # Output path
    json_path = xlsx_path.with_suffix('.js')
    
    # Write JSON file
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=4))
    
    logger.info(f"✓ Conversion complete: {json_path}")
    return json_path


def ensure_issue_file_exists(project_dir: Path) -> Path:
    """Ensure ISSUE_DESP.js exists, convert from xlsx if needed.
    
    Args:
        project_dir: Project directory path
        
    Returns:
        Path to ISSUE_DESP.js
        
    Raises:
        FileNotFoundError: If neither .js nor .xlsx file exists
    """
    js_file = project_dir / "ISSUE_DESP.js"
    xlsx_file = project_dir / "ISSUE_DESP.xlsx"
    
    # Check if .js file exists
    if js_file.exists():
        logger.debug(f"Found ISSUE_DESP.js in {project_dir}")
        return js_file
    
    # Check if .xlsx file exists
    if xlsx_file.exists():
        logger.info(f"ISSUE_DESP.js not found, converting from ISSUE_DESP.xlsx...")
        return convert_xlsx_to_json(xlsx_file)
    
    # Neither file exists
    raise FileNotFoundError(
        f"Neither ISSUE_DESP.js nor ISSUE_DESP.xlsx found in {project_dir}\n"
        f"Please ensure the issue description file exists."
    )


def load_openharmony_dataset(subset: str, split: str) -> dict[str, dict]:
    """Load OpenHarmony dataset from local files."""
    base_path = Path("dataset1") / "openharmony" / split
    instances = {}
    
    for project_dir in base_path.iterdir():
        if not project_dir.is_dir():
            continue
        
        try:
            # Ensure ISSUE_DESP.js exists (convert from xlsx if needed)
            issue_file = ensure_issue_file_exists(project_dir)
        except FileNotFoundError as e:
            logger.warning(f"Skipping {project_dir.name}: {e}")
            continue
        
        try:
            issues = json.loads(issue_file.read_text())
            project_name = project_dir.name
            
            # 使用列表索引作为 issue_id，从 0 开始
            for list_index, issue in enumerate(issues):
                instance_id = f"openharmony__{project_name}-{list_index}"
                instances[instance_id] = {
                    "instance_id": instance_id,
                    "project_name": project_name,
                    "project_path": str(project_dir.absolute()),
                    "list_index": list_index,  # 列表中的索引 (0-based)
                    "issue_index": issue.get("index", list_index + 1),  # 原始 index 字段 (1-based)
                    "issue_file": issue.get("文件路径", issue.get("issue_file", "")),
                    "rule_id": issue.get("规范", issue.get("rule_id", "")),
                    "description": issue.get("缺陷描述", issue.get("description", "")),
                    "line_number": issue.get("代码行数", issue.get("line_no", 0)),
                    "code_content": issue.get("创建时间", issue.get("code", "")),  # "创建时间" 字段实际存储代码
                    "error_level": issue.get("问题级别", issue.get("error_level", "")),
                    "defect_id": issue.get("缺陷id", ""),
                    "problem_number": issue.get("问题编号", ""),
                }
        except Exception as e:
            logger.warning(f"Failed to load issues from {issue_file}: {e}")
    
    return instances


def make_readonly(path: Path) -> None:
    """Make a directory and all its contents read-only.
    
    Args:
        path: Path to the directory to make read-only
    """
    try:
        # Use chmod to recursively remove write permissions
        subprocess.run(
            ["chmod", "-R", "a-w", str(path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.debug(f"Set {path} to read-only")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to Python's os.chmod if chmod command is not available
        for root, dirs, files in os.walk(path):
            for d in dirs:
                os.chmod(os.path.join(root, d), stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            for f in files:
                os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        os.chmod(path, stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        logger.debug(f"Set {path} to read-only (using Python fallback)")


def prepare_working_directory(
    instance: dict, 
    base_output_dir: str = "dataset1/openharmony/test_result",
    mode: str = "single",
    instance_range: str = ""
) -> str:
    """Copy project to working directory with timestamped naming.
    
    This function:
    1. Ensures the source directory is read-only to prevent accidental modifications
    2. Copies the project to the test_result directory
    3. Returns the path to the working directory where modifications will occur
    
    Args:
        instance: Instance dictionary
        base_output_dir: Base directory for output projects
        mode: Processing mode ('single', 'batch', 'full')
        instance_range: Instance range for batch mode (e.g., '0:10')
        
    Returns:
        Path to the working directory
    """
    import time
    
    source_path = Path(instance["project_path"])
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Ensure source directory is read-only to prevent accidental modifications
    if source_path.exists():
        # Check if already read-only by testing write permission
        test_file = source_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            # If we can write, make it read-only
            make_readonly(source_path)
            logger.info(f"Set source directory to read-only: {source_path}")
        except (PermissionError, OSError):
            # Already read-only or permission denied, which is fine
            logger.debug(f"Source directory appears to be read-only: {source_path}")
    
    # Generate directory name based on mode
    if mode == "single":
        dir_name = f"{timestamp}_single_issue{instance['list_index']}"
    elif mode == "batch":
        dir_name = f"{timestamp}_batch_{instance_range.replace(':', '_to_')}"
    elif mode == "full":
        dir_name = f"{timestamp}_full"
    else:
        dir_name = f"{timestamp}_{mode}"
    
    # Create output directory structure with project name subdirectory
    output_base = Path(base_output_dir)
    project_name = instance["project_name"]
    output_project_path = output_base / project_name / dir_name
    
    # Copy project if not already exists
    if not output_project_path.exists():
        logger.info(f"Copying project from {source_path} to {output_project_path}...")
        shutil.copytree(source_path, output_project_path)
        logger.info(f"✓ Project copied to: {output_project_path}")
    else:
        logger.info(f"Working directory already exists: {output_project_path}")
    
    return str(output_project_path.absolute())


def format_openharmony_issue(instance: dict) -> str:
    """Format OpenHarmony issue as a problem statement."""
    return f"""OpenHarmony Code Quality Issue

Project: {instance['project_name']}
File: {instance['issue_file']}
Issue Index: {instance['issue_index']} (List Index: {instance['list_index']})
Severity: {instance['error_level']}

Coding Standard Rule:
{instance['rule_id']}

Issue Description:
{instance['description']}

Problem Location:
Line {instance['line_number']}: {instance['code_content']}

Task:
Please fix this code quality issue by modifying the file:
{instance['issue_file']}

Note: The file path is relative to the current working directory. Do not use absolute paths.

Make sure your fix complies with the coding standard rule mentioned above.
Focus on STATIC ANALYSIS - read and understand the code, then make the necessary changes.
"""


# fmt: off
@app.command()
def main(
    subset: str = typer.Option("dataset1", "--subset", help="Dataset path", rich_help_panel="Data selection"),
    split: str = typer.Option("test", "--split", help="Dataset split", rich_help_panel="Data selection"),
    instance_spec: str = typer.Option("0", "-i", "--instance", help="OpenHarmony instance ID or index", rich_help_panel="Data selection"),
    model_name: str | None = typer.Option(None, "-m", "--model", help="Model to use", rich_help_panel="Basic"),
    model_class: str | None = typer.Option(None, "-c", "--model-class", help="Model class to use", rich_help_panel="Advanced"),
    config_path: Path = typer.Option(builtin_config_dir / "extra" / "openharmony.yaml", "-c", "--config", help="Path to a config file", rich_help_panel="Basic"),
    exit_immediately: bool = typer.Option(False, "--exit-immediately", help="Exit immediately when the agent wants to finish", rich_help_panel="Basic"),
    output: Path = typer.Option(DEFAULT_OUTPUT, "-o", "--output", help="Output trajectory file", rich_help_panel="Basic"),
) -> None:
    # fmt: on
    """Run on a single OpenHarmony instance."""
    logger.info(f"Loading OpenHarmony dataset from {subset}, split {split}...")
    instances = load_openharmony_dataset(subset, split)
    
    if not instances:
        logger.error("No instances found in the dataset")
        return
    
    if instance_spec.isnumeric():
        instance_spec = sorted(instances.keys())[int(instance_spec)]
    
    if instance_spec not in instances:
        logger.error(f"Instance {instance_spec} not found. Available instances: {list(instances.keys())[:10]}...")
        return
    
    instance: dict = instances[instance_spec]
    logger.info(f"Selected instance: {instance_spec}")
    logger.info(f"Original project path: {instance['project_path']}")
    
    # Prepare working directory (copy project to test_result)
    working_path = prepare_working_directory(instance, mode="single")
    logger.info(f"Working directory: {working_path}")
    
    config_path = get_config_path(config_path)
    logger.info(f"Loading agent config from '{config_path}'")
    config = yaml.safe_load(config_path.read_text())
    
    if model_class is not None:
        config.setdefault("model", {})["model_class"] = model_class
    if exit_immediately:
        config.setdefault("agent", {})["confirm_exit"] = False
    
    # Use local environment with working directory as cwd
    env_config = config.get("environment", {})
    env_config["cwd"] = working_path
    env = LocalEnvironment(**env_config)
    
    agent = InteractiveAgent(
        get_model(model_name, config.get("model", {})),
        env,
        **({"mode": "yolo"} | config.get("agent", {})),
    )
    
    exit_status, result, extra_info = None, None, None
    try:
        task = format_openharmony_issue(instance)
        exit_status, result = agent.run(task)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error processing instance {instance_spec}: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    finally:
        # Save trajectory to working directory (with fixed project)
        # Create a dedicated trajectory folder
        project_prefix = instance_spec.rsplit("-", 1)[0]  # Extract project prefix (e.g., "openharmony__distributedschedule_samgr")
        traj_dir = Path(working_path) / f"{project_prefix}_traj"
        traj_dir.mkdir(parents=True, exist_ok=True)
        working_traj_path = traj_dir / f"{instance_spec}.traj.json"
        save_traj(
            agent,
            working_traj_path,
            exit_status=exit_status,
            result=result,
            extra_info=extra_info,
            instance_id=instance_spec,
            print_path=False,
        )


if __name__ == "__main__":
    app()


