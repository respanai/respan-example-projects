import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_basic", async ({ llm }) => {
  const result = await llm.chat({
    messages: [{ role: "user", content: "Describe Respan." }],
  });
  console.log(result.message.content);
  const completion = await llm.complete({
    prompt: "Complete a short sentence about tracing.",
  });
  console.log(completion.text);
});
