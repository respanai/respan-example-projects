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
  CURRENT_FEATURES,
  LIVE,
} from "./_shared.js";
import type {
  CodexOptions,
  ThreadOptions,
  TurnOptions,
} from "@openai/codex-sdk";
import fs from "node:fs/promises";
import path from "node:path";
const name = "codex-sdk-ts-current-options";
if (!CURRENT_FEATURES) {
  logExampleResult(name, {
    skipped:
      "Codex0.162 current-only config/thread/turn options and cache-write usage",
  });
} else {
  const respan = createRespan(name);
  try {
    const summary = await runWithCodexWorkflow(respan, name, async () => {
      const requestPath = path.join(
        await createScratchWorkspace("current"),
        "request.json",
      );
      const codexOptions: CodexOptions & { configOverrides: string[] } = {
        configOverrides: ['controlled_flag="raw"'],
      };
      const threadOptions: ThreadOptions & { threadSource: string } = {
        ...codexThreadOptions(),
        threadSource: "controlled-source",
      };
      const turnOptions: TurnOptions & { cyberAccessProgram: "standard" } = {
        cyberAccessProgram: "standard",
      };
      const result = await createCodex({ requestPath, codexOptions })
        .startThread(threadOptions)
        .run("controlled current options", turnOptions);
      if (!LIVE) {
        const { args } = JSON.parse(await fs.readFile(requestPath, "utf8"));
        assert.ok(args.includes('controlled_flag="raw"'));
        assert.ok(args.some((v: string) => v.includes("controlled-source")));
        assert.ok(args.some((v: string) => v.includes("standard")));
      }
      return { usage: result.usage };
    });
    if (!LIVE) {
      const a = captured.find(
        (s) => s.attrs["respan.entity.log_type"] === "agent",
      )!;
      assert.equal(
        JSON.parse(String(a.attrs["respan.metadata"])).codex_turn_usage
          .cache_write_input_tokens,
        2,
      );
    }
    logExampleResult(name, summary);
  } finally {
    await shutdownRespan(respan);
  }
}
