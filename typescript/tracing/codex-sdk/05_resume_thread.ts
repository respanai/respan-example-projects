import {
  assert,
  codexThreadOptions,
  createCodex,
  createRespan,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
} from "./_shared.js";
const name = "codex-sdk-ts-resume-thread";
const respan = createRespan(name);
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const codex = createCodex();
    const first = codex.startThread(codexThreadOptions());
    await first.run("Remember the controlled word respan.");
    assert.ok(first.id);
    const resumed = codex.resumeThread(first.id, codexThreadOptions());
    const result = await resumed.run("Return the controlled word.");
    assert.equal(resumed.id, first.id);
    return { threadId: first.id, finalResponse: result.finalResponse };
  });
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
