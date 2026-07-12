import pytest

from src.agent import (
    Agent,
    make_critic_agent,
    make_planner_agent,
    make_research_agent,
    make_validator_agent,
    make_writer_agent,
)


def echo_handler(input_text, prior_messages):
    return f"echo: {input_text}"


def test_agent_run_calls_handler():
    agent = Agent(name="test", role_description="testing", handler=echo_handler)
    result = agent.run("hello", [])
    assert result == "echo: hello"


def test_agent_run_rejects_empty_input():
    agent = Agent(name="test", role_description="testing", handler=echo_handler)
    with pytest.raises(ValueError):
        agent.run("   ", [])


def test_agent_run_passes_prior_messages_through():
    captured = {}

    def capturing_handler(input_text, prior_messages):
        captured["count"] = len(prior_messages)
        return "ok"

    agent = Agent(name="test", role_description="testing", handler=capturing_handler)
    agent.run("input", [1, 2, 3])  # type: ignore[list-item]
    assert captured["count"] == 3


def test_research_agent_factory_sets_correct_name():
    agent = make_research_agent(echo_handler)
    assert agent.name == "researcher"


def test_planner_agent_factory_sets_correct_name():
    agent = make_planner_agent(echo_handler)
    assert agent.name == "planner"


def test_writer_agent_factory_sets_correct_name():
    agent = make_writer_agent(echo_handler)
    assert agent.name == "writer"


def test_critic_agent_factory_sets_correct_name():
    agent = make_critic_agent(echo_handler)
    assert agent.name == "critic"


def test_validator_agent_factory_sets_correct_name():
    agent = make_validator_agent(echo_handler)
    assert agent.name == "validator"
