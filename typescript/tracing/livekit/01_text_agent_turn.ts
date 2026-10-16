import { agentTurn, assertCaptured, runExample } from "./_shared.js";
await runExample("TypeScript LiveKit Native Text Turn", async () => {
  const result = await agentTurn();
  assertCaptured(
    (span) =>
      span.attributes["gen_ai.completion.0.content"] ===
      "The native transport completed this turn.",
  );
  return result;
});
