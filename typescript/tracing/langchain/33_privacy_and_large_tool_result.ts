import { RunnableLambda } from "@langchain/core/runnables";
import { tool } from "@langchain/core/tools";
import { RespanCallbackHandler } from "@respan/instrumentation-langchain";
import { z } from "zod";
import { initRespan, shutdown, tracingConfig } from "./_shared";

export async function privacyAndLargeToolResult(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-privacy");
  const outputOnly = new RespanCallbackHandler({
    recordInputs: false,
    includeMetadata: false,
  });
  const vector = tool(
    () => Array.from({ length: 5001 }, (_, index) => index / 5001),
    {
      name: "local_vector",
      description: "Return a controlled large vector.",
      schema: z.object({}),
    },
  );
  try {
    await RunnableLambda.from(() => false).invoke(
      { private_input: "omitted" },
      { callbacks: [outputOnly], runName: "output_only" },
    );
    const result = await vector.invoke(
      {
        type: "tool_call",
        id: "call_vector_5001",
        name: "local_vector",
        args: {},
      },
      tracingConfig(runtime, "large_tool_result"),
    );
    console.log(
      `Native tool returned ${JSON.parse(String(result.content)).length} vector values.`,
    );
  } finally {
    await shutdown(runtime);
  }
}
if (import.meta.url === `file://${process.argv[1]}`)
  await privacyAndLargeToolResult();
