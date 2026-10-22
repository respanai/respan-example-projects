import { createAgent, toolStrategy } from "langchain";
import { z } from "zod";

import { chatModel, initRespan, shutdown, tracingConfig } from "./_shared";

const ContactInfo = z.object({
  name: z.string(),
  email: z.string(),
});

export async function agentStructuredOutput(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-agent-structured-output",
  );
  const model = chatModel([
    {
      toolCalls: [
        {
          id: "call_extract_contact",
          name: "extract-1",
          args: { name: "Ada Lovelace", email: "ada@example.com" },
        },
      ],
    },
  ]);
  const agent = createAgent({
    model,
    tools: [],
    responseFormat: toolStrategy(ContactInfo),
    version: "v1",
  });

  try {
    const result = await agent.invoke(
      {
        messages: [
          {
            role: "user",
            content: "Extract contact info: Ada Lovelace, ada@example.com",
          },
        ],
      },
      tracingConfig(runtime, "agent_structured_output", {
        framework: "langgraph",
      }),
    );
    console.log(JSON.stringify(result.structuredResponse));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await agentStructuredOutput();
}
