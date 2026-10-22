import { finish, isDirect } from "./_shared.ts";
import {
  createAgentSession,
  ModelRuntime,
  SessionManager,
  SettingsManager,
} from "@earendil-works/pi-coding-agent";
import { PiInstrumentor, captured, results, runId } from "./_shared.ts";
export async function main() {
  if (process.env.RESPAN_PI_LIVE !== "1") {
    results.push({
      scenario: "live-provider",
      skipped: "Set RESPAN_PI_LIVE=1, OPENAI_API_KEY and PI_CHAT_MODEL",
    });
    return;
  }
  if (!process.env.OPENAI_API_KEY || !process.env.PI_CHAT_MODEL)
    throw new Error("Live Pi requires OPENAI_API_KEY and PI_CHAT_MODEL");
  const runtime = await ModelRuntime.create({
    modelsPath: null,
    refreshOnCreate: false,
  });
  await runtime.setRuntimeApiKey("openai", process.env.OPENAI_API_KEY);
  const model = runtime.getModel("openai", process.env.PI_CHAT_MODEL);
  if (!model)
    throw new Error("PI_CHAT_MODEL is absent from the official model catalog");
  const { session } = await createAgentSession({
    modelRuntime: runtime,
    model,
    tools: [],
    sessionManager: SessionManager.inMemory(),
    settingsManager: SettingsManager.inMemory({
      compaction: { enabled: false },
      retry: { enabled: false },
    }),
  });
  const instrumentor = new PiInstrumentor({
    traceScope: "run",
    metadata: { run_id: runId, scenario: "live-provider" },
  });
  instrumentor.activate();
  const detach = instrumentor.attach(session);
  try {
    await session.prompt("Reply with a short greeting.");
    results.push({ scenario: "live-provider", completed: true });
  } finally {
    detach();
    session.dispose();
    instrumentor.deactivate();
  }
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
