import { runNamedWorkflow } from "./_runtime.js";
await runNamedWorkflow(
  "llama_index_private",
  async ({ llm }) => {
    console.log(
      (
        await llm.chat({
          messages: [
            {
              role: "user",
              content: "This content stays outside instrumentation spans.",
            },
          ],
        })
      ).message.content,
    );
  },
  { traceContent: false },
);
