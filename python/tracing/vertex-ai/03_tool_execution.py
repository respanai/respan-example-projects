from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from respan import tool, workflow
from vertexai.generative_models import FunctionDeclaration, Part, Tool


@tool(name="get_weather")
def get_weather(city):
    return {"city": city, "temperature": 22, "sunny": True}


def main():
    native = NativeRuntime()
    respan = create_respan()

    @workflow(name="vertexai_tools")
    def execute(city):
        declaration = FunctionDeclaration(
            name="get_weather",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "api_key": {"type": "string", "default": "controlled-secret"},
                },
                "required": ["city"],
            },
        )
        model = native.model()
        chat = model.start_chat()
        first = chat.send_message(
            "weather in " + city, tools=[Tool(function_declarations=[declaration])]
        )
        call = first.candidates[0].content.parts[0].function_call
        result = get_weather(call.args["city"])
        second = chat.send_message(
            Part.from_function_response(name=call.name, response=result)
        )
        assert len(chat.history) == 4
        return second.text

    try:
        with example_context("tools"):
            assert execute("Tokyo") == "native response"
        print("tools: native schema, function call/response and connected tool span")
    finally:
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    main()
