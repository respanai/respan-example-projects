# Guardrails tracing examples

Nine deterministic examples for Guardrails AI 0.11.0 and the paired `respan-instrumentation-guardrails` update. The adapter also supports Guardrails 0.9.3. These examples use released Respan runtime packages; the target instrumentation may be installed from its paired PR for development.

```bash
pip install -r requirements.txt
pip install --no-deps -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-guardrails
RESPAN_EXAMPLE_RUN_ID=guardrails-audit-001 python run_all.py
```

Set `RESPAN_API_KEY` in the repository root `.env` or environment. `RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`. Every script exports its synthetic trace content to Respan, with the exact run marker in metadata and a per-example custom identifier. Local validators, custom callbacks, and LiteLLM's built-in mock responses require no provider key or model request. Model-cost lookup stays local, and each guard disables Guardrails Hub metrics.

| Script | Coverage |
|---|---|
| `01_pydantic_parse.py` | Validate a known JSON response against a Pydantic schema. |
| `02_gateway_structured_generation.py` | Local fixture generation with model, message, and usage attributes. |
| `03_propagated_attributes.py` | Customer, thread, and exact-run metadata propagation. |
| `04_async_validation.py` | AsyncGuard parsing and custom async generation. |
| `05_validator_outcomes.py` | Local validator pass, noop rejection, and fixed output. |
| `06_streaming.py` | Consume sync and async fixture streams. |
| `07_reask.py` | Repair invalid output with a second custom LLM call. |
| `08_content_privacy.py` | Omit guard and validator content while retaining structure. |
| `09_controlled_error.py` | Preserve native error spans from a raised validation exception. |

`02_gateway_structured_generation.py` also supports an explicit live Gateway run with `RESPAN_GUARDRAILS_LIVE=1`; set `RESPAN_MODEL` to select its model. The complete default runner uses fixtures.

Guardrails' native streaming spans and links are retained. Source telemetry can omit final model completion content or stream token usage. A noop validator rejection is represented by the validation result, not an execution error. Raised exceptions retain the SDK's native error status.

After running, inspect Respan MCP with the exact `metadata__run_id` filter. Check all trees and full exceptional records for parentage, `guardrail`/`chat` types, model/usage, messages, validator results, reask counts, privacy, and errors. A successful export alone does not establish stored-trace semantic acceptance.
