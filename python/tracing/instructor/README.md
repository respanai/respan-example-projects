# Instructor tracing examples

Eleven scripts exercise released Instructor 1.17.0 with controlled OpenAI HTTP
responses by default. Native validation, retries, partial/iterable APIs,
async clients, hooks, response parsing, and exceptions still execute.

```bash
pip install -r requirements.txt
python run_all.py
```

Use the companion adapter branch/wheel until it is published. Fixture mode
contacts no model provider and does not export traces. Set
`RESPAN_EXAMPLE_EXPORT=1`, `RESPAN_API_KEY`, and one `RESPAN_EXAMPLE_RUN_ID` to
export the synthetic suite to `https://api.respan.ai/api/v2/traces`.
`RESPAN_BASE_URL` selects another intended tracing API base.

Export/live mode loads the repository `.env` with `override=False`, preserving
explicit shell settings. `RESPAN_EXAMPLE_ENV_FILE` selects another file. The
runner gives every script the same marker, applies timeouts, and reports failed
scenarios. SDK client objects remain outside decorated workflow inputs so their
credentials are not serialized.

| Script | Coverage |
| --- | --- |
| 01_create | Typed invoice extraction |
| 02_validation_hooks | Native validation retry and retained user completion hooks |
| 03_create_with_completion | Parsed result plus actual provider response ID |
| 04_create_iterable | Native multiple-object response |
| 05_async_create | Async typed generation |
| 06_responses | Current factory and OpenAI Responses |
| 07_partial_stream | Native partial response shape and early close where supported |
| 08_controlled_errors | HTTP401, exhausted validation, and current retry token budget |
| 09_privacy | Private model I/O and suppression |
| 10_typed_dict | TypedDict schema and native SDK return type |
| 11_async_stream_cancel | Async iterable output and original cancellation |

Instructor 1.3.7 also runs the suite, with explicit version skips for06/10 and no
completion-hook/token-budget API. Its retry-count semantics and stream return
shapes differ from 1.17; examples retain the actual behavior. The current SDK
converts a TypedDict schema to a native generated Pydantic result in this fixture;
the adapter preserves it. Fixture usage is explicit synthetic response data,
not a live provider measurement.

`INSTRUCTOR_EXAMPLE_MODE=live` uses OpenAI with `INSTRUCTOR_PROVIDER_API_KEY` or
`OPENAI_API_KEY`, optional `INSTRUCTOR_PROVIDER_BASE_URL`, and `INSTRUCTOR_MODEL`
(default `gpt-4o-mini`). Tracing credentials and destinations remain separate.
Controlled errors, synthetic retries, and cancellation target fixture mode.
Live provider access, billing, and unlisted optional provider APIs require
separate validation.
