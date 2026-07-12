"""
Task model.

Design decision: a Task tracks its own status and revision count, rather
than the Coordinator inferring state from the message log. This keeps
"what stage is this task at" a cheap, direct read instead of requiring a
scan over every message ever sent for that task — that distinction
matters once a task has gone through several critique/revision cycles and
the message log for it is long.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class TaskStatus(str, Enum):
    """Lifecycle states a task moves through."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    NEEDS_REVISION = "needs_revision"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """A unit of work routed through the agent pipeline.

    Attributes:
        description: What the task asks for, e.g. "Write a short blog
            post about X".
        status: Current lifecycle state.
        current_output: The most recent output produced for this task
            (overwritten on each revision — history lives in the message
            log, not here).
        revision_count: How many times this task has been sent back for
            revision. Used by the Coordinator to enforce a max-retries
            limit and avoid infinite critique loops.
        task_id: Unique identifier, auto-generated.
    """

    description: str
    status: TaskStatus = TaskStatus.PENDING
    current_output: str | None = None
    revision_count: int = 0
    task_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValueError("Task requires a non-empty description")

    def mark_in_progress(self) -> None:
        self.status = TaskStatus.IN_PROGRESS

    def mark_needs_revision(self, feedback_output: str) -> None:
        self.status = TaskStatus.NEEDS_REVISION
        self.current_output = feedback_output
        self.revision_count += 1

    def mark_completed(self, final_output: str) -> None:
        self.status = TaskStatus.COMPLETED
        self.current_output = final_output

    def mark_failed(self) -> None:
        self.status = TaskStatus.FAILED
