"""
Message model for inter-agent communication.

Design decision: every exchange between agents — a request, a response, a
critique, a rejection — is represented as an AgentMessage, not as a raw
string return value. This is deliberate: it means the full conversation
history for a task is always reconstructable from a flat list of
messages, which is what makes the Coordinator's audit trail (see
coordinator.py) possible without any extra bookkeeping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class MessageType(str, Enum):
    """What kind of exchange this message represents."""

    REQUEST = "request"        # Coordinator -> Agent: do this work
    RESPONSE = "response"      # Agent -> Coordinator: here's the output
    CRITIQUE = "critique"      # Critic agent -> Coordinator: feedback on output
    REJECTION = "rejection"    # Validator/Critic -> Coordinator: this failed
    APPROVAL = "approval"      # Validator/Critic -> Coordinator: this passed


@dataclass
class AgentMessage:
    """A single message exchanged during task execution.

    Attributes:
        task_id: Which task this message belongs to — this is what lets
            the Coordinator reconstruct a full conversation for a single
            task out of a flat message log.
        from_agent: Name of the sending agent (or "coordinator").
        to_agent: Name of the receiving agent (or "coordinator").
        message_type: See MessageType.
        content: The actual text payload.
        message_id: Unique id, auto-generated.
        timestamp: When the message was created.
    """

    task_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: str
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.content or not self.content.strip():
            raise ValueError("AgentMessage requires non-empty content")
