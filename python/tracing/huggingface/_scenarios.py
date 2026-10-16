"""Run released native Transformers APIs against an offline random CPU model."""

import inspect
import threading

import transformers
from _native import tiny_pipeline
from opentelemetry import context
from packaging.version import Version
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY
from transformers import GenerationConfig, TextGenerationPipeline, TextIteratorStreamer
from transformers.pipelines.pt_utils import PipelineIterator


def run(case, provider):
    pipeline = tiny_pipeline()

    def generate(prompt=None, **options):
        if prompt is None:
            return pipeline(max_new_tokens=2, do_sample=False, **options)
        return pipeline(prompt, max_new_tokens=2, do_sample=False, **options)

    if case == "text":
        return [
            generate("Tracing Hugging Face"),
            generate(text_inputs="Tracing native"),
            pipeline(
                text_inputs="Tracing",
                generation_config=GenerationConfig(
                    max_new_tokens=1, do_sample=False, pad_token_id=0, eos_token_id=2
                ),
            ),
        ]
    if case == "batch":
        return [
            generate(["Tracing Hugging", "Face native"]),
            generate("Tracing", num_return_sequences=2, num_beams=2),
        ]
    if case == "privacy":
        result = []
        for flag in (
            ENABLE_CONTENT_TRACING_KEY,
            "trace_content",
            "override_enable_content_tracing",
        ):
            token = context.attach(context.set_value(flag, False))
            try:
                result.append(bool(generate("private controlled input")))
            finally:
                context.detach(token)
        iterator = generate(
            p for p in ["private controlled input", "private controlled second"]
        )
        next(iter(iterator))
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        context.detach(token)
        result.append(bool(list(iterator)))
        return result
    if case == "tiny":
        result = [
            generate("Tracing Hugging", return_tensors=True),
            generate("", return_full_text=False),
            generate(" ".join(["Tracing"] * 5000), return_tensors=True),
        ]
        if Version(transformers.__version__) >= Version("5"):
            result.append(
                generate("Tracing", return_dict_in_generate=True, output_scores=True)
            )
        else:
            result.append(
                {
                    "skipped": "Native pipeline additional ModelOutput fields unavailable on supported minimum"
                }
            )
        return result
    if case == "chat":
        history = [
            {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": "Tracing " + str(i),
            }
            for i in range(75)
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "native_tool",
                    "description": "Controlled schema",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "token": {"type": "string", "default": "synthetic-secret"},
                            "enabled": {"type": "boolean", "default": False},
                        },
                        "required": ["enabled"],
                    },
                },
            }
        ]
        if (
            "tools"
            in inspect.signature(TextGenerationPipeline._sanitize_parameters).parameters
        ):
            return generate(history, tools=tools)
        return {
            "response": generate(history),
            "skipped": "Native pipeline tools is unavailable on this Transformers version",
        }
    if case == "iterator":
        consumed = []

        def prompts():
            for value in ["Tracing", "Face"]:
                consumed.append(value)
                yield value

        iterator = generate(prompts())
        assert type(iterator) is PipelineIterator
        first = list(iterator)
        second = generate(p for p in ["Hugging"])
        third = generate(p for p in ["native"])
        return {
            "consumed": consumed,
            "output": first,
            "siblings": [list(second), list(third)],
        }
    if case == "streamer":
        streamer = TextIteratorStreamer(
            pipeline.tokenizer, skip_prompt=True, timeout=10
        )
        response, errors = [], []
        carrier = context.get_current()

        def worker():
            token = context.attach(carrier)
            try:
                response.append(generate("Tracing", streamer=streamer))
            except BaseException as error:  # noqa: BLE001
                errors.append(error)
            finally:
                context.detach(token)

        thread = threading.Thread(target=worker)
        thread.start()
        pieces = list(streamer)
        thread.join(10)
        if errors:
            raise errors[0]
        assert not thread.is_alive()
        return {"pieces": pieces, "response": response}
    if case == "error":
        result = []
        for private in (False, True):
            token = context.attach(
                context.set_value(ENABLE_CONTENT_TRACING_KEY, not private)
            )
            try:
                try:
                    generate("Tracing", native_unused_keyword="token=synthetic-secret")
                except ValueError as error:
                    result.append(type(error).__name__)
            finally:
                context.detach(token)
        return result
    raise ValueError(case)


SCENARIOS = {
    name: (lambda provider, case=name: run(case, provider))
    for name in (
        "text",
        "batch",
        "privacy",
        "tiny",
        "chat",
        "iterator",
        "streamer",
        "error",
    )
}
