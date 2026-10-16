import { llm, voice } from "@livekit/agents";
import { z } from "zod";
import { agentTurn, runExample } from "./_shared.js";
await runExample("TypeScript LiveKit Native Agent Handoff", async () => {
  const billing = new voice.Agent({
    id: "billing",
    instructions: "Handle billing questions.",
  });
  return agentTurn({
    tool: "handoff_to_billing",
    tools: {
      handoff_to_billing: llm.tool({
        description: "Transfer to billing.",
        parameters: z.object({ city: z.string() }),
        execute: async () =>
          llm.handoff({ agent: billing, returns: "Transferred to billing." }),
      }),
    },
  });
});
