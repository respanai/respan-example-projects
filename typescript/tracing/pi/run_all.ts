import { finish } from "./_shared.ts";
import { main as scenario1 } from "./01_sdk_stream.ts";
import { main as scenario2 } from "./02_extension_tools.ts";
import { main as scenario3 } from "./03_errors_abort.ts";
import { main as scenario4 } from "./04_compaction_branch.ts";
import { main as scenario5 } from "./05_sessions_steering.ts";
import { main as scenario6 } from "./06_capture_policy.ts";
import { main as scenario7 } from "./07_multiple_sessions.ts";
import { main as scenario8 } from "./08_live_provider.ts";

try {
  await scenario1();
  await scenario2();
  await scenario3();
  await scenario4();
  await scenario5();
  await scenario6();
  await scenario7();
  await scenario8();
} finally {
  await finish();
}
