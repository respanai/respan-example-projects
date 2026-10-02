import { printResult, runExaExample } from "./_shared.js";

const example = "expected-error";
const result = await runExaExample({
  example,
  fn: async ({ client, mode }) => {
    if (mode === "live") return { mode, skipped: true };
    try {
      await client.search("expected Exa provider error", { numResults: 1 });
    } catch (error) {
      return {
        mode,
        error: error instanceof Error ? `${error.name}: ${error.message}` : String(error),
      };
    }
    throw new Error("expected the deterministic Exa request to fail");
  },
});
printResult(example, result.mode, result);
