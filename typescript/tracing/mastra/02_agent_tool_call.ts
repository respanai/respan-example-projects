import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import {
  createRuntime,
  createToolCallModel,
  EXAMPLE_RUN_ID,
  getTraceWorkflowName,
  runWithRespanWorkflow,
} from "./_shared.js";

const workflowName = "Mastra Tool Example";

const getWeather = createTool({
  id: "get_weather",
  description: "Get a deterministic weather report for a city.",
  inputSchema: z.object({
    city: z.string(),
  }),
  execute: async ({ city }) => ({
    city,
    forecast: "sunny",
    temperature_f: 72,
  }),
});

const weatherAgent = new Agent({
  id: "mastra-weather-agent",
  name: "Mastra Weather Agent",
  instructions: "Use the get_weather tool before answering weather questions.",
  model: createToolCallModel(),
  tools: { getWeather },
});

const { mastra, respan } = createRuntime({ weatherAgent });

const text = await runWithRespanWorkflow(
  mastra,
  respan,
  workflowName,
  async () => {
    const agent = mastra.getAgent("weatherAgent");
    const result = await agent.generate(
      "Use the weather tool and tell me the weather in Tokyo.",
    );
    return result.text;
  },
);

console.log(
  JSON.stringify(
    {
      workflowName: getTraceWorkflowName(workflowName),
      runId: EXAMPLE_RUN_ID,
      text,
    },
    null,
    2,
  ),
);
