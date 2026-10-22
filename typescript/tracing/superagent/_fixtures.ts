import { createRequire } from "node:module";
import * as sdk from "safety-agent";

export interface FixturePlan {
  redact?: boolean;
  fail?: Error;
  fallback?: boolean;
  extra?: Record<string, unknown>;
}
export function providerFixture() {
  const original = globalThis.fetch;
  const requests: any[] = [];
  const plan: FixturePlan = {};
  process.env.OPENAI_COMPATIBLE_API_KEY = "controlled-only";
  process.env.OPENAI_API_KEY = "controlled-only";
  sdk.providers["openai-compatible"].baseUrl = "http://fixture.invalid/v1";
  sdk.providers.openai.baseUrl = "http://fixture.invalid/v1";
  globalThis.fetch = async (url, options) => {
    if (String(url).includes("/billing/usage"))
      return new Response(null, { status: 204 });
    if (!String(url).startsWith("http://fixture.invalid/"))
      throw new Error("Unexpected provider route in controlled fixture");
    const body = JSON.parse(String(options?.body));
    requests.push(body);
    if (plan.fail) throw plan.fail;
    if (plan.fallback && requests.length === 1)
      return Response.json(
        { error: { message: "controlled provider failure" } },
        { status: 429 },
      );
    const result = plan.redact
      ? { redacted: "controlled contact removed", findings: [] }
      : {
          classification: "pass",
          reasoning: "controlled explanation",
          violation_types: [],
          cwe_codes: [],
          ...plan.extra,
        };
    const text = JSON.stringify(result);
    const raw = body.input
      ? {
          id: "controlled-response",
          model: "controlled-resolved",
          output: [
            {
              type: "message",
              role: "assistant",
              content: [{ type: "output_text", text }],
            },
          ],
          usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
        }
      : {
          id: "controlled-response",
          model: "controlled-resolved",
          choices: [{ message: { role: "assistant", content: text } }],
          usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
        };
    return Response.json(raw);
  };
  return {
    requests,
    plan,
    close: () => {
      globalThis.fetch = original;
    },
  };
}

/** Exercise the actual Daytona SDK through its HTTP adapter; no remote sandbox is created. */
export async function daytonaFixture() {
  const sdkRequire = createRequire(import.meta.resolve("safety-agent"));
  const nativeRequire = createRequire(sdkRequire.resolve("@daytonaio/sdk"));
  const axios = nativeRequire("axios");
  const original = axios.defaults.adapter;
  const calls: { path: string; method: string }[] = [];
  process.env.DAYTONA_API_KEY = "controlled-only";
  process.env.DAYTONA_API_URL = "http://fixture.invalid/api";
  process.env.DAYTONA_TARGET = "controlled";
  const report = [
    JSON.stringify({
      type: "text",
      part: { text: "controlled native scan report" },
    }),
    JSON.stringify({
      type: "step_finish",
      part: { tokens: { input: 0, output: 0, reasoning: 0 }, cost: 0 },
    }),
  ].join("\n");
  axios.defaults.adapter = async (config: any) => {
    const path = String(config.url);
    calls.push({ path, method: config.method });
    const data = path.includes("toolbox-proxy-url")
      ? { url: "http://fixture.invalid/toolbox" }
      : path.includes("/process/execute")
        ? { result: report, exitCode: 0 }
        : path.includes("/sandbox")
          ? {
              id: "controlled-sandbox",
              name: "controlled",
              state: "started",
              regionId: "controlled",
              labels: { "code-toolbox-language": "typescript" },
            }
          : {};
    return { data, status: 200, statusText: "OK", headers: {}, config };
  };
  return {
    calls,
    close: () => {
      axios.defaults.adapter = original;
    },
  };
}
