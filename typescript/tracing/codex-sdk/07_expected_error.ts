import {
  assert,
  captured,
  codexThreadOptions,
  createCodex,
  createRespan,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
  LIVE,
} from "./_shared.js";
const name = "codex-sdk-ts-expected-error";
const respan = createRespan(name);
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    let errors = 0;
    for (const scenario of ["failure", "process-error", "invalid-json"]) {
      const t = createCodex(
        LIVE
          ? { codexPathOverride: "/tmp/respan-missing-codex-binary" }
          : { scenario },
      ).startThread(codexThreadOptions());
      await assert.rejects(t.run("controlled failure"));
      errors++;
    }
    const controller = new AbortController();
    controller.abort();
    await assert.rejects(
      createCodex()
        .startThread(codexThreadOptions())
        .run("controlled abort", { signal: controller.signal }),
    );
    errors++;
    return { controlledFailures: errors };
  });
  assert.equal(
    captured.filter(
      (s) =>
        s.attrs["respan.entity.log_type"] === "agent" &&
        (s.status as { code: number }).code === 2,
    ).length,
    4,
  );
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
