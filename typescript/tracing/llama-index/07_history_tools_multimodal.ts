import { FunctionTool } from "llamaindex";
import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_full_payload", async ({ llm }) => {
  const history: any[] = Array.from({ length: 80 }, (_, index) => ({
    role: "user",
    content: `history-${index}`,
  }));
  history.push(
    {
      role: "assistant",
      content: "",
      options: {
        toolCall: [
          {
            id: "historical-only",
            name: "lookup",
            input: { topic: "history" },
          },
        ],
      },
    },
    {
      role: "user",
      content: [
        { type: "text", text: "Summarize this image." },
        {
          type: "image_url",
          image_url: { url: "data:image/png;base64,iVBORw0KGgo=" },
        },
      ],
    },
  );
  const tools = Array.from({ length: 80 }, (_, index) =>
    FunctionTool.from(() => false, {
      name: `tool_${index}`,
      description: "Example tool",
      parameters: {
        type: "object",
        properties: { enabled: { type: "boolean", default: false } },
      },
    }),
  );
  const result = await llm.chat({
    messages: history,
    tools,
    responseFormat: { type: "json_object" },
  });
  console.log(result.message.content);
});
