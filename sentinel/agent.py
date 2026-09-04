import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel

from agents import Agent, Runner, function_tool
from agents.mcp import (
    MCPServerStdio,
    create_static_tool_filter,
)

from sentinel.rag.retriever import KnowledgeRetriever


# ============================================================
# Paths / Environment
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

load_dotenv(ROOT_DIR / ".env")

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set")


# ============================================================
# RAG Retriever
# ============================================================

retriever = KnowledgeRetriever(
    ROOT_DIR / "knowledge"
)


# ============================================================
# Structured Agent Output
# ============================================================

class DiagnosticResult(BaseModel):
    status: Literal[
        "HEALTHY",
        "BUILD_FAILED",
        "TEST_FAILED",
        "SUSPICIOUS",
    ]

    evidence: str
    diagnosis: str

    recommended_action: Literal[
        "none",
        "clean_rebuild",
        "reconfigure_project",
        "rerun_tests",
        "human_review",
    ]


# ============================================================
# RAG Tool
# ============================================================

@function_tool
def search_project_knowledge(
    query: str,
    top_k: int = 3,
) -> str:
    """
    Search past project architecture notes, development notes,
    known errors, and previous recovery knowledge.

    Args:
        query: Natural-language description of the problem or topic.
        top_k: Number of relevant chunks to retrieve.
    """

    results = retriever.search(
        query,
        top_k=top_k,
    )

    if not results:
        return "No relevant project knowledge found."

    parts = []

    for result in results:
        parts.append(
            f"""
SOURCE: {result.source} #{result.chunk_id}
SCORE: {result.score:.4f}

{result.text}
""".strip()
        )

    return "\n\n---\n\n".join(parts)


# ============================================================
# Diagnostic Agent
# ============================================================

async def run_diagnostic_agent(
    request: str,
) -> DiagnosticResult:

    # Diagnostic Agent is deliberately READ-ONLY.
    #
    # Recovery tools still exist on the MCP server,
    # but this Agent cannot see or execute them.
    #
    # The Harness will decide whether a recommended recovery
    # action is safe and execute it separately.
    server = MCPServerStdio(
        name="Project Sentinel MCP",
        params={
            "command": os.sys.executable,
            "args": [
                "-m",
                "sentinel.mcp_server.server",
            ],
            "cwd": str(ROOT_DIR),
        },
        cache_tools_list=True,
        tool_filter=create_static_tool_filter(
            allowed_tool_names=[
                "git_status",
                "git_diff",
                "run_build",
                "run_tests",
            ]
        ),
    )

    async with server:

        agent = Agent(
            name="Project Sentinel",

            instructions="""
You are Project Sentinel, an engineering diagnostic agent.

Your role is to inspect the monitored software project,
diagnose its current health, and recommend the next action.

You are DIAGNOSTIC ONLY.

You may inspect the current project through these MCP tools:

- git_status
- git_diff
- run_build
- run_tests

You may also search historical project knowledge through:

- search_project_knowledge


DIAGNOSTIC WORKFLOW

When appropriate:

1. Inspect the current Git state.
2. Inspect source changes using git_diff.
3. Build the project.
4. Run the test suite.
5. If a failure or suspicious condition exists,
   search past project knowledge for relevant historical context.
6. Determine the most likely diagnosis.
7. Recommend exactly one next action.


STATUS VALUES

Choose exactly one:

- HEALTHY
  The project builds and tests successfully and no meaningful
  regression is evident.

- BUILD_FAILED
  The build/configuration process fails.

- TEST_FAILED
  The build succeeds but one or more tests fail.

- SUSPICIOUS
  No definitive build/test failure exists, but current evidence
  indicates something that requires attention.


RECOMMENDED ACTION VALUES

Choose exactly one:

- none
  No recovery action is required.

- clean_rebuild
  Recommend only when evidence suggests stale/corrupted build
  state, dependency state, or CMake build-directory problems.

- reconfigure_project
  Recommend when CMake configuration should be regenerated
  without requiring a full clean rebuild.

- rerun_tests
  Recommend when simply repeating the tests is a safe and
  meaningful next action.

- human_review
  Use for source-code defects, logical bugs, unsafe conditions,
  ambiguous failures, or anything requiring engineering judgment.


IMPORTANT SAFETY RULES

- You CANNOT execute recovery actions.
- You CANNOT modify source files.
- You CANNOT delete project files.
- Do not claim an action was executed unless MCP evidence proves it.
- Distinguish CURRENT evidence from HISTORICAL RAG context.
- Historical context is supporting evidence, not proof of the
  current root cause.
""",

            tools=[
                search_project_knowledge,
            ],

            mcp_servers=[
                server,
            ],

            output_type=DiagnosticResult,
        )

        result = await Runner.run(
            agent,
            request,
        )

        return result.final_output
