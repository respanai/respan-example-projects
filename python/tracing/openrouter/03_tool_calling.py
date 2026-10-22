import json

from _fixtures import TOOL
from _shared import MODEL, native_client, tool, tracing, workflow
from opentelemetry import trace
from opentelemetry.semconv._incubating.attributes.gen_ai_attributes import (
    GEN_AI_TOOL_CALL_ID,
)


@tool(name="get_weather")
def get_weather(city):
    trace.get_current_span().set_attribute(GEN_AI_TOOL_CALL_ID, "call_weather_p9")
    return {"city": city, "temperature_c": 22}


def main():
    with tracing("tools"), native_client() as client:

        @workflow(name="openrouter_native_tools")
        def run(question):
            response = client.chat.send(
                model=MODEL,
                messages=[{"role": "user", "content": question}],
                tools=[TOOL],
            )
            call = response.choices[0].message.tool_calls[0]
            return get_weather(**json.loads(call.function.arguments))

        print(run("What is the weather in Tokyo?"))


if __name__ == "__main__":
    main()
