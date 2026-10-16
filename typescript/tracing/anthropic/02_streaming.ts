import { MODEL, createRuntime, runCase, log } from "./_shared.js";
const caseId = "streaming";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    const params = {
      model: MODEL,
      max_tokens: 2048,
      messages: [
        {
          role: "user" as const,
          content: "Stream tool arguments and thinking.",
        },
      ],
      stream: true as const,
    };
    const pending = runtime.client.messages.create(params);
    const { data: stream, response } = await pending.withResponse();
    const controller = stream.controller;
    let futureDeltas = 0;
    let events = 0,
      text = "",
      toolFragments = "";
    for await (const event of stream) {
      events++;
      if (
        (event as { delta?: { type?: string } }).delta?.type === "future_delta"
      )
        futureDeltas++;
      if (event.type === "content_block_delta") {
        if (event.delta.type === "text_delta") text += event.delta.text;
        if (event.delta.type === "input_json_delta")
          toolFragments += event.delta.partial_json;
      }
    }
    if (stream.controller !== controller)
      throw Error("Native controller changed");
    const early = await runtime.client.messages.create(params);
    const iterator = early[Symbol.asyncIterator]();
    await iterator.next();
    await iterator.return?.();
    const aborted = await runtime.client.messages.create(params);
    const abortIterator = aborted[Symbol.asyncIterator]();
    await abortIterator.next();
    aborted.controller.abort();
    try {
      await abortIterator.next();
    } catch {}
    await abortIterator.return?.();
    const beforeFirstNext = await runtime.client.messages.create(params);
    beforeFirstNext.controller.abort();
    await new Promise<void>((resolve) => setImmediate(resolve));
    return {
      futureDeltas,
      abortedBeforeFirstNext: true,
      status: response.status,
      events,
      text,
      toolFragments,
      earlyReturn: true,
      aborted: true,
    };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
