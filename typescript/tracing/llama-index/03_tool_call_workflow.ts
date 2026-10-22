import { FunctionTool } from "llamaindex";
import { OpenAIAgent } from "@llamaindex/openai";
import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_tool", async ({ llm }) => {
  const lookup = FunctionTool.from(
    ({ topic }: { topic: string }) => ({ topic, found: false }),
    {
      name: "lookup",
      description: "Look up a topic",
      parameters: {
        type: "object",
        properties: { topic: { type: "string" } },
        required: ["topic"],
      },
    },
  );
  const agent = new OpenAIAgent({ llm, tools: [lookup] });
  console.log(
    (await agent.chat({ message: "USE_NATIVE_TOOL: look up Respan." })).message
      .content,
  );
});
