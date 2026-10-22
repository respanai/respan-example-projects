import { RunnableLambda } from "@langchain/core/runnables";
import {
  addRespanCallback,
  getCallbackHandler,
} from "@respan/instrumentation-langchain";

import {
  getWeather,
  initRespan,
  shutdown,
  type ExampleRuntime,
} from "./_shared";

function langflowConfig(
  runtime: ExampleRuntime,
  name: string,
  handler: ReturnType<typeof getCallbackHandler>,
) {
  const config = {
    runName: name,
    tags: ["respan-langchain-example", "langflow", name],
    metadata: {
      example: name,
      custom_identifier: process.env.RESPAN_EXAMPLE_RUN_ID,
      framework: "langflow",
      langflow_component: "RoutingComponent",
    },
  };
  if (!runtime.enabled) return config;
  return addRespanCallback(config, handler);
}

export async function langflowComponentGrouping(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-langflow-component-grouping",
  );
  const handler = getCallbackHandler();
  const routeDepartment = RunnableLambda.from(
    (input: { department: string }) => `${input.department}-workspace`,
  );

  try {
    const route = await routeDepartment.invoke(
      { department: "security" },
      langflowConfig(runtime, "langflow_route_department", handler),
    );
    const weather = await getWeather.invoke(
      { city: "Dublin" },
      langflowConfig(runtime, "langflow_get_weather", handler),
    );
    console.log(`${route}: ${weather}`);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await langflowComponentGrouping();
}
