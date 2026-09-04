from dataclasses import dataclass
from pathlib import Path
from queue import Queue
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from sentinel.config import SentinelConfig


@dataclass(frozen=True)
class ProjectChange:
    event_type: str
    path: Path
    timestamp: float


class ProjectEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        config: SentinelConfig,
        event_queue: Queue,
    ):
        self.config = config
        self.event_queue = event_queue

    def _is_relevant(self, path_str: str) -> bool:
        path = Path(path_str)

        try:
            relative_path = path.resolve().relative_to(
                self.config.project_path
            )
        except ValueError:
            return False

        for part in relative_path.parts:
            if part in self.config.ignore_dirs:
                return False

        return (
            path.suffix.lower()
            in self.config.watch_extensions
        )

    def _emit(
        self,
        event_type: str,
        path_str: str,
    ):
        if not self._is_relevant(path_str):
            return

        path = Path(path_str).resolve()

        change = ProjectChange(
            event_type=event_type,
            path=path,
            timestamp=time.time(),
        )

        self.event_queue.put(change)

        print(
            f"[WATCHER] {event_type}: {path}"
        )

    def on_modified(self, event):
        if not event.is_directory:
            self._emit(
                "modified",
                event.src_path,
            )

    def on_created(self, event):
        if not event.is_directory:
            self._emit(
                "created",
                event.src_path,
            )

    def on_moved(self, event):
        if not event.is_directory:
            self._emit(
                "moved",
                event.dest_path,
            )


class ProjectWatcher:
    def __init__(
        self,
        config: SentinelConfig,
        event_queue: Queue,
    ):
        self.config = config

        self.observer = Observer()

        self.handler = ProjectEventHandler(
            config,
            event_queue,
        )

    def start(self):
        self.observer.schedule(
            self.handler,
            str(self.config.project_path),
            recursive=True,
        )

        self.observer.start()

        print()
        print("=== Project Sentinel Watcher ===")
        print(
            f"Watching : {self.config.project_path}"
        )
        print("Status   : WATCHING")
        print()

    def stop(self):
        self.observer.stop()
        self.observer.join()
