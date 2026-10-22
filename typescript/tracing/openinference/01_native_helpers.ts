import { context } from "@opentelemetry/api";
import type { Respan } from "@respan/respan";
import {
  traceAgent,
  traceChain,
  traceTool,
  setMetadata,
  setSession,
  setUser,
  setTags,
  setPromptTemplate,
  observe,
} from "@arizeai/openinference-core";
import { OpenInferenceSpanKind } from "@arizeai/openinference-semantic-conventions";
import { workflow } from "./_shared.js";
export async function run(respan: Respan) {
  const tool = traceTool(
    (input: { query: string }) => ({
      found: true,
      count: 0,
      query: input.query,
    }),
    { name: "lookup" },
  );
  const chain = traceChain((value: unknown) => ({ value, ok: false }), {
    name: "summarize",
  });
  const agent = traceAgent((query: string) => chain(tool({ query })), {
    name: "support",
  });
  class Planner {
    @observe({ name: "plan", kind: OpenInferenceSpanKind.CHAIN }) plan(
      text: string,
    ) {
      return { text, steps: ["lookup", "summarize"] };
    }
  }
  return workflow(respan, "native-helpers", () => {
    let ctx = context.active();
    ctx = setMetadata(ctx, { native_helper: true });
    ctx = setSession(ctx, { sessionId: "fixture-session" });
    ctx = setUser(ctx, { userId: "fixture-user" });
    ctx = setTags(ctx, ["fixture", "openinference"]);
    ctx = setPromptTemplate(ctx, {
      template: "Answer {question}",
      variables: { question: "tracing" },
      version: "v1",
    });
    return context.with(ctx, () => ({
      agent: agent("How do native helpers nest?"),
      plan: new Planner().plan("trace helpers"),
    }));
  });
}
