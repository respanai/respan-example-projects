# Superagent tracing examples

The eight scripts exercise `safety-agent` **0.1.7** with the paired Respan
instrumentation. By default, the real SDK uses controlled provider HTTP,
URL-fetch and Daytona boundaries. Provider and sandbox services are not contacted.

```bash
pip install -r requirements.txt
RESPAN_API_KEY=... RESPAN_EXAMPLE_RUN_ID=superagent-check python run_all.py
```

The repository `.env` loads with `override=False`, preserving shell settings.
Set `RESPAN_BASE_URL` to change the trace export destination. Use the companion
adapter branch/wheel until its release is published.

| Script | Coverage |
| --- | --- |
| 01_guard | Native guard chunk aggregation, structured result and actual zero usage |
| 02_redact | Typed options, entities and rewrite; complete returned result |
| 03_workflow | Nested workflow/task/guard/redact ancestry and metadata |
| 04_scan | Actual SDK scan options and typed response through a controlled Daytona boundary |
| 05_expected_error | Controlled HTTP401 and native input-validation errors |
| 06_content_policy | Environment/context privacy and suppression |
| 07_input_types | Image bytes and public URL processing through controlled boundaries |
| 08_fallback | Current native provider retry/fallback |

The adapter also supports 0.1.5, whose SDK lacks the fallback-model API.
Content capture is bounded and credentials are redacted. Guardrail/tool usage
stays SDK operation metadata; it is not canonical LLM usage.

`SUPERAGENT_EXAMPLE_MODE=live` replaces fixture boundaries with real clients and
requires provider/Superagent keys and Daytona credentials for scanning. The
controlled error and synthetic fallback scenarios target fixture mode. Live
provider/sandbox acceptance is separate from the deterministic suite.
