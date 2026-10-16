import assert from "node:assert/strict";
import {
  CHAT_MODEL,
  createOpenRouterClient,
  createRespan,
  runWithOpenRouterWorkflow,
  shutdownRespan,
  logExampleResult,
} from "./_shared.js";
export async function runResponses(respan = createRespan()): Promise<void> {
  const own = arguments.length === 0;
  try {
    await runWithOpenRouterWorkflow(
      respan,
      "openrouter_ts_responses",
      async () => {
        const client = createOpenRouterClient();
        // BetaResponses is the public endpoint on the supported 0.13.7 minimum.
        const result = await client.beta.responses.send({
          responsesRequest: {
            model: CHAT_MODEL,
            input: "Show a controlled Responses result.",
            stream: false,
          },
        });
        assert.ok("output" in result);
        logExampleResult("openrouter_ts_responses", {
          outputItems: result.output.length,
        });
      },
    );
  } finally {
    if (own) await shutdownRespan(respan);
  }
}
if (import.meta.url === `file://${process.argv[1]}`) await runResponses();
