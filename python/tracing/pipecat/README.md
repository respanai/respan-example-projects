# Pipecat tracing examples

These examples exercise released Pipecat pipelines and the native OpenInference
observer through the Respan adapter. The default runner uses controlled service
frames and HTTP/SSE responses, needs no API keys, and keeps spans in memory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt build poetry-core
# Until the companion SDK change is published, install only its target adapter.
pip install --no-deps --no-build-isolation -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-pipecat
python run_all.py
```

Use compatible upstream pairs when pinning dependencies:

| Pipecat | OpenInference delegate | Pipeline API |
| --- | --- | --- |
| >=1.1,<1.3 | >=1.0.2,<2 | PipelineTask / PipelineRunner |
| >=1.3,<2 | >=2,<3 | PipelineWorker / WorkerRunner |

Controlled validation uses1.12.0/2.0.8 and1.1.0/1.0.2 on Python3.12.
The helper selects the actual released Worker or Task API and typed service
settings. No inference methods or native execution methods are mocked. The
OpenAI service uses its real released client with a controlled HTTP transport.

| Script | Controlled coverage |
| --- | --- |
| `01_offline_pipeline.py` | Native LLM frames, text and supplied cache/reasoning/token metrics |
| `02_gateway_llm_pipeline.py` | Explicit optional live provider call; skips by default |
| `03_expected_error.py` | Actual OpenAI AuthenticationError with response401 delivered as native ErrorFrame |
| `04_native_http_service.py` | Pipecat OpenAI service over real client HTTP/SSE |
| `05_tools_and_history.py` | Registered native handler, current tool ID/arguments,150 messages,121 schema properties,5000 dense and256 sparse values |
| `06_private_pipeline.py` | Content disabled on the adapter and workflow context; caller frames/results preserved |
| `07_voice_frames.py` | Native STT/TTS text-frame observation; no live audio inference |
| `08_native_cancel_and_partial_error.py` | Native worker/task cancellation and actual partial text followed by a provider error |
| `09_ambient_supplied_parent.py` | Ambient opt-out bounds a supplied-context parent even after the caller reenables native child capture |

Export the controlled spans only when explicitly requested:

```bash
export RESPAN_PIPECAT_EXPORT=1
export RESPAN_API_KEY=...
export RESPAN_EXAMPLE_RUN_ID=my-pipecat-run
python run_all.py
```

Only explicit export loads the repository `.env`, using `override=False`; shell
markers and configuration stay authoritative. `RESPAN_BASE_URL` defaults to
`https://api.respan.ai/api`. Every script flushes and shuts down telemetry.

A live call requires `RESPAN_PIPECAT_LIVE=1` and
`PIPECAT_PROVIDER_API_KEY`; optional `PIPECAT_PROVIDER_BASE_URL` and
`PIPECAT_PROVIDER_MODEL` configure the actual provider. The historical second
script filename does not establish Respan Gateway routing support. No live
provider, realtime audio, audio model/codec, transport, worker bus or distributed
execution acceptance is claimed by the controlled runner. Backend ingestion and
stored trace projections must be checked separately from local span validation.
