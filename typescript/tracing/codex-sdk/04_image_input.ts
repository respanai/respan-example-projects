import {
  assert,
  captured,
  codexThreadOptions,
  createCodex,
  createDemoImage,
  createRespan,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
  LIVE,
} from "./_shared.js";
const name = "codex-sdk-ts-image-input";
const respan = createRespan(name);
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const image = await createDemoImage();
    const parts: Array<
      { type: "text"; text: string } | { type: "local_image"; path: string }
    > = Array.from({ length: 80 }, (_, i) => ({
      type: "text",
      text: `controlled text part ${i}`,
    }));
    parts.splice(40, 0, { type: "local_image", path: image });
    const result = await createCodex()
      .startThread(codexThreadOptions())
      .run(parts);
    return {
      finalResponse: result.finalResponse,
      inputPartCount: parts.length,
    };
  });
  if (!LIVE) {
    const a = captured.find(
      (s) => s.attrs["respan.entity.log_type"] === "agent",
    )!;
    const parts = JSON.parse(String(a.attrs["traceloop.entity.input"]))[0]
      .content;
    assert.equal(parts.length, 81);
    assert.equal(parts[40].type, "local_image");
  }
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
