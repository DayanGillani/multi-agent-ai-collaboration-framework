import pytest

from src.message import AgentMessage, MessageType
from src.task import Task, TaskStatus


def test_agent_message_requires_content():
    with pytest.raises(ValueError):
        AgentMessage(
            task_id="t1",
            from_agent="a",
            to_agent="b",
            message_type=MessageType.REQUEST,
            content="   ",
        )


def test_agent_message_generates_unique_ids():
    msg1 = AgentMessage(task_id="t1", from_agent="a", to_agent="b", message_type=MessageType.REQUEST, content="hi")
    msg2 = AgentMessage(task_id="t1", from_agent="a", to_agent="b", message_type=MessageType.REQUEST, content="hi")
    assert msg1.message_id != msg2.message_id


def test_task_requires_description():
    with pytest.raises(ValueError):
        Task(description="")


def test_task_starts_pending():
    task = Task(description="do something")
    assert task.status == TaskStatus.PENDING


def test_task_mark_in_progress():
    task = Task(description="do something")
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_task_mark_needs_revision_increments_count():
    task = Task(description="do something")
    task.mark_needs_revision("draft output")
    assert task.status == TaskStatus.NEEDS_REVISION
    assert task.revision_count == 1
    assert task.current_output == "draft output"

    task.mark_needs_revision("second draft")
    assert task.revision_count == 2


def test_task_mark_completed():
    task = Task(description="do something")
    task.mark_completed("final output")
    assert task.status == TaskStatus.COMPLETED
    assert task.current_output == "final output"


def test_task_mark_failed():
    task = Task(description="do something")
    task.mark_failed()
    assert task.status == TaskStatus.FAILED


def test_each_task_has_unique_id():
    task1 = Task(description="one")
    task2 = Task(description="two")
    assert task1.task_id != task2.task_id
