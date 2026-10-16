import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";

import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

export async function promptChainInvoke(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-prompt-chain-invoke");
  const prompt = ChatPromptTemplate.fromMessages([
    ["system", "Translate the user text to {language}."],
    ["human", "{text}"],
  ]);
  const model = chatModel(["Bonjour, Respan."]);
  const chain = prompt.pipe(model).pipe(new StringOutputParser());

  try {
    const result = await chain.invoke(
      { language: "French", text: "Hello, Respan." },
      tracingConfig(runtime, "prompt_chain_invoke"),
    );
    console.log(result);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await promptChainInvoke();
}
