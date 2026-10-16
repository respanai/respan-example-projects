"""Trace a smolagents ToolCallingAgent run with a function tool."""

from _shared import build_model, build_respan, example_attributes
from respan import workflow
from smolagents import ToolCallingAgent, tool

EXAMPLE_NAME = "tool-calling-agent"
WORKFLOW_NAME = "smolagents_tool_calling_agent_workflow"


@tool
def calculate_invoice_total(unit_price_usd: int, quantity: int) -> str:
    """Calculate an invoice total.

    Args:
        unit_price_usd: Price per item in whole dollars.
        quantity: Number of items.
    """
    total = unit_price_usd * quantity
    return f"{quantity} items at ${unit_price_usd} each cost ${total}."


@workflow(name=WORKFLOW_NAME)
def execute_tool_calling_agent_workflow(prompt: str) -> str:
    agent = ToolCallingAgent(
        tools=[calculate_invoice_total],
        model=build_model("invoice"),
        max_steps=3,
        verbosity_level=0,
    )
    result = agent.run(prompt)
    print(result)
    return str(result)


def run_tool_calling_agent() -> str:
    respan = build_respan(example_name=EXAMPLE_NAME, workflow_name=WORKFLOW_NAME)
    try:
        with example_attributes(EXAMPLE_NAME, WORKFLOW_NAME):
            return execute_tool_calling_agent_workflow(
                "Use the calculate_invoice_total tool for 7 items priced at 9 USD "
                "each, then return only the final total sentence."
            )
    finally:
        respan.shutdown()


if __name__ == "__main__":
    run_tool_calling_agent()
