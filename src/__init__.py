"""Multi-Agent AI Collaboration Framework — core package."""

from .agent import (
    Agent,
    make_critic_agent,
    make_planner_agent,
    make_research_agent,
    make_validator_agent,
    make_writer_agent,
)
from .coordinator import Coordinator, WorkflowResult
from .message import AgentMessage, MessageType
from .task import Task, TaskStatus

__all__ = [
    "Agent",
    "make_research_agent",
    "make_planner_agent",
    "make_writer_agent",
    "make_critic_agent",
    "make_validator_agent",
    "Coordinator",
    "WorkflowResult",
    "AgentMessage",
    "MessageType",
    "Task",
    "TaskStatus",
]
