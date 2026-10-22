# Langfuse tracing with Respan

This example uses released Langfuse 4.x and the paired Respan Langfuse adapter
update. It creates four deterministic traces and fourteen spans:

- `langfuse_simple.workflow`: workflow and generation.
- `langfuse_research.workflow`: workflow, two tools, and generation.
- `langfuse_features.workflow`: workflow, guardrail, agent, embedding, and a
  controlled tool error.
- `langfuse_async.workflow`: async workflow, a single-message tool generation,
  and a generation with usage but no captured content.

Generation spans include messages, model, and exact example token counts.
The embedding includes its model, example input-token count, and complete vector.
These are deterministic SDK observations; no model provider is called.
`propagate_attributes()` attaches the run marker, user, session, and trace name
to the root and every descendant, using the Langfuse 4 API.

Until the companion adapter update is released, install the requirements and
the local adapter together. Other Respan dependencies can use released packages:

```bash
pip install -r requirements.txt -e /path/to/respan/python-sdks/instrumentations/respan-instrumentation-langfuse
RESPAN_EXAMPLE_RUN_ID=your-marker python langfuse_simple_example.py
```

The script loads the repository root `.env`. Set `RESPAN_API_KEY` and optionally
`RESPAN_BASE_URL` for the Respan destination. Dummy Langfuse credentials enable
local SDK span creation; the instrumentor redirects the default trace exporter
into the active Respan runtime before it sends a Langfuse request.

The script checks fourteen successful span injections and closes both SDKs.
For end-to-end acceptance, query Respan logs with exact `metadata__run_id`
matching `RESPAN_EXAMPLE_RUN_ID`, then inspect the four trees and their span
input/output, parentage, guardrail type, embedding usage/vector, and error.
A local count does not confirm backend acceptance.
