import assert from "node:assert/strict";
import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_embedding", async ({ embedding }) => {
  const vectors = await embedding.getTextEmbeddings([
    "first document",
    "second document",
  ]);
  if (process.env.LLAMA_INDEX_LIVE !== "true")
    assert.equal(vectors[0].length, 5001);
  console.log(
    JSON.stringify({ vectors: vectors.length, dimensions: vectors[0].length }),
  );
});
