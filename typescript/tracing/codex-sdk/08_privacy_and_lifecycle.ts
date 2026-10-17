import {
  assert,
  captured,
  codexThreadOptions,
  createCodex,
  createRespan,
  logExampleResult,
  ownerFor,
  runWithCodexWorkflow,
  shutdownRespan,
} from "./_shared.js";
process.env.RESPAN_TRACE_CONTENT = "false";
const name = "codex-sdk-ts-privacy-lifecycle";
const respan = createRespan(name, {
  traceContent: false,
  captureItemSpans: false,
});
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const owner = ownerFor(respan);
    assert.equal(owner.isActive(), true);
    const pending = createCodex()
      .startThread(codexThreadOptions())
      .run("private controlled input");
    owner.deactivate();
    const result = await pending;
    assert.equal(owner.isActive(), false);
    await owner.activate();
    const stream = await createCodex()
      .startThread(codexThreadOptions())
      .runStreamed("private stream");
    await stream.events.next();
    await stream.events.return(undefined as never);
    return {
      inFlightDrained: result.finalResponse.length > 0,
      reactivated: owner.isActive(),
      cancelled: true,
    };
  });
  for (const s of captured) {
    assert.equal(s.attrs["traceloop.entity.input"], undefined);
    assert.equal(s.attrs["traceloop.entity.output"], undefined);
  }
  assert.equal(
    captured.filter((s) => s.attrs["respan.entity.log_type"] === "agent")
      .length,
    2,
  );
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
