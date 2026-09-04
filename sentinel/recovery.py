import os
from pathlib import Path

from agents.mcp import MCPServerStdio


ROOT_DIR = Path(__file__).resolve().parents[1]


async def execute_recovery_action(
    action: str,
):
    server = MCPServerStdio(
        name="Project Sentinel Recovery MCP",
        params={
            "command": os.sys.executable,
            "args": [
                "-m",
                "sentinel.mcp_server.server",
            ],
            "cwd": str(ROOT_DIR),
        },
        cache_tools_list=True,
    )

    async with server:
        if action == "clean_rebuild":
            return await server.call_tool(
                "clean_rebuild",
                {},
            )

        if action == "reconfigure_project":
            return await server.call_tool(
                "reconfigure_project",
                {},
            )

        if action == "rerun_tests":
            return await server.call_tool(
                "run_tests",
                {},
            )

        raise ValueError(
            f"Unsupported recovery action: {action}"
        )
