"""ADK2.11 tool-node confirmation pauses before execution, then resumes."""

from _shared import APP_USER_ID, make_runner, make_user_message, run_scenario
from google.adk.tools import FunctionTool
from google.adk.workflow import START, Workflow, node
from google.adk.workflow.utils._workflow_hitl_utils import create_request_input_response
from google.genai import types


async def scenario():
    executed = []

    def greet(name: str) -> dict:
        """Return a deterministic greeting."""
        executed.append(name)
        return {"greeting": "hello " + name}

    target = node(FunctionTool(greet, require_confirmation=True))
    runner, session = await make_runner(
        node=Workflow(name="confirm_workflow", edges=[(START, target)])
    )
    events = [
        event
        async for event in runner.run_async(
            user_id=APP_USER_ID,
            session_id=session.id,
            new_message=make_user_message('{"name":"Ada"}'),
        )
    ]
    assert not executed
    request = next(call for event in events for call in event.get_function_calls())
    response = types.Content(
        role="user",
        parts=[create_request_input_response(request.id, {"confirmed": True})],
    )
    resumed = [
        event
        async for event in runner.run_async(
            user_id=APP_USER_ID, session_id=session.id, new_message=response
        )
    ]
    assert executed == ["Ada"]
    return {
        "executions": len(executed),
        "outputs": [event.output for event in resumed if event.output is not None],
    }


if __name__ == "__main__":
    run_scenario("07_workflow_confirmation", scenario)
