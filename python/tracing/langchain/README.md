# LangChain Respan tracing examples

Run all 34 scripts with released SDKs and controlled responses, without API keys:

```bash
cd python/tracing/langchain
python -m pip install -r requirements.txt
python run_all_examples.py
```

The default is fixture mode with an in-memory OTel exporter. It does not load the
repository `.env` or send traces. Fake models are real LangChain SDK classes;
structured output and the provider example use real ChatOpenAI/OpenAI clients
with controlled HTTP/SSE responses. Tool binding retains the actual schemas.

To export these controlled fixtures explicitly:

```bash
RESPAN_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=your-unique-marker python run_all_examples.py
```

Export loads the repository-root `.env` with `override=False`, or the file named
by `RESPAN_ENV_FILE`. Set `RESPAN_API_KEY`; `RESPAN_BASE_URL` defaults to
`https://api.respan.ai/api`. The run marker appears in Respan metadata for scoped
trace inspection. Credentials are not printed. Export is a separate opt-in from
model-provider access.

To call a real provider in structured-output examples 13/23, set
`LANGCHAIN_LIVE=1`, `OPENAI_API_KEY`, and optionally `OPENAI_BASE_URL` and
`LANGCHAIN_OPENAI_MODEL`, then run either script. Live support depends on the
selected provider/model and is not established by the controlled fixtures.
Script 31 is a deterministic protocol/error fixture and should stay in fixture
mode. These fixtures do not validate the full Langflow application.

The runner uses fresh subprocesses, runs the entire bounded set, reports failures,
and explicitly skips APIs absent from the installed release. Current validation
uses LangChain 1.4.3/core 1.6.6/OpenAI integration 1.6.7/LangGraph 1.2.12. At the
supported minimum (LangChain/core 0.3.0, OpenAI 0.2.0, LangGraph 0.2.20), scripts
19–23 require the newer `create_agent` API and 30 requires dynamic interrupt/resume;
28 compatible scripts run and six are explicitly skipped. Set
`LANGCHAIN_RUNNER_REPORT` to save counts and `LANGCHAIN_CAPTURE_DIR` to save local
span attributes for comparison.

| Scripts | SDK surface |
| --- | --- |
| 00–09 | Quickstart, chat invoke/stream/batch/as_completed and async/events |
| 10–13 | Text LLM, tool binding, provider structured output |
| 14–18 | Sync/async tools, prompt chains, parallel runnables, retrievers |
| 19–23 | Current agents, update/message/custom streams, structured agent output |
| 24–28 | Custom events, retries, chain/tool/retriever errors |
| 29–30 | State graph invoke/stream, checkpointed interrupt/resume |
| 31 | Real OpenAI HTTP/SSE/async responses, source cache/reasoning usage, errors |
| 32 | Environment start privacy bound and Respan context end veto |
| 33 | Current calls distinct from history, actual IDs, full 5000-dimensional tool artifacts |

Callbacks capture actual completion messages, source usage, current tool calls,
full schemas/IDs/vectors and documents. Private runs keep native results while
omitting content. Errors have OTel ERROR, no fabricated output or HTTP status.
The adapter keeps caller context across streaming yields and uses native run
parent IDs for trace hierarchy. Local checks and HTTP export acceptance do not
establish stored-trace semantic acceptance; inspect same-run trees and records.

Official references: [models](https://docs.langchain.com/oss/python/langchain/models),
[agents](https://docs.langchain.com/oss/python/langchain/agents),
[streaming](https://docs.langchain.com/oss/python/langchain/streaming), and
[LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).
