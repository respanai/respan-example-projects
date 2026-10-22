"""Complex Haystack pipeline and representative edge cases."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _shared import (
    configure_respan,
    create_tool_runner,
    finish_respan,
    print_result,
    sample_document_store,
    sample_documents,
    write_sample_files,
)


def run_complex_edge_cases_example():
    respan = configure_respan("haystack-complex-edge-cases")
    try:
        from haystack import Pipeline, component
        from haystack.components.builders import (
            AnswerBuilder,
            ChatPromptBuilder,
            PromptBuilder,
        )
        from haystack.components.caching import CacheChecker
        from haystack.components.converters import (
            CSVToDocument,
            HTMLToDocument,
            JSONConverter,
            MarkdownToDocument,
            OutputAdapter,
            TextFileToDocument,
        )
        from haystack.components.evaluators import (
            AnswerExactMatchEvaluator,
            DocumentRecallEvaluator,
        )
        from haystack.components.extractors import RegexTextExtractor
        from haystack.components.joiners import (
            AnswerJoiner,
            DocumentJoiner,
            ListJoiner,
            StringJoiner,
        )
        from haystack.components.preprocessors import (
            DocumentCleaner,
            DocumentSplitter,
            TextCleaner,
        )
        from haystack.components.rankers import LostInTheMiddleRanker
        from haystack.components.retrievers import (
            FilterRetriever,
            MultiQueryTextRetriever,
        )
        from haystack.components.retrievers.in_memory import (
            InMemoryBM25Retriever,
            InMemoryEmbeddingRetriever,
        )
        from haystack.components.routers import (
            ConditionalRouter,
            DocumentLengthRouter,
            DocumentTypeRouter,
            FileTypeRouter,
            MetadataRouter,
        )
        from haystack.components.validators import JsonSchemaValidator
        from haystack.components.writers import DocumentWriter
        from haystack.dataclasses import ChatMessage
        from haystack.dataclasses.chat_message import ToolCall
        from haystack.document_stores.in_memory import InMemoryDocumentStore
        from haystack.tools import Tool

        @component
        class OfflineProviderGenerator:
            @component.output_types(replies=list[str], meta=list[dict[str, Any]])
            def run(self, prompt: str) -> dict[str, Any]:
                return {
                    "replies": [
                        "Python was created by Guido van Rossum and first released in 1991."
                    ],
                    "meta": [
                        {
                            "provider": "anthropic",
                            "model_name": "claude-offline",
                            "usage": {"input_tokens": 42, "output_tokens": 13},
                        }
                    ],
                }

        @component
        class EdgeCaseProbe:
            @component.output_types(report=dict[str, str])
            def run(self, trigger: str) -> dict[str, Any]:
                report = {"trigger": trigger}

                def capture(name: str, action: Any) -> None:
                    try:
                        action()
                    except Exception as exc:  # noqa: BLE001 - collect controlled SDK failures
                        first_line = str(exc).splitlines()[0]
                        report[name] = f"{type(exc).__name__}: {first_line}"
                    else:
                        report[name] = "no error"

                capture(
                    "missing_required_prompt_variable",
                    lambda: PromptBuilder(
                        "Required variable: {{ missing }}",
                        required_variables=["missing"],
                    ).run(),
                )
                capture(
                    "conditional_router_no_route",
                    lambda: ConditionalRouter(
                        [
                            {
                                "condition": "{{ False }}",
                                "output": "{{ value }}",
                                "output_name": "never",
                                "output_type": str,
                            }
                        ]
                    ).run(value="x"),
                )
                capture(
                    "conditional_router_type_validation",
                    lambda: ConditionalRouter(
                        [
                            {
                                "condition": "{{ True }}",
                                "output": "{{ value }}",
                                "output_name": "typed",
                                "output_type": int,
                            }
                        ],
                        validate_output_type=True,
                    ).run(value="not-an-int"),
                )

                @component
                class BadOutput:
                    def run(self):
                        return ["not", "a", "dict"]

                def invalid_component_output() -> None:
                    pipeline = Pipeline()
                    pipeline.add_component("bad_output", BadOutput())
                    pipeline.run({})

                capture("component_invalid_output", invalid_component_output)

                def bad_connection() -> None:
                    pipeline = Pipeline()
                    pipeline.add_component(
                        "prompt",
                        PromptBuilder("{{ value }}", required_variables=["value"]),
                    )
                    pipeline.add_component(
                        "retriever",
                        InMemoryEmbeddingRetriever(sample_document_store()),
                    )
                    pipeline.connect("prompt.prompt", "retriever.query_embedding")

                capture("pipeline_connect_type_mismatch", bad_connection)

                def missing_tool() -> None:
                    def noop() -> str:
                        return "ok"

                    tool = Tool(
                        name="noop",
                        description="No-op tool.",
                        parameters={"type": "object", "properties": {}},
                        function=noop,
                    )
                    create_tool_runner([tool]).run(
                        messages=[
                            ChatMessage.from_assistant(
                                tool_calls=[
                                    ToolCall(
                                        tool_name="missing",
                                        arguments={},
                                        id="missing",
                                    )
                                ]
                            )
                        ]
                    )

                capture("tool_invoker_missing_tool", missing_tool)

                try:
                    from haystack.components.samplers import TopPSampler

                    sampler = TopPSampler(top_p=0.8, min_top_k=1)
                    sampler.run(sample_documents())
                    report["top_p_sampler_optional_dependency"] = "available"
                except Exception as exc:  # noqa: BLE001 - collect controlled SDK failures
                    first_line = str(exc).splitlines()[0]
                    report["top_p_sampler_optional_dependency"] = (
                        f"{type(exc).__name__}: {first_line}"
                    )

                return {"report": report}

        def add(a: int, b: int) -> str:
            return str(a + b)

        with TemporaryDirectory() as directory:
            files = write_sample_files(Path(directory))
            unknown_file = Path(directory) / "sample.unknown"
            unknown_file.write_text("unclassified content", encoding="utf-8")
            file_sources = [
                str(files["text"]),
                str(files["markdown"]),
                str(files["html"]),
                str(files["json"]),
                str(files["csv"]),
                str(unknown_file),
            ]

            document_store = sample_document_store()
            writer_store = InMemoryDocumentStore()
            tool = Tool(
                name="add",
                description="Add two integers.",
                parameters={
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer"},
                        "b": {"type": "integer"},
                    },
                    "required": ["a", "b"],
                },
                function=add,
            )

            metadata_rules = {
                "programming": {
                    "field": "meta.kind",
                    "operator": "==",
                    "value": "programming",
                },
                "cooking": {
                    "field": "meta.kind",
                    "operator": "==",
                    "value": "cooking",
                },
            }
            query_routes = [
                {
                    "condition": "{{ documents | length == 0 }}",
                    "output": "{{ query }}",
                    "output_name": "empty_query",
                    "output_type": str,
                },
                {
                    "condition": "{{ True }}",
                    "output": "{{ query }}",
                    "output_name": "runnable_query",
                    "output_type": str,
                },
            ]
            prompt_template = """
