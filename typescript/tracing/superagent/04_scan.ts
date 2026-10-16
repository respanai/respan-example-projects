import assert from "node:assert/strict";
import { runExample } from "./_shared.js";
import { daytonaFixture } from "./_fixtures.js";
await runExample("scan", async ({ client, fixture }) => {
  const transport = fixture ? await daytonaFixture() : undefined;
  try {
    const result = await client.scan({
      repo:
        process.env.SUPERAGENT_SCAN_REPO ??
        "https://example.invalid/controlled-repo",
      branch: "main",
    });
    if (transport) {
      assert.equal(result.result, "controlled native scan report");
      assert.ok(transport.calls.some((c) => c.method === "delete"));
    }
    return result;
  } finally {
    transport?.close();
  }
});
