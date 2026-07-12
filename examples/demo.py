"""
End-to-end demo of the Multi-Agent AI Collaboration Framework.

Run with:
    python examples/demo.py

Simulates a realistic scenario: the writer's first draft is too short,
the critic rejects it and asks for more detail, the writer revises, and
the critic approves the second draft. This demo intentionally includes a
rejection cycle (not just a first-try success) because that's the actual
interesting behavior this framework exists to coordinate.

As in the CRM project's demo, every agent handler here is a simple
deterministic Python function rather than a real LLM call — this proves
the orchestration logic works without requiring an API key to run.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (
    Coordinator,
    make_critic_agent,
    make_planner_agent,
    make_research_agent,
    make_validator_agent,
    make_writer_agent,
)
from src.coordinator import APPROVED_MARKER

# Tracks how many times the writer has been called, so the demo can
# simulate a first draft that's too short and a revised draft that isn't.
writer_call_count = {"count": 0}


def research_handler(input_text: str, prior_messages) -> str:
    return (
        "Key points found: (1) unit testing catches regressions early, "
        "(2) tests double as documentation, (3) untested code is riskier "
        "to refactor."
    )


def planner_handler(input_text: str, prior_messages) -> str:
    return (
        "Outline: intro on why testing matters -> point on catching "
        "regressions -> point on documentation value -> point on "
        "refactor safety -> short conclusion."
    )


def writer_handler(input_text: str, prior_messages) -> str:
    writer_call_count["count"] += 1
    if writer_call_count["count"] == 1:
        # First draft: deliberately thin, to trigger a critique rejection.
        return "Testing is important because it catches bugs."
    # Revised draft: expanded based on critic feedback.
    return (
        "Unit testing matters for three concrete reasons. First, it "
        "catches regressions before they reach users. Second, well-"
        "written tests double as living documentation of how a system "
        "is meant to behave. Third, a strong test suite makes large "
        "refactors safe instead of risky, since any broken behavior "
        "surfaces immediately."
    )


def critic_handler(input_text: str, prior_messages) -> str:
    if len(input_text) < 100:
        return "This is too brief. Please expand with specific reasons and examples."
    return APPROVED_MARKER


def validator_handler(input_text: str, prior_messages) -> str:
    if "reason" in input_text.lower() or "reasons" in input_text.lower():
        return APPROVED_MARKER
    return "Missing explicit reasoning structure."


def run_demo() -> None:
    print("=" * 70)
    print("MULTI-AGENT AI COLLABORATION FRAMEWORK — END-TO-END DEMO")
    print("=" * 70)

    coordinator = Coordinator(
        researcher=make_research_agent(research_handler),
        planner=make_planner_agent(planner_handler),
        writer=make_writer_agent(writer_handler),
        critic=make_critic_agent(critic_handler),
        validator=make_validator_agent(validator_handler),
        max_revisions=3,
    )

    task_description = "Write a short paragraph about why unit testing matters."
    print(f"\nTask: {task_description}\n")

    result = coordinator.run(task_description)

    print("-" * 70)
    print("MESSAGE LOG")
    print("-" * 70)
    for msg in result.messages:
        preview = msg.content if len(msg.content) <= 90 else msg.content[:87] + "..."
        print(f"[{msg.from_agent:>10} -> {msg.to_agent:<10}] {preview}")

    print("\n" + "-" * 70)
    print("FINAL RESULT")
    print("-" * 70)
    print(f"Status: {result.task.status.value}")
    print(f"Revisions needed: {result.task.revision_count}")
    print(f"Succeeded: {result.succeeded}")
    print(f"\nFinal output:\n{result.task.current_output}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()
