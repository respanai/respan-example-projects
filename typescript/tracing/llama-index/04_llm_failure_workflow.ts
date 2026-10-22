import assert from "node:assert/strict";
import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_failure", async ({ llm }) => {
  await assert.rejects(
    llm.chat({ messages: [{ role: "user", content: "CONTROLLED_FAILURE" }] }),
    (error: any) => error.status === 422,
  );
  console.log("Native HTTP 422 observed.");
});
