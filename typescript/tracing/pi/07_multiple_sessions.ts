import { finish, isDirect } from "./_shared.ts";
import { assert, scenario } from "./_shared.ts";
export async function main() {
  const first = await scenario("independent-session-1");
  const second = await scenario("independent-session-2");
  assert.notEqual(
    first.spans[0].spanContext().traceId,
    second.spans[0].spanContext().traceId,
  );
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
