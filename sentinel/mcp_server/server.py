from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from sentinel.config import load_config
from sentinel.mcp_server.git_tools import (
    get_git_diff,
    get_git_status,
)
from sentinel.mcp_server.build_tools import (
    run_build as run_build_impl,
    run_tests as run_tests_impl,
)
from sentinel.mcp_server.recovery_tools import (
    clean_rebuild as clean_rebuild_impl,
    reconfigure_project as reconfigure_project_impl,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.json"

config = load_config(CONFIG_PATH)

mcp = MCPServer("Project Sentinel")


@mcp.tool()
def git_status() -> dict[str, Any]:
    """Return the current Git working-tree status of the monitored project."""

    return get_git_status(
        config.project_path,
        config.command_timeout_seconds,
    )


@mcp.tool()
def git_diff() -> dict[str, Any]:
    """Return unstaged source-code changes in the monitored project."""

    return get_git_diff(
        config.project_path,
        config.command_timeout_seconds,
    )

@mcp.tool()
def run_build() -> dict[str, Any]:
    """Build the monitored project and return compiler/build output."""

    fault_marker = (
        config.build_dir
        / ".sentinel_force_reconfigure"
    )

    if fault_marker.exists():
        return {
            "success": False,
            "returncode": 1,
            "command": "cmake --build build",
            "stdout": "",
            "stderr": (
                "Sentinel fault injection: "
                "stale or corrupted CMake build state detected. "
                "A clean configure and rebuild is recommended."
            ),
        }

    return run_build_impl(
        config.project_path,
        config.build_command,
        config.command_timeout_seconds,
    )
@mcp.tool()
def run_tests() -> dict[str, Any]:
    """Run the monitored project's test suite and return test output."""

    return run_tests_impl(
        config.project_path,
        config.test_command,
        config.command_timeout_seconds,
    )


@mcp.tool()
def reconfigure_project() -> dict[str, Any]:
    """Re-run CMake configuration without deleting the existing build directory."""

    return reconfigure_project_impl(
        config.project_path,
        config.configure_command,
        config.command_timeout_seconds,
    )


@mcp.tool()
def clean_rebuild() -> dict[str, Any]:
    """Delete only the configured build directory, reconfigure, and rebuild the project."""

    return clean_rebuild_impl(
        config.project_path,
        config.build_dir,
        config.configure_command,
        config.build_command,
        config.command_timeout_seconds,
    )


if __name__ == "__main__":
    mcp.run()
