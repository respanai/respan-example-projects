import { HumanMessage, SystemMessage } from "@langchain/core/messages";

import {
  chatModel,
  initRespan,
  messageText,
  shutdown,
  tracingConfig,
} from "./_shared";

export async function chatModelInvoke(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-chat-model-invoke");
  const model = chatModel(["Bonjour, Respan."]);

  try {
    const response = await model.invoke(
      [
        new SystemMessage("Translate English to French."),
        new HumanMessage("Hello, Respan."),
      ],
      tracingConfig(runtime, "chat_model_invoke"),
    );
    console.log(messageText(response));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await chatModelInvoke();
}
