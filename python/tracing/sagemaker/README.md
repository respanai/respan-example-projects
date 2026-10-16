# SageMaker Runtime tracing examples

Seven controlled scenarios call the real released boto3 client through botocore's native HTTP parser and CRC-correct event stream frames. They exercise text, full chat history/tool schemas/arguments, fragmented streams, async submission, 5001-dimensional embeddings, native errors/late privacy, and current SessionId/response routing fields. The minimum SDK skips SessionId only when its real service model lacks that member.

```bash
pip install -r requirements.txt
python run_all.py
```

The assertions require the companion instrumentation update. For development, install only the target instrumentation editable or from its built wheel; keep boto3 and Respan companions released. Default runs record locally and make no hosted AWS requests. Set `RESPAN_EXAMPLE_REPORT_DIR` to save actual span trees.

Explicit `RESPAN_EXAMPLE_EXPORT=1` exports through released RespanSpanExporter using `RESPAN_API_KEY`; only this mode loads repository `.env` without overriding shell values. `RESPAN_EXAMPLE_RUN_ID` shares the exact lookup marker. Hosted endpoint/account permissions and arbitrary custom model protocols remain outside these controlled fixtures.

Native StreamingBody and EventStream objects, bytes, resources and exceptions are preserved. Data is observed as callers consume it. Source-zero usage is retained; absent usage/totals/models are not invented. Errors have no fabricated output, but actual earlier stream data can remain. Backend status, redaction and indexing require separate same-run MCP acceptance.
