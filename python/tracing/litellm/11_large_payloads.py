"""Complete large arrays and sensitive-named schema definitions."""

import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
import copy
import json

import httpx
import litellm
from _fixtures import TOOLS, client
from _shared import MODE, create_respan, run_with_example_attributes
from respan import workflow

WORKFLOW_NAME = "litellm_large_payloads.workflow"


@workflow(name=WORKFLOW_NAME)
def run():
    tools = copy.deepcopy(TOOLS)
    tools[0]["function"]["parameters"]["properties"]["api_key"] = {
        "type": "string",
        "default": "fixture-default-secret",
        "examples": ["fixture-example-secret"],
    }
    native = client(tools=True)
    original = native._client._transport.handler

    def large(request):
        response = original(request)
        body = response.json()
        body["choices"] = [
            {
                "index": i,
                "message": {"role": "assistant", "content": f"choice-{i}"},
                "finish_reason": "stop",
            }
            for i in range(150)
        ]
        body["choices"][0]["message"]["tool_calls"] = [
            {
                "id": "large-current-call-id",
                "type": "function",
                "function": {
                    "name": "lookup",
                    "arguments": json.dumps(
                        {
                            "api_key": "fixture-argument-secret",
                            "content": 'Bearer fixture-token"quoted" value',
                            "basic_content": 'Basic fixture-token"quoted" value',
                        }
                    ),
                },
            }
        ]
        return httpx.Response(200, json=body)

    native._client._transport.handler = large
    response = litellm.completion(
        model="openai/fixture-model",
        messages=[{"role": "user", "content": f"message-{i}"} for i in range(150)],
        tools=tools,
        client=native,
    )
    assert len(response.choices) == 150
    assert (
        json.loads(response.choices[0].message.tool_calls[0].function.arguments)[
            "api_key"
        ]
        == "fixture-argument-secret"
    )
    return {
        "source_messages": 150,
        "source_choices": 150,
        "tool_schema_properties": 101,
    }


def main():
    if MODE != "fixture":
        print("SKIP: large payload/schema fixtures use controlled provider bodies")
        return
    respan = create_respan("litellm-large-payloads")
    try:
        print(
            run_with_example_attributes(respan, workflow_name=WORKFLOW_NAME, action=run)
        )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
