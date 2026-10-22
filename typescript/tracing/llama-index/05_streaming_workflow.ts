import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_stream", async ({ llm }) => {
  const stream = await llm.chat({
    messages: [{ role: "user", content: "Stream a short reply." }],
    stream: true,
  });
  for await (const chunk of stream) process.stdout.write(chunk.delta);
  process.stdout.write("\n");
});
