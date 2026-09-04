import subprocess
from pathlib import Path
from typing import Any


def run_command(
    command: list[str],
    cwd: Path,
    timeout: float,
) -> dict[str, Any]:

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "command": " ".join(command),
            "stdout": "",
            "stderr": "Command timed out.",
        }

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "command": " ".join(command),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_build(
    project_path: Path,
    command: list[str],
    timeout: float,
) -> dict[str, Any]:

    return run_command(
        command,
        project_path,
        timeout,
    )


def run_tests(
    project_path: Path,
    command: list[str],
    timeout: float,
) -> dict[str, Any]:

    return run_command(
        command,
        project_path,
        timeout,
    )
