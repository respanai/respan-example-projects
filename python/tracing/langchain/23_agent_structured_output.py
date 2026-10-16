"""Agent structured output."""

from _shared import init_telemetry, make_openai_chat_model, tracing_config
from langchain.agents import create_agent
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information extracted from text."""

    name: str = Field(description="Person name")
    email: str = Field(description="Email address")


def agent_structured_output() -> None:
    init_telemetry("langchain-agent-structured-output")
    model = make_openai_chat_model()
    if model is None:
        print(
            "Set OPENAI_API_KEY or RESPAN_API_KEY to run this provider-backed example."
        )
        return

    agent = create_agent(
        model=model,
        tools=[],
        response_format=ContactInfo,
    )
    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Extract contact info: Ada Lovelace, ada@example.com",
                }
            ]
        },
        config=tracing_config("agent_structured_output"),
    )
    print(response["structured_response"])


if __name__ == "__main__":
    agent_structured_output()
