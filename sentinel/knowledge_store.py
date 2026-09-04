from datetime import datetime
from pathlib import Path


def append_recovered_incident(
    knowledge_file: str | Path,
    diagnosis,
    action: str,
    verification,
) -> Path:
    """
    Persist a verified auto-recovery incident as reusable RAG knowledge.

    Only call this after recovery execution succeeded AND
    post-recovery verification returned HEALTHY.
    """

    knowledge_file = Path(
        knowledge_file
    ).resolve()

    knowledge_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    now = datetime.now().astimezone()

    section = f"""

## Auto-Recovered Incident - {now.isoformat()}

### Symptom

Status: {diagnosis.status}

{diagnosis.evidence}

### Diagnosis

{diagnosis.diagnosis}

### Recovery

Action: {action}

### Verification

Status: {verification.status}

{verification.evidence}

### Result

AUTO-RECOVERED
"""

    with knowledge_file.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(section)

    return knowledge_file
