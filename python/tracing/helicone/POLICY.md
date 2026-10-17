# Helicone sampling and privacy

`19_sampling_and_privacy.py` runs the actual `helicone-helpers==1.2.1`
manual logger and original builder objects through the public `Respan`
pipeline. Each policy runs in a separate Python process so OpenTelemetry
registration and Respan's singleton cannot leak between cases. The default
uses real HTTP requests to a loopback Helicone sink and OTLP receiver. It
does not load `.env` files or contact Helicone or a model provider.

The earlier [Helicone examples PR #77](https://github.com/respanai/respan-example-projects/pull/77)
contains the feature suite numbered 01–18. This policy example is independent
and adds coverage for the sampler, suppression, privacy ceilings, deferred
builders, and activation lifecycle.

Install the candidate Helicone wheel with the released Respan companions:

```bash
python3.12 -m venv .venv-policy
.venv-policy/bin/python -m pip install -r policy_requirements.txt \
  /path/to/respan_instrumentation_helicone-0.1.0-py3-none-any.whl
.venv-policy/bin/python 19_sampling_and_privacy.py
```

The sample checks DROP and RECORD_ONLY samplers, standard instrumentation
suppression, `capture_content=False`, `TRACELOOP_TRACE_CONTENT=false`, the
runtime context content flag, private ancestors, and `Respan(is_enabled=False)`.
These policies control Respan telemetry. Native Helicone logging continues
with its original payloads and destination; this fixture keeps that destination
on loopback.
Setting a nested context flag to true cannot re-enable content excluded by an
earlier policy. Deferred builders preserve their creation policy and the
current policy at send time. A builder from a deactivated instrumentation
generation retains native behavior without emitting under a new generation.
Builders created before instrumentation activates have only send-time policy.
The private-ancestor and deferred-builder cases also use an actual current
span's `allow_trace_content=False` attribute, including response mutation under
that span followed by a public send. Privacy checks inspect full attributes,
status descriptions, exception events, and the matching local OTLP record.

The feature case verifies that admitted requests still retain an 80-message
history in canonical JSON, 75 tool definitions, a native response tool-call ID, structured image
input, a 5001-dimensional embedding, stream assembly and explicit zero usage,
and controlled errors. These are synthetic manual log payloads; they do not
claim model inference or provider billing verification. Native application
results and exception objects remain unchanged. Indexed convenience message
attributes remain subject to the native OpenTelemetry attribute-count limit;
the example does not raise that limit. The delayed-parent case uses the real
ParentBased sampler to preserve an unsampled creation parent at send time.
Recent explicit manual timestamps and native builder creation/completion times
must survive in the emitted span with their original nonzero duration.

Run one case with `--mode`, for example:

```bash
.venv-policy/bin/python 19_sampling_and_privacy.py --mode delayed_policy
```

External Respan export requires `RESPAN_EXAMPLE_EXPORT=1` plus explicitly
configured `RESPAN_API_KEY`, `RESPAN_BASE_URL`, and `RESPAN_EXAMPLE_RUN_ID`.
The native Helicone sink stays local. The runner prints the exact trace and
span IDs for scoped inspection and never prints headers or credentials.
`RESPAN_EXAMPLE_CAPTURE_PATH` optionally saves synthetic local wire evidence
and summaries to the chosen directory. A successful local assertion proves
the producer and export pipeline; stored trace fidelity needs separate
inspection of those exact IDs.
