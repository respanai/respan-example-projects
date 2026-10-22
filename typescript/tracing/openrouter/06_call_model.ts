import assert from "node:assert/strict";
import * as z from "zod/v4";
import { ToolType } from "@openrouter/sdk/lib/tool-types.js";
import {
  CHAT_MODEL,
  LIVE,
  createOpenRouterClient,
  createRespan,
  runWithOpenRouterWorkflow,
  shutdownRespan,
  logExampleResult,
} from "./_shared.js";
export async function runCallModel(respan = createRespan()): Promise<void> {
  const own = arguments.length === 0;
  try {
    await runWithOpenRouterWorkflow(
      respan,
      "openrouter_ts_call_model",
      async () => {
        let executions = 0;
        const result = createOpenRouterClient().callModel({
          model: CHAT_MODEL,
          input: "Use lookup to find x, then respond.",
          tools: [
            {
              type: ToolType.Function,
              function: {
                name: "lookup",
                inputSchema: z.object({ q: z.string() }),
                outputSchema: z.object({ found: z.boolean() }),
                execute: async () => {
                  executions++;
                  return { found: false };
                },
              },
            },
          ],
        });
        const textPromise = result.getText();
        assert.equal(result.getText(), textPromise);
        const [text, response] = await Promise.all([
          textPromise,
          result.getResponse(),
        ]);
        if (!LIVE) assert.equal(executions, 1);
        logExampleResult("openrouter_ts_call_model", {
          text,
          executions,
          responseId: response.id,
        });
      },
    );
  } finally {
    if (own) await shutdownRespan(respan);
  }
}
if (import.meta.url === `file://${process.argv[1]}`) await runCallModel();
