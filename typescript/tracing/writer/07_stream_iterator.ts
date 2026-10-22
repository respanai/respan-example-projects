import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
} from "./_shared.js";
const respan = createRespan(),
  writer = createWriterClient(),
  workflowName = "writer.stream_iterator.workflow";
try {
  await runWithWriterWorkflow(respan, workflowName, async () => {
    const stream = await writer.chat.chat({
      model: DEFAULT_CHAT_MODEL,
      messages: [{ role: "user", content: "Stream a fixture response." }],
      stream: true,
    });
    let text = "";
    for await (const chunk of stream)
      text += chunk.choices[0]?.delta.content ?? "";
    const early = await writer.chat.chat({
      model: DEFAULT_CHAT_MODEL,
      messages: [{ role: "user", content: "Cancel after one chunk." }],
      stream: true,
    });
    for await (const chunk of early) {
      void chunk;
      break;
    }
    logExampleResult(workflowName, {
      expected: "native SSE reconstruction plus early-return partial output",
      text,
      cancelled: early.controller.signal.aborted,
    });
  });
} finally {
  await shutdownRespan(respan);
}
