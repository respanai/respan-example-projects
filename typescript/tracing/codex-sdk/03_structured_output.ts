import {
  assert,
  codexThreadOptions,
  createCodex,
  createRespan,
  createScratchWorkspace,
  logExampleResult,
  runWithCodexWorkflow,
  shutdownRespan,
  LIVE,
} from "./_shared.js";
import fs from "node:fs/promises";
import path from "node:path";
const name = "codex-sdk-ts-structured-output";
const respan = createRespan(name);
const schema = {
  type: "object",
  properties: { ok: { type: "boolean" }, value: { type: "integer" } },
  required: ["ok", "value"],
  additionalProperties: false,
};
try {
  const summary = await runWithCodexWorkflow(respan, name, async () => {
    const requestPath = path.join(
      await createScratchWorkspace("schema"),
      "request.json",
    );
    const result = await createCodex({ scenario: "structured", requestPath })
      .startThread(codexThreadOptions())
      .run("Return JSON with ok true and value zero.", {
        outputSchema: schema,
      });
    if (!LIVE) {
      assert.deepEqual(JSON.parse(result.finalResponse), {
        ok: true,
        value: 0,
      });
      assert.deepEqual(
        JSON.parse(await fs.readFile(requestPath, "utf8")).schema,
        schema,
      );
    }
    return { finalResponse: result.finalResponse };
  });
  logExampleResult(name, summary);
} finally {
  await shutdownRespan(respan);
}
