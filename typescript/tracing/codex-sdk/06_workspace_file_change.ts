import {
  assert,
  captured,
  codexThreadOptions,
  createCodex,
  createRespan,
  createScratchWorkspace,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
  LIVE,
} from "./_shared.js";
const name = "codex-sdk-ts-file-change";
const respan = createRespan(name);
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const scratch = await createScratchWorkspace("file-change");
    const result = await createCodex()
      .startThread(
        codexThreadOptions({
          workingDirectory: scratch,
          sandboxMode: "workspace-write",
        }),
      )
      .run("Create controlled.txt containing controlled text.");
    if (!LIVE) assert.ok(result.items.some((i) => i.type === "file_change"));
    return {
      finalResponse: result.finalResponse,
      itemTypes: result.items.map((i) => i.type),
    };
  });
  if (!LIVE) {
    const file = captured.find(
      (s) =>
        JSON.parse(String(s.attrs["respan.metadata"] || "{}"))
          .codex_item_type === "file_change",
    )!;
    assert.deepEqual(JSON.parse(String(file.attrs["traceloop.entity.input"])), [
      { path: "controlled.txt", kind: "update" },
    ]);
  }
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
