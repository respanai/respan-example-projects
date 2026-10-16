import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function langchainInstrumentationQuickstart(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-quickstart");
  const model = chatModel(["Hello from a traced TypeScript LangChain run."]);
  try {
    const response = await model.invoke(
      [
        new SystemMessage("Reply in one short sentence."),
        new HumanMessage("Say hello to Respan tracing."),
      ],
      tracingConfig(runtime, "quickstart"),
    );
    console.log(response.content);
  } finally {
    await shutdown(runtime);
  }
}
if (import.meta.url === `file://${process.argv[1]}`)
  await langchainInstrumentationQuickstart();
