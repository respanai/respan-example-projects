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
  workflowName = "writer.raw_responses.workflow";
try {
  await runWithWriterWorkflow(respan, workflowName, async () => {
    const request = {
      model: DEFAULT_CHAT_MODEL,
      messages: [
        { role: "user" as const, content: "Observe raw and parsed responses." },
      ],
    };
    const raw = await writer.chat.chat(request).asResponse();
    const promise = writer.chat.chat(request),
      paired = await promise.withResponse();
    if (paired.data !== (await promise))
      throw new Error("Writer result identity changed");
    logExampleResult(workflowName, {
      expected:
        "raw response emits metadata without consuming its body; withResponse captures content once",
      rawStatus: raw.status,
      rawBodyUnused: !raw.bodyUsed,
      pairedStatus: paired.response.status,
      text: paired.data.choices[0]?.message.content,
    });
  });
} finally {
  await shutdownRespan(respan);
}
