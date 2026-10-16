from _fixtures import NativeRuntime
from _shared import create_respan, example_context, finish_respan
from respan import workflow


def main():
    native = NativeRuntime()
    respan = create_respan()

    @workflow(name="vertexai_chat_streaming")
    def stream(prompt):
        chat = native.model().start_chat()
        chunks = list(chat.send_message(prompt, stream=True))
        assert len(chunks) == 70
        source = native.model().generate_content(prompt, stream=True)
        assert next(source).text == "0,"
        source.close()
        unread = native.model().generate_content(prompt, stream=True)
        unread.close()
        return "".join(chunk.text for chunk in chunks)

    try:
        with example_context("chat-streaming"):
            result = stream("stream")
            assert result.endswith("69,")
        print("chat-streaming: 70 native chunks and early/unread close preserved")
    finally:
        native.close()
        finish_respan(respan)


if __name__ == "__main__":
    main()
