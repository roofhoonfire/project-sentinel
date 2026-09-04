import subprocess
from pathlib import Path
from typing import Any


GIT_EXCLUDED_PATHS = [
    ":(exclude)firmware/zynq/vitis_workspace/.metadata/**",
    ":(exclude)firmware/zynq/vitis_workspace/IDE.log",
]


def _run_git(
    project_path: Path,
    args: list[str],
    timeout: float,
) -> dict[str, Any]:

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Git command timed out.",
        }

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def get_git_status(
    project_path: Path,
    timeout: float,
) -> dict[str, Any]:

    return _run_git(
        project_path,
        [
            "status",
            "--short",
            "--",
            ".",
            *GIT_EXCLUDED_PATHS,
        ],
        timeout,
    )


def get_git_diff(
    project_path: Path,
    timeout: float,
) -> dict[str, Any]:

    return _run_git(
        project_path,
        [
            "diff",
            "--",
            ".",
            *GIT_EXCLUDED_PATHS,
        ],
        timeout,
    )
