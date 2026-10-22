# Haystack Respan Tracing Examples

These examples target released Haystack 3.3 and OpenInference Haystack 0.1.44.
They use released Respan core and OpenInference bridge packages. Before the
paired SDK change is published, install the requirements and edited adapter in
one resolver operation:

```bash
cd python/tracing/haystack
python -m pip install -r requirements.txt \
  -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-haystack
```

The tested runtime uses `respan-ai==4.2.3`, `respan-tracing==2.20.1`,
`respan-sdk==2.7.6`, `respan-instrumentation-openinference==1.2.5`, and
OpenTelemetry 1.45.0. The requirements pin AI semantic conventions to the tested
0.5.1 release. The adapter also supports Haystack 2.18; the two new native mock
feature scripts require Haystack 3.

Run all 43 deterministic scenarios with one exact marker:

```bash
RESPAN_EXAMPLE_RUN_ID=haystack-my-run python run_all.py
```

The default suite uses local data and native mock models. With `RESPAN_API_KEY`
set, it exports the synthetic fixture traces to Respan; it makes no model
provider or gateway calls. Without that key, it runs locally. `RESPAN_BASE_URL`
defaults to `https://api.respan.ai/api`. Optional converter dependencies and
PyTorch for `TopPSampler` are included in the requirements.

Each scenario has one workflow containing its actual component spans. The suite
includes the complex pipeline and the newest SDK features: agent-owned tools,
async tools, full embedding vectors, streaming handles, controlled errors and
content opt-out. `TRACELOOP_TRACE_CONTENT=false` and Respan's scoped content
policy also disable payload capture. `TraceConfig(hide_inputs=True, hide_outputs=True)` configures
OpenInference privacy; Haystack's own content-tracing switch is separate.

Gateway and managed-prompt actions are explicit options:

```bash
# Calls the gateway and an existing deployed prompt; requires RESPAN_PROMPT_ID.
python run_all.py --live-gateway

# Creates and deploys a managed prompt, then calls it through the gateway.
python run_all.py --create-prompt
```

These options require a Respan key with the corresponding access and credits.
Set `RESPAN_PROMPT_VARIABLES_JSON` when an existing prompt uses custom variables.
They are not part of the deterministic instrumentation validation run. Individual
scripts can also be run directly.

## Scripts

| Script | Coverage |
| --- | --- |
| `00_setup_tracing.py` | Respan tracing setup with an offline Haystack pipeline |
| `01_setup_respan_gateway.py` | Respan gateway setup for `OpenAIChatGenerator` |
| `complex_edge_cases.py` | Complex single-trace pipeline with preprocessing, routing, retrieval, joining, prompt building, generation, answer building, adapting, and handled failure cases |
| `02_pipeline_run.py` | `Pipeline.run` |
| `03_async_pipeline_run.py` | `Pipeline.run_async` (or `AsyncPipeline` on Haystack 2) |
| `04_prompt_builder.py` | `PromptBuilder` |
| `05_chat_prompt_builder.py` | `ChatPromptBuilder` |
| `06_answer_builder.py` | `AnswerBuilder` |
| `07_output_adapter.py` | `OutputAdapter` |
| `08_document_writer.py` | `DocumentWriter` |
| `09_cache_checker.py` | `CacheChecker` |
| `10_in_memory_bm25_retriever.py` | `InMemoryBM25Retriever` |
| `11_in_memory_embedding_retriever.py` | `InMemoryEmbeddingRetriever` |
| `12_document_cleaner.py` | `DocumentCleaner` |
| `13_text_cleaner.py` | `TextCleaner` |
| `14_document_splitter.py` | `DocumentSplitter` |
| `15_recursive_document_splitter.py` | `RecursiveDocumentSplitter` |
| `16_markdown_header_splitter.py` | `MarkdownHeaderSplitter` |
| `17_document_joiner.py` | `DocumentJoiner` |
| `18_answer_joiner.py` | `AnswerJoiner` |
| `19_branch_joiner.py` | `BranchJoiner` |
| `20_list_joiner.py` | `ListJoiner` |
| `21_string_joiner.py` | `StringJoiner` |
| `22_conditional_router.py` | `ConditionalRouter` |
| `23_document_length_router.py` | `DocumentLengthRouter` |
| `24_document_type_router.py` | `DocumentTypeRouter` |
| `25_file_type_router.py` | `FileTypeRouter` |
| `26_metadata_router.py` | `MetadataRouter` |
| `27_top_p_sampler.py` | `TopPSampler` |
| `28_json_schema_validator.py` | `JsonSchemaValidator` |
| `29_regex_text_extractor.py` | `RegexTextExtractor` |
| `30_answer_exact_match_evaluator.py` | `AnswerExactMatchEvaluator` |
| `31_document_recall_evaluator.py` | `DocumentRecallEvaluator` |
| `32_document_mrr_evaluator.py` | `DocumentMRREvaluator` |
| `33_document_map_evaluator.py` | `DocumentMAPEvaluator` |
| `34_document_ndcg_evaluator.py` | `DocumentNDCGEvaluator` |
| `35_csv_to_document.py` | `CSVToDocument` |
| `36_json_converter.py` | `JSONConverter` |
| `37_markdown_to_document.py` | `MarkdownToDocument` |
| `38_text_file_to_document.py` | `TextFileToDocument` |
| `39_html_to_document.py` | `HTMLToDocument` |
| `40_tool_invoker.py` | Native `Agent` tool execution (or `ToolInvoker` on Haystack 2) |
| `41_openai_generator_gateway.py` | `OpenAIChatGenerator` through Respan gateway |
| `42_openai_chat_generator_gateway.py` | `OpenAIChatGenerator` through Respan gateway |
| `43_prompt_management_gateway.py` | Respan prompt management through Haystack `OpenAIChatGenerator` and the Respan gateway |
| `44_prompt_management_extra_body_gateway.py` | Creates and deploys a Respan managed prompt, then passes only `prompt_id` and variables through Haystack `generation_kwargs.extra_body` while the LLM call uses Respan gateway credits |
| `45_current_sdk_features.py` | Native mock agents, sync/async tools, 128-dimensional embeddings, `Pipeline.stream`, and controlled failure |
| `46_content_opt_out.py` | Agent/model/embedding content opt-out with reported usage retained |
