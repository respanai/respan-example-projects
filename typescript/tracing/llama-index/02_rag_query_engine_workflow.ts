import { Document, Settings, VectorStoreIndex } from "llamaindex";
import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_rag", async ({ llm, embedding }) => {
  Settings.llm = llm;
  Settings.embedModel = embedding;
  const index = await VectorStoreIndex.fromDocuments([
    new Document({ text: "Respan traces native AI applications." }),
  ]);
  const answer = await index
    .asQueryEngine()
    .query({ query: "What does Respan trace?" });
  console.log(answer.toString());
});
