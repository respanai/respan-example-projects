# Semantic Kernel tracing

These examples exercise Semantic Kernel **1.44.1** with the Respan adapter,
released Respan core packages, and real OpenAI SDK models. The default suite uses
synthetic HTTP responses through `httpx2.MockTransport`; it requires a Respan key
but no model-provider credentials.

```bash
pip install -r requirements.txt
export RESPAN_API_KEY=...
export RESPAN_EXAMPLE_RUN_ID=semantic-kernel-my-run
python run_all.py
```

Before the adapter release, install the companion adapter branch in the same
resolver command as these requirements (`pip install -r requirements.txt -e
/path/to/respan-instrumentation-semantic-kernel`). Core dependencies remain
registry packages. The runner preserves the supplied marker, bounds each script
to 180 seconds, continues after failures, and exits nonzero if any script fails.

| Script | Coverage |
| --- | --- |
| `01_kernel_function.py` | Direct kernel function execution |
| `02_chat_completion.py` | Prompt function, chat content, reported usage |
| `03_plugin_tool_call.py` | Automatic tool invocation, call IDs, prompt history |
| `04_function_failure.py` | Controlled tool/workflow failure |
| `05_agent_methods.py` | Agent `get_response(messages=...)`, `invoke`, and `invoke_stream` |
| `06_embeddings.py` | Three documents in two provider batches, complete 128-dimensional vectors, usage, HTTP error |
| `07_streaming.py` | Zero-usage stream, empty SSE response, chat HTTP error |
| `08_content_policy.py` | Environment/runtime opt-out and OTel suppression |
| `09_capture_opt_out.py` | Instrumentor `capture_content=False` |

The fixtures report chat usage 9/3, cache reads 4, reasoning tokens 2, embedding
usage 7 per provider batch, and explicit zero usage in the completed stream.
An empty stream and failed model calls have no provider usage. Tool results
belong in tool output and subsequent prompt history; only the requesting model
turn has current tool calls.

Scripts 02 and 03 can call a real Respan gateway when
`SEMANTIC_KERNEL_LIVE=1`. Set `RESPAN_GATEWAY_API_KEY` (or `RESPAN_API_KEY`),
`RESPAN_GATEWAY_BASE_URL`, and `RESPAN_MODEL` for that optional path. Scripts
05–09 always use deterministic fixtures because they assert controlled results.

After export, query Respan MCP using the exact `metadata.run_id`, then inspect
the trees and relevant full records. Check agent/task/tool parentage, current
versus historical tool calls, actual token counts, complete embedding vectors,
errors, and absence of disabled content. Local and export success do not establish
stored-trace semantic acceptance; report any ingestion differences separately.

The native Semantic Kernel iterator can retain its model span across yields,
and closing its outer iterator from another task may leave the inner model span
unfinished. The adapter preserves the SDK iterator API; these native limits are
recorded separately from fully consumed streaming examples.
