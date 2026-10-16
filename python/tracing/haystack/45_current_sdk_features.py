"""Haystack 3 agents, async tools, full embeddings, streams and controlled errors."""

import asyncio

from _shared import configure_respan, finish_respan, print_result


def run_features():
    respan = configure_respan("haystack-current-sdk-features")
    try:
        from haystack import Document, Pipeline, component
        from haystack.components.agents import Agent
        from haystack.components.embedders import MockDocumentEmbedder, MockTextEmbedder
        from haystack.components.generators.chat import MockChatGenerator
        from haystack.dataclasses import ChatMessage, ToolCall
        from haystack.tools import Tool

        def build_agent():
            model = MockChatGenerator(
                responses=[
                    ChatMessage.from_assistant(
                        tool_calls=[
                            ToolCall(
                                tool_name="add",
                                arguments={"a": 19, "b": 23},
                                id="haystack-fixture-call",
                            )
                        ]
                    ),
                    "42",
                ],
                meta={
                    "usage": {
                        "prompt_tokens": 7,
                        "completion_tokens": 3,
                        "total_tokens": 10,
                    }
                },
            )
            tool = Tool(
                name="add",
                description="Add fixture integers",
                parameters={
                    "type": "object",
                    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                    "required": ["a", "b"],
                },
                function=lambda a, b: a + b,
            )
            return Agent(chat_generator=model, tools=[tool])

        sync_result = build_agent().run(
            messages=[ChatMessage.from_user("Add 19 and 23")]
        )
        assert sync_result["last_message"].text == "42"
        text_vectors = MockTextEmbedder(dimension=128).run("Find fixture documentation")
        document_vectors = MockDocumentEmbedder(dimension=128).run(
            [Document(content="Trace fixtures"), Document(content="Vector fixtures")]
        )
        assert len(text_vectors["embedding"]) == 128
        assert all(len(doc.embedding) == 128 for doc in document_vectors["documents"])

        async def async_features():
            result = await build_agent().run_async(
                messages=[ChatMessage.from_user("Add 19 and 23 asynchronously")]
            )
            assert result["last_message"].text == "42"
            await MockTextEmbedder(dimension=128).run_async("Async embedding fixture")
            pipeline = Pipeline()
            pipeline.add_component(
                "generator", MockChatGenerator(responses="stream answer")
            )
            handle = pipeline.stream(
                {
                    "generator": {
                        "messages": [ChatMessage.from_user("Stream fixture response")]
                    }
                }
            )
            chunks = [chunk async for chunk in handle]
            assert "".join(chunk.content for chunk in chunks) == "stream answer"
            assert handle.result["generator"]["replies"][0].text == "stream answer"

        asyncio.run(async_features())

        @component
        class ControlledFailure:
            @component.output_types(value=str)
            def run(self, value: str):
                raise RuntimeError("expected fixture component failure")

        try:
            ControlledFailure().run("controlled failure fixture")
        except RuntimeError as exc:
            assert str(exc) == "expected fixture component failure"
        else:
            raise AssertionError("Expected the fixture failure")
        result = {
            "sync_and_async_tools": "42",
            "embedding_dimensions": 128,
            "stream": "stream answer",
            "expected_error": True,
        }
        print_result("Current SDK features", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_features()
