import { runExample, MODEL } from "./_shared.js";
await runExample("workflow", async ({ runtime, client, fixture }) => {
  const guard = await runtime.withTask({ name: "classify" }, () =>
    client.guard({ input: "controlled workflow", model: MODEL, chunkSize: 0 }),
  );
  if (fixture) fixture.plan.redact = true;
  const redact = await runtime.withTask({ name: "remove-contact" }, () =>
    client.redact({ input: "controlled contact", model: MODEL }),
  );
  return { guard, redact };
});
