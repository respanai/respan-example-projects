from __future__ import annotations

from _shared import (
    example_attributes,
    make_client,
    make_custom_identifier,
    make_respan,
    model_name,
    print_result,
    workflow_name,
)
from google.genai import types
from respan import tool, workflow

EXAMPLE_NAME = "tool-calling"


@tool(name="get_weather")
def get_weather(city: str) -> str:
    """Return deterministic weather for a city."""
    return f"Sunny and 22 C in {city}"


@workflow(name=workflow_name(EXAMPLE_NAME))
def _tool_calling_workflow(prompt: str) -> str:
    client = make_client()
    declaration = types.FunctionDeclaration(
        name="get_weather",
        description="Return deterministic weather for a city.",
        parameters_json_schema={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    )
    config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[declaration])],
        temperature=0,
        system_instruction="Use the weather tool when a city forecast is requested.",
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["get_weather"],
            )
        ),
    )
    tool_request = client.models.generate_content(
        model=model_name(),
        contents=prompt,
        config=config,
    )
    function_calls = tool_request.function_calls or []
    if not function_calls:
        raise RuntimeError("Gemini did not request get_weather")

    function_call = function_calls[0]
    weather = get_weather(**dict(function_call.args or {}))
    function_result = types.Content(
        role="user",
        parts=[
            types.Part.from_function_response(
                name=function_call.name or "get_weather",
                response={"result": weather},
            )
        ],
    )
    final_response = client.models.generate_content(
        model=model_name(),
        contents=[
            types.Content(role="user", parts=[types.Part(text=prompt)]),
            tool_request.candidates[0].content,
            function_result,
        ],
        config=types.GenerateContentConfig(temperature=0),
    )
    return final_response.text or ""


def run_tool_calling() -> None:
    respan = make_respan(EXAMPLE_NAME)
    custom_identifier = make_custom_identifier(EXAMPLE_NAME)
    text = ""

    try:
        with example_attributes(EXAMPLE_NAME, custom_identifier):
            print(f"custom_identifier={custom_identifier}", flush=True)
            print(f"workflow_name={workflow_name(EXAMPLE_NAME)}", flush=True)
            text = _tool_calling_workflow(
                "What is the weather in Tokyo? Use the tool and answer briefly."
            )
    finally:
        respan.shutdown()

    print_result(EXAMPLE_NAME, custom_identifier, text)


if __name__ == "__main__":
    run_tool_calling()
