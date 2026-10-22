import { finish, isDirect } from "./_shared.ts";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { assert, context, scenario } from "./_shared.ts";
export async function main() {
  const result = await context.with(
    context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
    () => scenario("content-denied"),
  );
  assert.equal(result.output, "native final");
  for (const span of result.spans) {
    assert.equal(span.attributes["traceloop.entity.input"], undefined);
    assert.equal(span.attributes["traceloop.entity.output"], undefined);
  }
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
