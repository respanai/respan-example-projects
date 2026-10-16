import { context } from "@opentelemetry/api";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { MODEL, LIVE, createRuntime, runCase, log } from "./_shared.js";
const caseId = "privacy_and_error";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    await context.with(
      context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
      () =>
        runtime.client.messages.create({
          model: MODEL,
          max_tokens: 512,
          messages: [{ role: "user", content: "Private model payload." }],
        }),
    );
    if (LIVE) return { privateCall: true, fixtureErrorSkipped: true };
    try {
      await runtime.client.messages.create({
        model: "fixture-error",
        max_tokens: 20,
        messages: [{ role: "user", content: "Controlled HTTP failure." }],
      });
      throw Error("Expected controlled error");
    } catch (error) {
      if (
        !(error instanceof Error) ||
        error.message === "Expected controlled error"
      )
        throw error;
      return {
        privateCall: true,
        errorType: error.name,
        status: (error as { status?: number }).status,
      };
    }
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
