import json
from datetime import datetime
from pathlib import Path
from typing import Any


class SentinelReportWriter:
    def __init__(
        self,
        report_dir: str | Path,
    ):
        self.report_dir = Path(report_dir).resolve()

        self.report_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(
        self,
        report: dict[str, Any],
    ) -> tuple[Path, Path]:

        now = datetime.now().astimezone()

        run_id = now.strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        report["run_id"] = run_id
        report["timestamp"] = now.isoformat()

        json_path = (
            self.report_dir
            / f"{run_id}.json"
        )

        md_path = (
            self.report_dir
            / f"{run_id}.md"
        )

        # ----------------------------------------
        # JSON trace
        # ----------------------------------------

        json_path.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------
        # Human-readable Markdown report
        # ----------------------------------------

        markdown = self._to_markdown(
            report
        )

        md_path.write_text(
            markdown,
            encoding="utf-8",
        )

        return json_path, md_path

    def _to_markdown(
        self,
        report: dict[str, Any],
    ) -> str:

        lines: list[str] = []

        lines.append("# Project Sentinel Report")
        lines.append("")
        lines.append(
            f"- Run ID: `{report['run_id']}`"
        )
        lines.append(
            f"- Timestamp: `{report['timestamp']}`"
        )
        lines.append(
            f"- Project: `{report.get('project', '')}`"
        )
        lines.append(
            f"- Final Status: **{report.get('final_status', '')}**"
        )

        # ----------------------------------------
        # Changes
        # ----------------------------------------

        lines.append("")
        lines.append("## Detected Changes")
        lines.append("")

        changes = report.get(
            "changes",
            [],
        )

        if changes:
            for change in changes:
                lines.append(
                    f"- `{change['event_type']}` "
                    f"`{change['path']}`"
                )
        else:
            lines.append(
                "No source changes recorded."
            )

        # ----------------------------------------
        # Diagnosis
        # ----------------------------------------

        diagnosis = report.get(
            "diagnosis",
            {},
        )

        lines.append("")
        lines.append("## Diagnosis")
        lines.append("")

        lines.append(
            f"**Status:** "
            f"`{diagnosis.get('status', '')}`"
        )

        lines.append("")
        lines.append("### Evidence")
        lines.append("")
        lines.append(
            diagnosis.get(
                "evidence",
                "",
            )
        )

        lines.append("")
        lines.append("### Diagnosis")
        lines.append("")
        lines.append(
            diagnosis.get(
                "diagnosis",
                "",
            )
        )

        lines.append("")
        lines.append(
            "### Recommended Action"
        )
        lines.append("")
        lines.append(
            f"`{diagnosis.get('recommended_action', '')}`"
        )

        # ----------------------------------------
        # Recovery
        # ----------------------------------------

        recovery = report.get(
            "recovery",
        )

        if recovery:

            lines.append("")
            lines.append("## Recovery")
            lines.append("")

            lines.append(
                f"- Action: "
                f"`{recovery.get('action', '')}`"
            )

            lines.append(
                f"- Executed: "
                f"`{recovery.get('executed', False)}`"
            )

            lines.append(
                f"- Tool Success: "
                f"`{recovery.get('success', False)}`"
            )

        # ----------------------------------------
        # Verification
        # ----------------------------------------

        verification = report.get(
            "verification",
        )

        if verification:

            lines.append("")
            lines.append(
                "## Post-Recovery Verification"
            )
            lines.append("")

            lines.append(
                f"**Status:** "
                f"`{verification.get('status', '')}`"
            )

            lines.append("")
            lines.append("### Evidence")
            lines.append("")
            lines.append(
                verification.get(
                    "evidence",
                    "",
                )
            )

            lines.append("")
            lines.append("### Diagnosis")
            lines.append("")
            lines.append(
                verification.get(
                    "diagnosis",
                    "",
                )
            )

        lines.append("")

        return "\n".join(lines)
