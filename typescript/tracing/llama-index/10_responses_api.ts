import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow("llama_index_responses", async ({ responses }) => {
  console.log(
    (
      await responses.chat({
        messages: [
          { role: "user", content: "Use the native Responses client." },
        ],
      })
    ).message.content,
  );
});
