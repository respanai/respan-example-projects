# Mistral AI tracing examples

These examples trace the official `mistralai` Python SDK with Respan. They load
environment variables from the repository root `.env` file.

Required for exporting traces:

```bash
RESPAN_API_KEY=...
```

Install the registry dependencies from this directory:

```bash
python -m pip install -r requirements.txt
```

For repository development, or before Mistral 3 support is released, install
the requirements and the local adapter together. Keep the other Respan packages
on their released versions:

```bash
python -m pip install -r requirements.txt \
  -e ../../../../respan/python-sdks/instrumentations/respan-instrumentation-mistralai
```

For Mistral calls, use one of these options:

```bash
# Direct Mistral API calls, still traced to Respan
MISTRAL_API_KEY=...
```

If `MISTRAL_API_KEY` is not set, the examples route the Mistral SDK through the
Respan OpenAI-compatible gateway using `RESPAN_GATEWAY_API_KEY` or
`RESPAN_API_KEY`. In gateway mode, `RESPAN_MISTRALAI_MODEL` is used when set;
otherwise the scripts fall back to `RESPAN_MODEL` from the repo-root `.env` so
the examples run in this repository without requiring separate Mistral provider
credentials.

Optional environment variables:

```bash
RESPAN_BASE_URL=https://api.respan.ai/api
RESPAN_MISTRALAI_MODEL=mistral/mistral-small
MISTRALAI_MODEL=mistral/mistral-small
```

Run one script at a time:

```bash
python 01_chat_completion.py
python 02_multi_turn_chat.py
python 03_async_chat_completion.py
python 04_sync_streaming.py
python 05_async_streaming.py
python 06_tool_calling.py
python 07_expected_provider_failure.py
python 08_expected_application_failure.py
python 09_structured_output.py
python 10_agent_completions.py
```

Or run the complete committed suite with one exact marker:

```bash
RESPAN_EXAMPLE_RUN_ID=otel2-fix-py-group-19-YYYYMMDDTHHMMSSZ python run_all.py
```

When the variable is omitted, `run_all.py` creates and prints one parent marker,
then passes that same marker to all ten child processes.

The first three examples use the configured live gateway (or direct Mistral
credentials). The stream, tool, and failure examples use the current Mistral
SDK with deterministic HTTP fixtures so their content, usage, tool calls, and
errors are repeatable while the resulting spans are still exported to Respan.
The last two examples cover sync/async structured chat and sync/async agent
completions, including both agent streaming methods, using the same HTTP fixtures.

Each script preserves `RESPAN_EXAMPLE_RUN_ID` in metadata as
`example_run_id`, and also emits a unique per-scenario `custom_identifier`.
Every workflow accepts bounded JSON-native scenario input; live SDK clients are
captured outside decorated signatures.

The examples support Mistral SDK 3 and its HTTPX2 transport. Set
`MISTRAL_USE_MOCKS=1` to run the basic sync/async scenarios against a deterministic
HTTP fixture; streaming, tools, and expected failure scenarios also exercise real
released SDK response parsing. To call a provider, omit that setting.
