from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from respan import workflow
from vertexai.generative_models import (
    GenerationConfig,
    HarmBlockThreshold,
    HarmCategory,
    Part,
    SafetySetting,
    ToolConfig,
)


def main():
    native = NativeRuntime()
    respan = create_respan()

    @workflow(name="vertexai_generation")
    def generate(prompt):
        return native.model().generate_content(
            [
                Part.from_text(prompt),
                Part.from_data(b"controlled-image", mime_type="image/png"),
            ],
            generation_config=GenerationConfig(
                temperature=0, top_p=0.25, stop_sequences=["done"], max_output_tokens=32
            ),
            safety_settings=[
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                )
            ],
            tool_config=ToolConfig(
                function_calling_config=ToolConfig.FunctionCallingConfig(
                    mode=ToolConfig.FunctionCallingConfig.Mode.AUTO
                )
            ),
            labels={"controlled": "value"},
        )

    try:
        with example_context("generation"):
            response = generate("hello")
            assert response.text == "native response" and len(native.requests) == 1
        print("generation: native text/config/media preserved")
    finally:
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    main()
