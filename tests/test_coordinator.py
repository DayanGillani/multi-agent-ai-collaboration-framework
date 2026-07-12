from src.agent import (
    make_critic_agent,
    make_planner_agent,
    make_research_agent,
    make_validator_agent,
    make_writer_agent,
)
from src.coordinator import APPROVED_MARKER, Coordinator
from src.task import TaskStatus


def build_coordinator(critic_responses, validator_response=APPROVED_MARKER, max_revisions=3):
    """Builds a Coordinator with deterministic fake agents for testing.

    critic_responses: a list of strings the critic returns in sequence
        on successive calls (simulating rejections followed by approval).
    """
    critic_calls = {"count": 0}

    def research_handler(input_text, prior_messages):
        return f"research findings for: {input_text}"

    def planner_handler(input_text, prior_messages):
        return f"plan based on: {input_text}"

    def writer_handler(input_text, prior_messages):
        return f"draft based on: {input_text}"

    def critic_handler(input_text, prior_messages):
        idx = min(critic_calls["count"], len(critic_responses) - 1)
        response = critic_responses[idx]
        critic_calls["count"] += 1
        return response

    def validator_handler(input_text, prior_messages):
        return validator_response

    return Coordinator(
        researcher=make_research_agent(research_handler),
        planner=make_planner_agent(planner_handler),
        writer=make_writer_agent(writer_handler),
        critic=make_critic_agent(critic_handler),
        validator=make_validator_agent(validator_handler),
        max_revisions=max_revisions,
    )


def test_happy_path_completes_on_first_critique_approval():
    coordinator = build_coordinator(critic_responses=[APPROVED_MARKER])
    result = coordinator.run("Write a short article about testing")

    assert result.succeeded is True
    assert result.task.status == TaskStatus.COMPLETED
    assert result.task.revision_count == 0


def test_pipeline_calls_all_five_agents_in_order():
    coordinator = build_coordinator(critic_responses=[APPROVED_MARKER])
    result = coordinator.run("test task")

    agent_sequence = [m.to_agent for m in result.messages if m.from_agent == "coordinator"]
    assert agent_sequence == ["researcher", "planner", "writer", "critic", "validator"]


def test_critique_rejection_triggers_revision_then_succeeds():
    coordinator = build_coordinator(
        critic_responses=["Needs more detail on X", APPROVED_MARKER]
    )
    result = coordinator.run("test task")

    assert result.succeeded is True
    assert result.task.revision_count == 1


def test_exceeding_max_revisions_fails_the_task():
    # Critic never approves — every response is a rejection.
    coordinator = build_coordinator(
        critic_responses=["still not good enough"], max_revisions=2
    )
    result = coordinator.run("test task")

    assert result.succeeded is False
    assert result.task.status == TaskStatus.FAILED
    assert result.task.revision_count == 2


def test_validator_rejection_fails_task_even_after_critique_approval():
    coordinator = build_coordinator(
        critic_responses=[APPROVED_MARKER], validator_response="missing required section"
    )
    result = coordinator.run("test task")

    assert result.succeeded is False
    assert result.task.status == TaskStatus.FAILED


def test_all_messages_share_the_same_task_id():
    coordinator = build_coordinator(critic_responses=[APPROVED_MARKER])
    result = coordinator.run("test task")

    task_ids = {m.task_id for m in result.messages}
    assert task_ids == {result.task.task_id}


def test_revision_input_includes_original_output_and_feedback():
    coordinator = build_coordinator(
        critic_responses=["Please add more examples", APPROVED_MARKER]
    )
    result = coordinator.run("test task")

    writer_requests = [
        m for m in result.messages if m.to_agent == "writer" and m.from_agent == "coordinator"
    ]
    assert len(writer_requests) == 2  # initial write + one revision
    revision_request = writer_requests[1]
    assert "Please add more examples" in revision_request.content
