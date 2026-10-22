import { agentTurn, runExample } from "./_shared.js";

// Apply the same content policy to the explicitly decorated runtime workflow.
const previous = process.env.RESPAN_TRACE_CONTENT;
process.env.RESPAN_TRACE_CONTENT = "false";
try {
  await runExample(
    "TypeScript LiveKit Native Content Opt Out",
    async () => agentTurn(),
    { traceContent: false },
  );
} finally {
  if (previous === undefined) delete process.env.RESPAN_TRACE_CONTENT;
  else process.env.RESPAN_TRACE_CONTENT = previous;
}
