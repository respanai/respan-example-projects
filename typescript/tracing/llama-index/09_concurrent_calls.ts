import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_concurrent", async ({ llm, embedding }) => {
  const results = await Promise.all([
    llm.chat({
      messages: [{ role: "user", content: "First concurrent request." }],
    }),
    llm.chat({
      messages: [{ role: "user", content: "Second concurrent request." }],
    }),
    embedding.getTextEmbedding("Concurrent embedding."),
  ]);
  console.log(JSON.stringify({ results: results.length }));
});
