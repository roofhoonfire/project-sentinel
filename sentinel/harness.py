import asyncio
import time
from pathlib import Path
from queue import Empty, Queue

from sentinel.agent import run_diagnostic_agent
from sentinel.config import SentinelConfig
from sentinel.recovery import execute_recovery_action
from sentinel.reporting import SentinelReportWriter
from sentinel.safety import is_safe_action
from sentinel.watcher import (
    ProjectChange,
    ProjectWatcher,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


class SentinelHarness:
    def __init__(
        self,
        config: SentinelConfig,
    ):
        self.config = config

        self.event_queue: Queue[
            ProjectChange
        ] = Queue()

        self.watcher = ProjectWatcher(
            config,
            self.event_queue,
        )

        self.reporter = SentinelReportWriter(
            ROOT_DIR / "reports"
        )

    # ========================================================
    # Event batching
    # ========================================================

    def _collect_changes(
        self,
        first_change: ProjectChange,
    ) -> list[ProjectChange]:

        changes = {
            str(first_change.path): first_change
        }

        deadline = (
            time.monotonic()
            + self.config.debounce_seconds
        )

        while True:
            remaining = (
                deadline - time.monotonic()
            )

            if remaining <= 0:
                break

            try:
                change = self.event_queue.get(
                    timeout=remaining
                )

                changes[str(change.path)] = change

                deadline = (
                    time.monotonic()
                    + self.config.debounce_seconds
                )

            except Empty:
                break

        return list(
            changes.values()
        )

    # ========================================================
    # Prompt
    # ========================================================

    def _build_diagnostic_request(
        self,
        changes: list[ProjectChange],
    ) -> str:

        lines = []

        for change in changes:

            try:
                relative = (
                    change.path.relative_to(
                        self.config.project_path
                    )
                )

            except ValueError:
                relative = change.path

            lines.append(
                f"- {change.event_type}: {relative}"
            )

        change_text = "\n".join(lines)

        return f"""
Project Sentinel detected the following source changes:

{change_text}

Inspect the monitored project after these changes.

Required workflow:

1. Inspect the current Git state.
2. Inspect relevant source changes if necessary.
3. Build the project.
4. Run the test suite.
5. If a failure or suspicious condition exists,
   search past project knowledge for relevant context.
6. Diagnose the current project health.
7. Recommend exactly one next action.

Do NOT execute recovery actions.
Do NOT modify source files.

Return the structured diagnostic result.
"""

    # ========================================================
    # Recovery verification
    # ========================================================

    async def _verify_recovery(self):

        return await run_diagnostic_agent(
            """
A safe automated recovery action has just been executed
by the Project Sentinel Harness.

Verify the current project state.

1. Build the project.
2. Run the complete test suite.
3. Inspect other project state only if necessary.
4. Determine whether the project is healthy.

Do NOT execute another recovery action.
Do NOT modify source files.

If build and tests pass without meaningful regression:
- status must be HEALTHY
- recommended_action must be none

Return the structured diagnostic result.
"""
        )

    # ========================================================
    # Helpers
    # ========================================================

    def _serialize_changes(
        self,
        changes: list[ProjectChange],
    ) -> list[dict]:

        result = []

        for change in changes:

            try:
                relative = (
                    change.path.relative_to(
                        self.config.project_path
                    )
                )

            except ValueError:
                relative = change.path

            result.append(
                {
                    "event_type":
                        change.event_type,
                    "path":
                        str(relative),
                    "timestamp":
                        change.timestamp,
                }
            )

        return result

    @staticmethod
    def _extract_recovery_result(
        result,
    ) -> tuple[bool, dict]:

        structured = getattr(
            result,
            "structured_content",
            None,
        )

        if not isinstance(
            structured,
            dict,
        ):
            return False, {}

        success = bool(
            structured.get(
                "success",
                False,
            )
        )

        return success, structured

    # ========================================================
    # Closed-loop cycle
    # ========================================================

    def _run_agent(
        self,
        changes: list[ProjectChange],
    ):

        request = (
            self._build_diagnostic_request(
                changes
            )
        )

        print()
        print("=" * 70)
        print(
            "[HARNESS] Change batch detected"
        )

        for change in changes:
            print(
                f"  - {change.event_type}: "
                f"{change.path}"
            )

        print()
        print(
            "[HARNESS] Starting diagnosis..."
        )

        diagnosis = None
        verification = None

        recovery_payload = None
        recovery_success = None
        recovery_executed = False

        final_status = "UNKNOWN"

        try:
            # =================================================
            # 1. OBSERVE / DIAGNOSE
            # =================================================

            diagnosis = asyncio.run(
                run_diagnostic_agent(
                    request
                )
            )

            print()
            print(
                "=== SENTINEL DIAGNOSIS ==="
            )

            print(
                f"Status : {diagnosis.status}"
            )

            print()
            print("Evidence:")
            print(
                diagnosis.evidence
            )

            print()
            print("Diagnosis:")
            print(
                diagnosis.diagnosis
            )

            print()
            print(
                "Recommended action: "
                f"{diagnosis.recommended_action}"
            )

            action = (
                diagnosis.recommended_action
            )

            # =================================================
            # 2. DECIDE
            # =================================================

            if action == "none":

                print()
                print(
                    "[HARNESS] "
                    "No recovery action required."
                )

                if (
                    diagnosis.status
                    == "HEALTHY"
                ):
                    final_status = "HEALTHY"
                else:
                    final_status = (
                        "NO_AUTO_ACTION"
                    )

            elif not is_safe_action(
                action
            ):

                print()
                print(
                    f"[HARNESS] Action "
                    f"'{action}' is not approved "
                    "for automatic execution."
                )

                print(
                    "[HARNESS] "
                    "Human review required."
                )

                final_status = (
                    "HUMAN_REVIEW"
                )

            else:

                print()
                print(
                    "[HARNESS] "
                    f"Safe recovery approved: "
                    f"{action}"
                )

                # =============================================
                # 3. ACT
                # =============================================

                recovery_result = asyncio.run(
                    execute_recovery_action(
                        action
                    )
                )

                recovery_executed = True

                (
                    recovery_success,
                    recovery_payload,
                ) = (
                    self._extract_recovery_result(
                        recovery_result
                    )
                )

                print()
                print(
                    "[HARNESS] "
                    "Recovery action executed."
                )

                print(
                    f"[HARNESS] "
                    f"Tool success: "
                    f"{recovery_success}"
                )

                # =============================================
                # 4. VERIFY
                # =============================================

                if recovery_success:

                    print()
                    print(
                        "[HARNESS] Starting "
                        "post-recovery "
                        "verification..."
                    )

                    verification = (
                        asyncio.run(
                            self._verify_recovery()
                        )
                    )

                    print()
                    print(
                        "=== RECOVERY "
                        "VERIFICATION ==="
                    )

                    print(
                        f"Status : "
                        f"{verification.status}"
                    )

                    print()
                    print("Evidence:")
                    print(
                        verification.evidence
                    )

                    print()
                    print("Diagnosis:")
                    print(
                        verification.diagnosis
                    )

                    # =========================================
                    # 5. CLOSED LOOP RESULT
                    # =========================================

                    if (
                        recovery_success
                        and
                        verification.status
                        == "HEALTHY"
                    ):

                        final_status = (
                            "AUTO-RECOVERED"
                        )

                        print()
                        print(
                            "======================"
                            "============"
                        )
                        print(
                            "STATUS: "
                            "AUTO-RECOVERED"
                        )
                        print(
                            "======================"
                            "============"
                        )

                    else:

                        final_status = (
                            "RECOVERY_FAILED"
                        )

                else:

                    final_status = (
                        "RECOVERY_FAILED"
                    )

                    print()
                    print(
                        "======================"
                        "============"
                    )
                    print(
                        "STATUS: "
                        "RECOVERY FAILED"
                    )
                    print(
                        "======================"
                        "============"
                    )

        except Exception as exc:

            final_status = "ERROR"

            print()
            print(
                "[HARNESS] "
                "Agent/recovery cycle failed:"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )

        # ====================================================
        # 6. PERSIST REPORT
        # ====================================================

        report = {
            "project":
                self.config.project_name,

            "changes":
                self._serialize_changes(
                    changes
                ),

            "diagnosis":
                (
                    diagnosis.model_dump()
                    if diagnosis
                    else {}
                ),

            "recovery":
                (
                    {
                        "action":
                            diagnosis.recommended_action,
                        "executed":
                            recovery_executed,
                        "success":
                            recovery_success,
                        "result":
                            recovery_payload,
                    }
                    if diagnosis
                    and diagnosis.recommended_action
                    != "none"
                    else None
                ),

            "verification":
                (
                    verification.model_dump()
                    if verification
                    else None
                ),

            "final_status":
                final_status,
        }

        json_path, md_path = (
            self.reporter.write(
                report
            )
        )

        print()
        print(
            f"[REPORT] JSON : "
            f"{json_path}"
        )

        print(
            f"[REPORT] MD   : "
            f"{md_path}"
        )

        print()
        print(
            "[HARNESS] Returning to WATCHING"
        )

        print("=" * 70)

    # ========================================================
    # Always-on loop
    # ========================================================

    def run_forever(self):

        self.watcher.start()

        try:
            while True:

                try:
                    first_change = (
                        self.event_queue.get(
                            timeout=1.0
                        )
                    )

                except Empty:
                    continue

                changes = (
                    self._collect_changes(
                        first_change
                    )
                )

                self._run_agent(
                    changes
                )

        except KeyboardInterrupt:

            print()
            print(
                "[HARNESS] "
                "Shutdown requested."
            )

        finally:

            self.watcher.stop()

            print(
                "[HARNESS] "
                "Project Sentinel stopped."
            )
