import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "writer.basic_chat.workflow";
const respan = createRespan();
const writer = createWriterClient();

try {
  const completion = await withTimeout(
    runWithWriterWorkflow(respan, workflowName, async () => {
      return await writer.chat.chat({
        model: DEFAULT_CHAT_MODEL,
        messages: [
          { role: "system", content: "You write concise launch notes." },
          {
            role: "user",
            content: "Summarize Writer tracing in one sentence.",
          },
        ],
        max_tokens: 80,
        temperature: 0.2,
      });
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected: "one assistant chat completion span",
    actual: completion.choices[0]?.message?.content,
    model: completion.model,
  });
} finally {
  await shutdownRespan(respan);
}
