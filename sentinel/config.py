import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SentinelConfig:
    project_name: str
    project_path: Path
    build_dir: Path

    configure_command: list[str]
    build_command: list[str]
    test_command: list[str]

    watch_extensions: tuple[str, ...]
    ignore_dirs: tuple[str, ...]

    debounce_seconds: float
    command_timeout_seconds: float
    
def load_config(config_path: str | Path) -> SentinelConfig:
    config_path = Path(config_path).expanduser().resolve()

    with config_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    project_path = Path(raw["project_path"]).expanduser().resolve()

    if not project_path.exists():
        raise FileNotFoundError(
            f"Target project does not exist: {project_path}"
        )

    if not project_path.is_dir():
        raise NotADirectoryError(
            f"Target project path is not a directory: {project_path}"
        )

    build_dir = project_path / raw["build_dir"]

    return SentinelConfig(
    project_name=raw["project_name"],
    project_path=project_path,
    build_dir=build_dir,

    configure_command=list(raw["configure_command"]),
    build_command=list(raw["build_command"]),
    test_command=list(raw["test_command"]),

    watch_extensions=tuple(raw["watch_extensions"]),
    ignore_dirs=tuple(raw["ignore_dirs"]),

    debounce_seconds=float(raw["debounce_seconds"]),
    command_timeout_seconds=float(raw["command_timeout_seconds"]),
)