Documents:
{% for doc in documents %}
- {{ doc.content }}
{% endfor %}

Question: {{ question }}
Answer:
"""

            pipeline = Pipeline(
                metadata={"example": "complex_edge_cases", "haystack_version": "2.28.0"}
            )
            pipeline.add_component(
                "document_type_router",
                DocumentTypeRouter(
                    mime_types=["text/plain"],
                    mime_type_meta_field="mime",
                ),
            )
            pipeline.add_component(
                "document_cleaner",
                DocumentCleaner(
                    remove_empty_lines=True,
                    remove_extra_whitespaces=True,
                ),
            )
            pipeline.add_component(
                "document_splitter",
                DocumentSplitter(split_by="word", split_length=12, split_overlap=2),
            )
            pipeline.add_component("metadata_router", MetadataRouter(metadata_rules))
            pipeline.add_component("length_router", DocumentLengthRouter(threshold=6))
            pipeline.add_component(
                "retriever",
                InMemoryBM25Retriever(document_store, top_k=2),
            )
            pipeline.add_component(
                "embedding_retriever",
                InMemoryEmbeddingRetriever(document_store, top_k=2),
            )
            pipeline.add_component("filter_retriever", FilterRetriever(document_store))
            pipeline.add_component(
                "multi_query_retriever",
                MultiQueryTextRetriever(
                    retriever=InMemoryBM25Retriever(document_store, top_k=1)
                ),
            )
            pipeline.add_component(
                "file_type_router",
                FileTypeRouter(
                    [
                        "text/plain",
                        "text/markdown",
                        "text/html",
                        "application/json",
                        "text/csv",
                    ]
                ),
            )
            pipeline.add_component("text_converter", TextFileToDocument())
            pipeline.add_component(
                "markdown_converter",
                MarkdownToDocument(progress_bar=False),
            )
            pipeline.add_component("html_converter", HTMLToDocument())
            pipeline.add_component(
                "json_converter",
                JSONConverter(
                    jq_schema=".[]",
                    content_key="text",
                    extra_meta_fields={"kind"},
                ),
            )
            pipeline.add_component(
                "csv_converter", CSVToDocument(conversion_mode="row")
            )
            pipeline.add_component(
                "converted_joiner",
                DocumentJoiner(join_mode="concatenate"),
            )
            pipeline.add_component(
                "joiner",
                DocumentJoiner(join_mode="concatenate", top_k=8),
            )
            pipeline.add_component("ranker", LostInTheMiddleRanker())
            pipeline.add_component("query_router", ConditionalRouter(query_routes))
            pipeline.add_component(
                "prompt_builder",
                PromptBuilder(
                    prompt_template,
                    required_variables=["documents", "question"],
                ),
            )
            pipeline.add_component("llm", OfflineProviderGenerator())
            pipeline.add_component("answer_builder", AnswerBuilder())
            pipeline.add_component(
                "answer_joiner",
                AnswerJoiner(join_mode="concatenate", top_k=1),
            )
            pipeline.add_component(
                "answer_adapter",
                OutputAdapter("{{ answers[0].data }}", output_type=str),
            )
            pipeline.add_component("audit_joiner", StringJoiner())
            pipeline.add_component("list_joiner", ListJoiner(str))
            pipeline.add_component(
                "text_cleaner",
                TextCleaner(convert_to_lowercase=True, remove_punctuation=True),
            )
            pipeline.add_component(
                "chat_prompt_builder",
                ChatPromptBuilder(
                    template=[
                        ChatMessage.from_system("Be concise."),
                        ChatMessage.from_user("Question: {{ question }}"),
                    ],
                    required_variables=["question"],
                    variables=["question"],
                ),
            )
            pipeline.add_component(
                "json_validator",
                JsonSchemaValidator(
                    {
                        "type": "object",
                        "properties": {"answer": {"type": "string"}},
                        "required": ["answer"],
                    }
                ),
            )
            pipeline.add_component(
                "regex_extractor",
                RegexTextExtractor(r"ticket=(\d+)"),
            )
            pipeline.add_component("tool_use_add_numbers", create_tool_runner([tool]))
            pipeline.add_component(
                "tool_result_adapter",
                OutputAdapter(
                    "{{ tool_messages | selectattr('tool_call_result') | map(attribute='tool_call_result.result') | first }}",
                    output_type=str,
                ),
            )
            pipeline.add_component("document_writer", DocumentWriter(writer_store))
            pipeline.add_component(
                "cache_checker",
                CacheChecker(document_store, cache_field="source"),
            )
            pipeline.add_component(
                "answer_exact_match_evaluator",
                AnswerExactMatchEvaluator(),
            )
            pipeline.add_component(
                "document_recall_evaluator",
                DocumentRecallEvaluator(),
            )
            pipeline.add_component("edge_case_probe", EdgeCaseProbe())

            pipeline.connect(
                "document_type_router.text/plain", "document_cleaner.documents"
            )
            pipeline.connect(
                "document_cleaner.documents", "document_splitter.documents"
            )
            pipeline.connect("document_splitter.documents", "metadata_router.documents")
            pipeline.connect("metadata_router.programming", "length_router.documents")
            pipeline.connect("length_router.long_documents", "joiner.documents")
            pipeline.connect("metadata_router.cooking", "joiner.documents")
            pipeline.connect("retriever.documents", "joiner.documents")
            pipeline.connect("embedding_retriever.documents", "joiner.documents")
            pipeline.connect("filter_retriever.documents", "joiner.documents")
            pipeline.connect("multi_query_retriever.documents", "joiner.documents")
            pipeline.connect("file_type_router.text/plain", "text_converter.sources")
            pipeline.connect(
                "file_type_router.text/markdown", "markdown_converter.sources"
            )
            pipeline.connect("file_type_router.text/html", "html_converter.sources")
            pipeline.connect(
                "file_type_router.application/json", "json_converter.sources"
            )
            pipeline.connect("file_type_router.text/csv", "csv_converter.sources")
            pipeline.connect("text_converter.documents", "converted_joiner.documents")
            pipeline.connect(
                "markdown_converter.documents", "converted_joiner.documents"
            )
            pipeline.connect("html_converter.documents", "converted_joiner.documents")
            pipeline.connect("json_converter.documents", "converted_joiner.documents")
            pipeline.connect("csv_converter.documents", "converted_joiner.documents")
            pipeline.connect("converted_joiner.documents", "joiner.documents")
            pipeline.connect("joiner.documents", "ranker.documents")
            pipeline.connect("ranker.documents", "query_router.documents")
            pipeline.connect("query_router.runnable_query", "prompt_builder.question")
            pipeline.connect("ranker.documents", "prompt_builder.documents")
            pipeline.connect("prompt_builder.prompt", "llm.prompt")
            pipeline.connect("llm.replies", "answer_builder.replies")
            pipeline.connect("llm.meta", "answer_builder.meta")
            pipeline.connect("ranker.documents", "answer_builder.documents")
            pipeline.connect("query_router.runnable_query", "answer_builder.query")
            pipeline.connect("answer_builder.answers", "answer_joiner.answers")
            pipeline.connect("answer_joiner.answers", "answer_adapter.answers")
            pipeline.connect("query_router.runnable_query", "audit_joiner.strings")
            pipeline.connect("answer_adapter.output", "audit_joiner.strings")
            pipeline.connect("text_cleaner.texts", "list_joiner.values")
            pipeline.connect("audit_joiner.strings", "list_joiner.values")
            pipeline.connect(
                "tool_use_add_numbers.messages"
                if hasattr(
                    pipeline.get_component("tool_use_add_numbers"), "chat_generator"
                )
                else "tool_use_add_numbers.tool_messages",
                "tool_result_adapter.tool_messages",
            )
            pipeline.connect("tool_result_adapter.output", "list_joiner.values")

            result = pipeline.run(
                {
                    "document_type_router": {"documents": sample_documents()},
                    "retriever": {"query": "Who created Python?"},
                    "embedding_retriever": {
                        "query_embedding": [0.8, 0.2, 0.0],
                        "return_embedding": True,
                    },
                    "filter_retriever": {
                        "filters": {
                            "field": "meta.kind",
                            "operator": "==",
                            "value": "cooking",
                        }
                    },
                    "multi_query_retriever": {
                        "queries": ["Python creator", "systems programming language"]
                    },
                    "file_type_router": {"sources": file_sources},
                    "csv_converter": {"content_column": "text"},
                    "query_router": {"query": "Who created Python?"},
                    "text_cleaner": {"texts": ["Haystack, Tracing! 123"]},
                    "chat_prompt_builder": {"question": "What is Haystack?"},
                    "json_validator": {
                        "messages": [ChatMessage.from_assistant('{"wrong": "Paris"}')]
                    },
                    "regex_extractor": {"text_or_messages": "support ticket=42"},
                    "tool_use_add_numbers": {
                        "messages": [
                            ChatMessage.from_assistant(
                                tool_calls=[
                                    ToolCall(
                                        tool_name="add",
                                        arguments={"a": 19, "b": 23},
                                        id="call_1",
                                    )
                                ]
                            )
                        ]
                    },
                    "document_writer": {"documents": sample_documents()},
                    "cache_checker": {"items": ["python", "missing"]},
                    "answer_exact_match_evaluator": {
                        "ground_truth_answers": ["Paris"],
                        "predicted_answers": ["Paris"],
                    },
                    "document_recall_evaluator": {
                        "ground_truth_documents": [[sample_documents()[0]]],
                        "retrieved_documents": [sample_documents()[:2]],
                    },
                    "edge_case_probe": {
                        "trigger": "run controlled Haystack error cases"
                    },
                },
                include_outputs_from=set(pipeline.graph.nodes),
            )

        print_result("Complex Haystack edge cases", result)
        return result
    finally:
        finish_respan(respan, emit_summary_span=False)


if __name__ == "__main__":
    run_complex_edge_cases_example()
