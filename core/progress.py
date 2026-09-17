from __future__ import annotations

import sys
import time
from typing import TextIO


def _duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def _bar(done: int, total: int, width: int = 24) -> str:
    ratio = min(1.0, done / max(1, total))
    filled = int(width * ratio)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


class ProgressReporter:
    """Single-line CMD progress display for collection and scanning."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout
        self.started = time.monotonic()
        self.completed = self.success = self.saved = self.errors = 0
        self.total = 0
        self._last_length = 0

    def _write(self, text: str, finish: bool = False) -> None:
        padded = text.ljust(self._last_length)
        self.stream.write("\r" + padded + ("\n" if finish else ""))
        self.stream.flush()
        self._last_length = 0 if finish else len(text)

    def collection(self, completed_sources: int, total_sources: int, raw_candidates: int, target: int) -> None:
        elapsed = time.monotonic() - self.started
        eta = (elapsed / completed_sources * (total_sources - completed_sources)) if completed_sources else None
        percent = completed_sources / max(1, total_sources) * 100
        self._write(
            f"[COLLECT] {_bar(completed_sources, total_sources)} {percent:5.1f}% "
            f"Sources {completed_sources}/{total_sources} | Raw {raw_candidates:,} | "
            f"Target {target:,} | Elapsed {_duration(elapsed)} | ETA {_duration(eta)}",
            finish=completed_sources >= total_sources,
        )

    def start_scan(self, total: int) -> None:
        self.started = time.monotonic()
        self.completed = self.success = self.saved = self.errors = 0
        self.total = total
        self._write(
            f"[SCAN] {_bar(0, total)}   0.0% 0/{total:,} | OK 0 | Saved 0 | Errors 0 | "
            f"Elapsed 00:00 | ETA --:--",
            finish=total == 0,
        )

    def scan(self, http_status: int, written: bool, error: str = "") -> None:
        self.completed += 1
        self.success += int(200 <= http_status < 400)
        self.saved += int(written)
        self.errors += int(bool(error) or not http_status)
        elapsed = time.monotonic() - self.started
        eta = elapsed / self.completed * (self.total - self.completed) if self.completed else None
        percent = self.completed / max(1, self.total) * 100
        self._write(
            f"[SCAN] {_bar(self.completed, self.total)} {percent:5.1f}% "
            f"{self.completed:,}/{self.total:,} | OK {self.success:,} | Saved {self.saved:,} | "
            f"Errors {self.errors:,} | Elapsed {_duration(elapsed)} | ETA {_duration(eta)}",
            finish=self.completed >= self.total,
        )
