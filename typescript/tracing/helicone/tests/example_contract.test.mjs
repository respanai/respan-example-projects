import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const exampleDir = new URL("../", import.meta.url);
const scenarioFiles = [
  "01_log_request_chat_tools.ts",
  "02_log_stream.ts",
  "03_log_single_stream.ts",
  "04_single_request_builder.ts",
  "05_custom_events.ts",
  "06_expected_error.ts",
  "07_anthropic_direct.ts",
  "08_delayed_builder.ts",
  "09_privacy_constructor_headers.ts",
  "10_provider_stream_shapes.ts",
];

test("example set locks ten scenarios and both exact marker names", async () => {
  const [shared, runner] = await Promise.all([
    readFile(new URL("_shared.ts", exampleDir), "utf8"),
    readFile(new URL("run_all.ts", exampleDir), "utf8"),
  ]);
  assert.match(shared, /run_id:\s*RUN_ID/);
  assert.match(shared, /example_run_id:\s*RUN_ID/);
  assert.match(runner, /RESPAN_EXAMPLE_RUN_ID:\s*runId/);
  assert.match(runner, /setTimeout/);
  assert.match(runner, /results\.some/);
  const singleBuilder = await readFile(
    new URL("04_single_request_builder.ts", exampleDir),
    "utf8",
  );
  assert.match(singleBuilder, /runtime\.logger\.sendLog\(/);
  assert.match(singleBuilder, /\.toReadableStream\(/);
  assert.match(singleBuilder, /\.addAdditionalHeaders\(/);
  for (const fileName of scenarioFiles) {
    assert.ok(runner.includes(`"${fileName}"`), `${fileName} missing from run_all`);
    await readFile(new URL(fileName, exampleDir), "utf8");
  }
});

test("examples contain no Helicone credential dependency or credential literal", async () => {
  const sources = await Promise.all(
    ["_shared.ts", ...scenarioFiles].map((fileName) =>
      readFile(new URL(fileName, exampleDir), "utf8")
    ),
  );
  const combined = sources.join("\n");
  assert.doesNotMatch(combined, /process\.env\.HELICONE_API_KEY/);
  assert.doesNotMatch(combined, /sk-[A-Za-z0-9_-]{8,}/);
  assert.doesNotMatch(combined, /Bearer\s+[A-Za-z0-9_-]{8,}/);
});

test("privacy and delayed-builder scenarios lock their semantic contracts", async () => {
  const [privacy, delayed, customEvents] = await Promise.all([
    readFile(new URL("09_privacy_constructor_headers.ts", exampleDir), "utf8"),
    readFile(new URL("08_delayed_builder.ts", exampleDir), "utf8"),
    readFile(new URL("05_custom_events.ts", exampleDir), "utf8"),
  ]);
  assert.match(privacy, /traceContent:\s*false/);
  assert.match(privacy, /Helicone-User-Id/);
  assert.match(privacy, /Helicone-Session-Id/);
  assert.match(delayed, /delayed_builder_creation/);
  assert.match(delayed, /delayed_builder_send_context/);
  assert.ok(delayed.indexOf("logBuilder(") < delayed.indexOf("createdBuilder.sendLog()"));
  assert.match(delayed, /return\s+\{\s*builderCreated:\s*true\s*\}/);
  assert.doesNotMatch(delayed, /return\s+runtime\.logger\.logBuilder\s*\(/);
  assert.doesNotMatch(delayed, /return\s+(?:builder|runtime\.logger)\b/);
  assert.doesNotMatch(delayed, /JSON\.stringify\([^)]*(?:builder|logger|apiKey)/);
  assert.doesNotMatch(delayed, /\bapiKey\b/);
  for (const field of [
    "authToken",
    "bearerToken",
    "idToken",
    "sessionToken",
    "privateKey",
    "clientSecret",
    "credential",
    "credentials",
    "heliconeAuth",
    "promptTokens",
    "completionTokens",
    "tokenCount",
    "tokenizer",
  ]) {
    assert.ok(customEvents.includes(field), `${field} missing from redaction probe`);
  }
  assert.match(customEvents, /serializedPayload:\s*JSON\.stringify\s*\(/);
  assert.match(customEvents, /serialized-private-sentinel/);
  assert.match(customEvents, /serialized-tokenizer/);
});
