import os

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

"""Actual provider vectors plus full tool schemas, IDs and vector results."""
import litellm
from _fixtures import HISTORY, TOOLS, client
from _shared import MODE, create_respan, run_with_example_attributes
from respan import tool, workflow

WORKFLOW_NAME = "litellm_embeddings_tools.workflow"


@tool(name="vector_tool")
def vector_tool():
    return {"vector": [float(i) for i in range(5000)]}


@workflow(name=WORKFLOW_NAME)
def run():
    embedding = litellm.embedding(
        model="openai/fixture-embed", input=["controlled source"], client=client()
    )
    assert len(embedding.data[0]["embedding"]) == 5000
    response = litellm.completion(
        model="openai/fixture-model",
        messages=HISTORY,
        tools=TOOLS,
        client=client(tools=True),
    )
    assert response.choices[0].message.tool_calls[0].id == "current-source-id"
    result = vector_tool()
    assert len(result["vector"]) == 5000
    return {
        "provider_vector_size": 5000,
        "tool_result_size": 5000,
        "tool_call_id": "current-source-id",
    }


def main():
    if MODE != "fixture":
        print("SKIP: embeddings/full-vector fixture uses controlled provider bodies")
        return
    respan = create_respan("litellm-embeddings-tools")
    try:
        print(
            run_with_example_attributes(respan, workflow_name=WORKFLOW_NAME, action=run)
        )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    main()
