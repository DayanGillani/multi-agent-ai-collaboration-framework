"""
Agent definitions.

Design decision: every Agent wraps a "handler" — a plain callable with
signature (input_text, prior_messages) -> str — rather than hard-coding a
call to a specific LLM provider inside the class. This is the same
dependency-injection pattern used in the CRM project's prompt/response
split: it means the orchestration logic (how agents hand work to each
other, how critique loops work, how many retries are allowed) can be
fully unit tested with fast, deterministic fake handlers, completely
independent of whether the "thinking" behind each handler is a real LLM
call, a rule-based function, or a canned response for a demo.

Swapping a fake handler for a real LLM call is a one-line change at the
call site — nothing in Agent, Coordinator, or the tests needs to know the
difference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .message import AgentMessage


class AgentHandler(Protocol):
    """Signature every agent's underlying "thinking" function must match."""

    def __call__(self, input_text: str, prior_messages: list[AgentMessage]) -> str:
        ...


@dataclass
class Agent:
    """A single specialized participant in the multi-agent pipeline.

    Attributes:
        name: Unique identifier for this agent (e.g. "researcher").
        role_description: Human-readable description of what this agent
            does — used in logging/demo output, not by the routing logic.
        handler: The function that actually produces this agent's output
            given input text and prior conversation context.
    """

    name: str
    role_description: str
    handler: Callable[[str, list[AgentMessage]], str]

    def run(self, input_text: str, prior_messages: list[AgentMessage]) -> str:
        """Execute this agent's handler and return its raw output.

        Kept as a thin wrapper (rather than calling self.handler directly
        everywhere) so validation or logging can be added here later
        without touching every call site.
        """
        if not input_text or not input_text.strip():
            raise ValueError(f"Agent '{self.name}' received empty input_text")
        return self.handler(input_text, prior_messages)


def make_research_agent(handler: Callable[[str, list[AgentMessage]], str]) -> Agent:
    """Factory for a research agent: gathers relevant information for a task."""
    return Agent(
        name="researcher",
        role_description="Gathers background information relevant to the task.",
        handler=handler,
    )


def make_planner_agent(handler: Callable[[str, list[AgentMessage]], str]) -> Agent:
    """Factory for a planner agent: turns research into a structured plan."""
    return Agent(
        name="planner",
        role_description="Turns research findings into a structured plan or outline.",
        handler=handler,
    )


def make_writer_agent(handler: Callable[[str, list[AgentMessage]], str]) -> Agent:
    """Factory for a writer agent: produces the actual deliverable."""
    return Agent(
        name="writer",
        role_description="Produces the deliverable content from the plan.",
        handler=handler,
    )


def make_critic_agent(handler: Callable[[str, list[AgentMessage]], str]) -> Agent:
    """Factory for a critic agent: reviews output and gives feedback.

    Convention: the critic's handler should return either the literal
    string "APPROVED" (nothing to change) or a feedback string describing
    what to revise. The Coordinator checks for that exact string — see
    coordinator.py for why this simple convention was chosen over parsing
    free-form critique text for a verdict.
    """
    return Agent(
        name="critic",
        role_description="Reviews the writer's output and either approves it or requests changes.",
        handler=handler,
    )


def make_validator_agent(handler: Callable[[str, list[AgentMessage]], str]) -> Agent:
    """Factory for a validator agent: final structural/quality check.

    Same APPROVED / feedback convention as the critic agent, but intended
    to run after critique passes — checking things like completeness or
    format compliance rather than content quality.
    """
    return Agent(
        name="validator",
        role_description="Performs a final structural check before task completion.",
        handler=handler,
    )
