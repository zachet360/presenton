"""Accumulates detailed step-by-step logs during presentation generation."""

import time
from datetime import datetime, timezone
from typing import Any, Optional


def _safe_json(obj: Any, max_str_len: int = 50_000) -> Any:
    """Make an object JSON-serialisable, truncating very long strings."""
    if obj is None:
        return None
    if isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return obj[:max_str_len] + "…" if len(obj) > max_str_len else obj
    if isinstance(obj, bytes):
        return f"<{len(obj)} bytes>"
    if isinstance(obj, dict):
        return {str(k): _safe_json(v, max_str_len) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json(v, max_str_len) for v in obj]
    return str(obj)


class GenerationLogger:
    def __init__(self, filename: str):
        self.filename = filename
        self.steps: list[dict] = []
        self.started_at = datetime.now(timezone.utc)
        self._step_start: Optional[float] = None
        self._step_name: Optional[str] = None

    def begin(self, name: str, **input_data: Any):
        """Start a new step. Automatically closes the previous one if open."""
        if self._step_name is not None:
            self.end()
        self._step_name = name
        self._step_start = time.monotonic()
        self.steps.append({
            "name": name,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": None,
            "input": _safe_json(input_data) if input_data else None,
            "output": None,
            "error": None,
        })

    def end(self, **output_data: Any):
        """Close the current step, recording duration and output."""
        if self._step_start is not None:
            step = self.steps[-1]
            step["duration_ms"] = round((time.monotonic() - self._step_start) * 1000)
            if output_data:
                step["output"] = _safe_json(output_data)
            self._step_start = None
            self._step_name = None

    def end_with_error(self, error: str):
        """Close the current step with an error."""
        if self._step_start is not None:
            step = self.steps[-1]
            step["duration_ms"] = round((time.monotonic() - self._step_start) * 1000)
            step["error"] = error
            self._step_start = None
            self._step_name = None

    def add_substep(self, parent_name: str, substep_data: dict):
        """Add a substep entry to the most recent step matching parent_name."""
        for step in reversed(self.steps):
            if step["name"] == parent_name:
                if "substeps" not in step:
                    step["substeps"] = []
                step["substeps"].append(_safe_json(substep_data))
                return

    def total_duration_ms(self) -> int:
        elapsed = datetime.now(timezone.utc) - self.started_at
        return round(elapsed.total_seconds() * 1000)

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "started_at": self.started_at.isoformat(),
            "total_duration_ms": self.total_duration_ms(),
            "steps": self.steps,
        }
