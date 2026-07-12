"""
Coordinator — task orchestration and workflow routing.

Design decision: the pipeline is a fixed sequence (research -> plan ->
write -> critique -> validate), not a dynamically-decided agent graph
where an LLM chooses what to call next. A dynamic router is a reasonable
future extension, but it trades away predictability and testability for
flexibility that this project doesn't yet need. A fixed pipeline with an
explicit critique/revision loop is fully deterministic given its inputs,
which is what makes the test suite for this module possible without
mocking an LLM's routing decisions.

The critique loop specifically: after the writer produces output, the
critic reviews it. If the critic's handler returns the exact string
"APPROVED", the task proceeds to validation. Otherwise, the critic's
response is treated as revision feedback, sent back to the writer, and
the cycle repeats — up to max_revisions times, after which the task is
marked FAILED rather than looping forever. This bounded-retry design is
the concrete answer to "how do you stop an agent conversation that
disagrees with itself indefinitely."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .agent import Agent
from .message import AgentMessage, MessageType
from .task import Task, TaskStatus

APPROVED_MARKER = "APPROVED"


@dataclass
class WorkflowResult:
    """Final outcome of running a task through the pipeline."""

    task: Task
    messages: list[AgentMessage]

    @property
    def succeeded(self) -> bool:
        return self.task.status == TaskStatus.COMPLETED


class Coordinator:
    """Orchestrates a fixed research -> plan -> write -> critique -> validate pipeline."""

    def __init__(
        self,
        researcher: Agent,
        planner: Agent,
        writer: Agent,
        critic: Agent,
        validator: Agent,
        max_revisions: int = 3,
    ) -> None:
        """
        Args:
            researcher, planner, writer, critic, validator: the five
                pipeline agents. Passed explicitly (not looked up by
                name from a registry) so a misconfigured pipeline is a
                constructor-time type error, not a runtime KeyError.
            max_revisions: How many critique/revision cycles are allowed
                before the task is marked FAILED instead of looping
                indefinitely.
        """
        self._researcher = researcher
        self._planner = planner
        self._writer = writer
        self._critic = critic
        self._validator = validator
        self._max_revisions = max_revisions

    def run(self, description: str) -> WorkflowResult:
        """Run a new task through the full pipeline.

        Args:
            description: What the task asks for.

        Returns:
            A WorkflowResult containing the final Task state and the full
            message log for the run.
        """
        task = Task(description=description)
        messages: list[AgentMessage] = []
        task.mark_in_progress()

        research_output = self._call_agent(self._researcher, task.description, messages, task.task_id)
        plan_output = self._call_agent(self._planner, research_output, messages, task.task_id)
        writer_output = self._call_agent(self._writer, plan_output, messages, task.task_id)

        approved = self._run_critique_loop(task, writer_output, messages)
        if not approved:
            task.mark_failed()
            return WorkflowResult(task=task, messages=messages)

        validation_output = self._call_agent(
            self._validator, task.current_output, messages, task.task_id
        )
        if validation_output.strip() == APPROVED_MARKER:
            task.mark_completed(task.current_output)
        else:
            # Validator rejection is treated as terminal, not a further
            # revision cycle — validation is meant to catch structural
            # issues after content has already been critique-approved,
            # not to open a second negotiation loop.
            task.mark_failed()

        return WorkflowResult(task=task, messages=messages)

    def _run_critique_loop(
        self, task: Task, initial_output: str, messages: list[AgentMessage]
    ) -> bool:
        """Runs the critic/writer revision cycle. Returns True if approved."""
        current_output = initial_output
        task.current_output = current_output

        for _ in range(self._max_revisions + 1):
            critique = self._call_agent(self._critic, current_output, messages, task.task_id)

            if critique.strip() == APPROVED_MARKER:
                task.current_output = current_output
                return True

            if task.revision_count >= self._max_revisions:
                return False

            task.mark_needs_revision(current_output)
            revision_input = (
                f"Original output:\n{current_output}\n\n"
                f"Critic feedback:\n{critique}\n\n"
                "Please revise based on this feedback."
            )
            current_output = self._call_agent(self._writer, revision_input, messages, task.task_id)

        return False

    def _call_agent(
        self,
        agent: Agent,
        input_text: str,
        messages: list[AgentMessage],
        task_id: str,
    ) -> str:
        """Runs one agent, logging the request and response as messages."""
        request_msg = AgentMessage(
            task_id=task_id,
            from_agent="coordinator",
            to_agent=agent.name,
            message_type=MessageType.REQUEST,
            content=input_text,
        )
        messages.append(request_msg)

        output = agent.run(input_text, messages)

        response_msg = AgentMessage(
            task_id=task_id,
            from_agent=agent.name,
            to_agent="coordinator",
            message_type=MessageType.RESPONSE,
            content=output,
        )
        messages.append(response_msg)

        return output
