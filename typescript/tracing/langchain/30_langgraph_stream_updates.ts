import { END, START, StateGraph, StateSchema } from "@langchain/langgraph";
import { z } from "zod";

import { initRespan, shutdown, tracingConfig } from "./_shared";

const State = new StateSchema({
  topic: z.string(),
  note: z.string().default(""),
});

export async function langgraphStreamUpdates(): Promise<void> {
  const runtime = await initRespan(
    "typescript-langchain-langgraph-stream-updates",
  );
  const graph = new StateGraph(State)
    .addNode("refineTopic", (state: typeof State.State) => ({
      topic: `${state.topic} and callbacks`,
    }))
    .addNode("writeNote", (state: typeof State.State) => ({
      note: `Tracing ${state.topic}`,
    }))
    .addEdge(START, "refineTopic")
    .addEdge("refineTopic", "writeNote")
    .addEdge("writeNote", END)
    .compile();

  try {
    const stream = await graph.stream(
      { topic: "LangGraph" },
      {
        ...tracingConfig(runtime, "langgraph_stream_updates", {
          framework: "langgraph",
        }),
        streamMode: "updates",
      },
    );
    const updates: string[] = [];
    for await (const chunk of stream) {
      updates.push(Object.keys(chunk).join(","));
    }
    console.log(updates.join(" -> "));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await langgraphStreamUpdates();
}
