import {
  assert,
  codexThreadOptions,
  createCodex,
  createRespan,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
  verifyCaptured,
} from "./_shared.js";
const name = "codex-sdk-ts-streaming";
const respan = createRespan(name);
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const stream = await createCodex()
      .startThread(codexThreadOptions())
      .runStreamed("Stream a controlled result.");
    const iterator = stream.events;
    const eventTypes: string[] = [];
    for await (const event of iterator) eventTypes.push(event.type);
    assert.equal(stream.events, iterator);
    assert.ok(eventTypes.includes("turn.completed"));
    return { eventTypes };
  });
  verifyCaptured();
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
