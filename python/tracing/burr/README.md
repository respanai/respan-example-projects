# Apache Burr tracing examples

The nine scenarios use Apache Burr's real state machine and tracing APIs with
controlled local actions. They cover application runs and errors, custom spans,
synchronous and asynchronous streams, `abuild()`, structured state and arguments,
privacy vetoes, iteration, and single-step execution. No model provider is needed.

Install `requirements.txt` in a virtual environment and install the Burr
instrumentation package from your local checkout for development:

```bash
pip install -r requirements.txt
pip install --no-deps -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-burr
RESPAN_EXAMPLE_RUN_ID=burr-local-check python run_all.py
```

The default records spans in memory. To export the same controlled scenarios,
set `RESPAN_EXAMPLE_EXPORT=1` and provide `RESPAN_API_KEY` in the environment or
repository-root `.env`. `RESPAN_BASE_URL` defaults to `https://api.respan.ai/api`.
The `.env` is loaded only for explicit export. There are no live model calls.

Set `RESPAN_EXAMPLE_REPORT_DIR` to save local span reports. The runner prints one
shared run marker; each application ID contains that marker and its scenario.
Always fully consume a stream or call its native `get()` method so Burr delivers
its terminal lifecycle callbacks.
