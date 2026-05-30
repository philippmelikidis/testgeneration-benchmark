"""Lightweight progress reporting shared by the orchestrator and all pipelines.

A run is split into weighted *phases* (e.g. generate/execute/judge per pipeline).
Each phase reports an intra-phase fraction in [0, 1] plus log messages; the
:class:`Progress` object turns that into a single overall percentage. Pipelines
depend only on the small :class:`Phase` handle, so they stay decoupled from how
progress is surfaced (UI, job file, plain logging).
"""

from __future__ import annotations

from typing import Callable, Optional

# sink(percent_or_None, message): percent is the overall fraction in [0, 1];
# None means "log line only, percentage unchanged".
Sink = Callable[[Optional[float], str], None]


class Phase:
    def __init__(self, progress: "Progress", weight: float, label: str):
        self._p = progress
        self.weight = weight
        self.label = label

    def update(self, frac: float, message: str | None = None) -> None:
        """Report intra-phase progress (0..1) with an optional log message."""
        self._p._update(self, frac, message)

    def log(self, message: str) -> None:
        """Emit a log line without moving the percentage."""
        self._p._log(message)


class NullPhase(Phase):
    """No-op phase so pipelines can run without a reporter."""

    def __init__(self) -> None:  # noqa: D107
        pass

    def update(self, frac: float, message: str | None = None) -> None:
        return None

    def log(self, message: str) -> None:
        return None


class Progress:
    def __init__(self, total_weight: float, sink: Sink):
        self.total = max(total_weight, 1e-9)
        self.sink = sink
        self._done = 0.0
        self._current: Phase | None = None

    def phase(self, weight: float, label: str) -> Phase:
        """Open a new phase, closing the previous one as fully complete."""
        if self._current is not None:
            self._done += self._current.weight
        self._current = Phase(self, weight, label)
        self._emit(self._overall(0.0), label)
        return self._current

    def finish(self, message: str = "fertig") -> None:
        if self._current is not None:
            self._done += self._current.weight
            self._current = None
        self.sink(1.0, message)

    # -- internal -------------------------------------------------------- #
    def _update(self, phase: Phase, frac: float, message: str | None) -> None:
        self.sink(self._overall(frac, phase), message or phase.label)

    def _log(self, message: str) -> None:
        self.sink(None, message)

    def _overall(self, frac: float, phase: Phase | None = None) -> float:
        phase = phase or self._current
        w = phase.weight if phase else 0.0
        frac = min(max(frac, 0.0), 1.0)
        return min((self._done + w * frac) / self.total, 1.0)

    def _emit(self, pct: float, message: str) -> None:
        self.sink(pct, message)
