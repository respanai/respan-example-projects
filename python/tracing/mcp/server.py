"""Local MCP stdio server used by the Respan MCP examples."""

import sys

if "--exit-immediately" in sys.argv:
    raise SystemExit(3)

from openinference.instrumentation.mcp import MCPInstrumentor

MCPInstrumentor().instrument()

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("respan-mcp-example-server")


@mcp.tool()
def summarize_city(city: str) -> str:
    return (
        f"{city} is ready for a concise travel brief: include weather, "
        "transport, local highlights, and one practical next step."
    )


@mcp.tool()
def calculate_delivery_total(subtotal: float, tax_rate: float = 0.0875) -> str:
    total = subtotal * (1 + tax_rate)
    return f"{total:.2f}"


@mcp.resource("profile://city/paris")
def paris_profile() -> str:
    return (
        "Paris profile: strong public transit, dense museum coverage, "
        "and reliable cafe options near major rail hubs."
    )


@mcp.resource("profile://city/{city}")
def city_profile(city: str) -> str:
    return f"Profile for {city}: deterministic local MCP resource."


@mcp.prompt(name="city_research_prompt")
def city_research_prompt(city: str) -> str:
    return (
        f"Create a compact research brief for {city}. Include current travel "
        "constraints, local context, and three source questions to verify."
    )


@mcp.tool()
def current_trace_id() -> str:
    from opentelemetry import trace

    context = trace.get_current_span().get_span_context()
    return f"{context.trace_id:032x}" if context.is_valid else ""


if __name__ == "__main__":
    mcp.run(transport="stdio")
