import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_privacy_constructor_headers";
const privatePromptMarker = "private-prompt-must-not-be-exported";
const privateResponseMarker = "private-response-must-not-be-exported";
const runtime = await createRuntime({
  traceContent: false,
  loggerHeaders: {
    "Helicone-User-Id": "constructor-header-user",
    "Helicone-Session-Id": "constructor-header-thread",
    "Helicone-Property-source": "constructor-header",
    Authorization: "local-only-auth-marker",
    "X-Internal-Token": "local-only-token-marker",
  },
});

try {
  await runWorkflow(runtime, workflowName, async () => {
    const now = Date.now();
    await runtime.logger.sendLog(
      {
        model: "privacy-model",
        messages: [{ role: "user", content: privatePromptMarker }],
        tools: [{
          name: "private_tool",
          description: "private-tool-description-must-not-be-exported",
          parameters: { type: "object", properties: { private: { type: "string" } } },
        }],
      },
      {
        choices: [{
          message: { role: "assistant", content: privateResponseMarker },
        }],
        usage: { prompt_tokens: 4, completion_tokens: 3, total_tokens: 7 },
      },
      {
        startTime: now - 5,
        endTime: now,
        status: 200,
        additionalHeaders: {
          "Helicone-Property-scenario": "privacy",
        },
      },
    );
  });

  logResult(workflowName, {
    traceContent: false,
    expectedCustomer: "constructor-header-user",
    expectedThread: "constructor-header-thread",
    expectedProperties: ["source", "scenario"],
    forbiddenMarkers: [
      privatePromptMarker,
      privateResponseMarker,
      "private-tool-description-must-not-be-exported",
      "local-only-auth-marker",
      "local-only-token-marker",
    ],
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
