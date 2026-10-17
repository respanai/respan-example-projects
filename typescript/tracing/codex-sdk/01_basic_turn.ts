import {
  assert,
  captured,
  codexThreadOptions,
  createCodex,
  createRespan,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
  verifyCaptured,
  LIVE,
} from "./_shared.js";
const name = "codex-sdk-ts-basic";
const respan = createRespan(name);
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const result = await createCodex()
      .startThread(codexThreadOptions())
      .run("Summarize the controlled workspace.");
    if (!LIVE) {
      assert.equal(result.items.length, 8);
      assert.equal(result.finalResponse, "controlled native result");
    }
    return {
      finalResponse: result.finalResponse,
      itemTypes: result.items.map((i) => i.type),
      usage: result.usage,
    };
  });
  verifyCaptured();
  if (!LIVE) {
    const m = captured.find(
      (s) =>
        JSON.parse(String(s.attrs["respan.metadata"] || "{}")).codex_item_id ===
        "mcp-1",
    )!;
    assert.equal(
      JSON.parse(String(m.attrs["traceloop.entity.input"])).arguments
        .definitions.length,
      82,
    );
    assert.equal(
      JSON.parse(String(m.attrs["traceloop.entity.output"])).structured_content
        .vector.length,
      5001,
    );
  }
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
