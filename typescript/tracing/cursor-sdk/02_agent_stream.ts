import assert from "node:assert/strict";
import { scenario } from "./_shared.js";
await scenario("stream-large-resume", async (sdk, fixture) => {
  const agent = await sdk.Agent.create(fixture.options);
  const run = await agent.send(
    {
      text: "large",
      images: [
        {
          data: "Zml4dHVyZQ==",
          mimeType: "image/png",
          dimension: { width: 1, height: 1 },
        },
      ],
    },
    "JsonlLocalAgentStore" in sdk
      ? { model: { id: "cursor-fixture-next" } }
      : undefined,
  );
  const events = [];
  for await (const event of run.stream()) events.push(event);
  const result = await run.wait();
  assert.equal(result.status, "finished");
  assert.equal(events.filter((event) => event.type === "tool_call").length, 2);
  const restored = await sdk.Agent.getRun(run.id, {
    runtime: "cloud",
    agentId: agent.agentId,
    apiKey: fixture.options.apiKey,
  });
  assert.equal((await restored.wait()).status, "finished");
  const resumed = await sdk.Agent.resume(agent.agentId, fixture.options);
  const followup = await resumed.send("followup");
  assert.equal((await followup.wait()).status, "finished");
  await agent[Symbol.asyncDispose]();
  await resumed[Symbol.asyncDispose]();
  return {
    status: result.status,
    runId: run.id,
    eventTypes: events.map((event) => event.type),
    usage: result.usage,
  };
});
