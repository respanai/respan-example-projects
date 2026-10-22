import { finish, isDirect } from "./_shared.ts";
import { assert, scenario, byType } from "./_shared.ts";
export async function main() {
  const result = await scenario("sdk-stream", {
    responses: [
      {
        text: "native streamed answer",
        usage: { prompt_tokens: 19, completion_tokens: 7, total_tokens: 26 },
      },
    ],
  });
  assert.equal(result.output, "native streamed answer");
  assert.equal(
    byType(result.spans, "chat")[0].attributes["gen_ai.usage.input_tokens"],
    19,
  );
  assert.equal(result.spans.length, 2);
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
