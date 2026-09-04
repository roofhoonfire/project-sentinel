import shutil
from pathlib import Path
from typing import Any

from sentinel.mcp_server.build_tools import run_command


def reconfigure_project(
    project_path: Path,
    configure_command: list[str],
    timeout: float,
) -> dict[str, Any]:

    return run_command(
        configure_command,
        project_path,
        timeout,
    )


def clean_rebuild(
    project_path: Path,
    build_dir: Path,
    configure_command: list[str],
    build_command: list[str],
    timeout: float,
) -> dict[str, Any]:

    project_root = project_path.resolve()
    resolved_build = build_dir.resolve()

    # 안전장치:
    # build directory가 target project 밖이면 삭제 금지.
    if (
        resolved_build == project_root
        or project_root not in resolved_build.parents
    ):
        return {
            "success": False,
            "error": f"Unsafe build directory: {resolved_build}",
        }

    if resolved_build.exists():
        shutil.rmtree(resolved_build)

    configure_result = run_command(
        configure_command,
        project_root,
        timeout,
    )

    if not configure_result["success"]:
        return {
            "success": False,
            "stage": "configure",
            "configure": configure_result,
        }

    build_result = run_command(
        build_command,
        project_root,
        timeout,
    )

    return {
        "success": build_result["success"],
        "stage": "build",
        "configure": configure_result,
        "build": build_result,
    }
