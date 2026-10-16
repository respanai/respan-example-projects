import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import "../_env.js";
const root = fileURLToPath(new URL("..", import.meta.url));
const require = createRequire(import.meta.url);
const eveRoot = dirname(require.resolve("eve/package.json"));
const { version } = JSON.parse(
  await readFile(join(eveRoot, "package.json"), "utf8"),
);
const current = Number(version.split(".")[1]) >= 62;
const app = join(root, ".respan-eve", "app");
await rm(app, { recursive: true, force: true });
await mkdir(app, { recursive: true });
await cp(join(root, "agent"), join(app, "agent"), { recursive: true });
await writeFile(
  join(app, "package.json"),
  JSON.stringify({
    private: true,
    type: "module",
    dependencies: {
      eve: version,
      ai: current ? "7.0.136" : "7.0.26",
      zod: "4.4.3",
    },
  }),
);
await cp(join(root, "profiles/capture.ts"), join(app, "agent/capture.ts"));
await writeFile(
  join(app, "_env.ts"),
  `export const EXAMPLE_RUN_ID=process.env.RESPAN_EXAMPLE_RUN_ID;\nexport const RESPAN_API_KEY=process.env.RESPAN_API_KEY;\nexport const RESPAN_BASE_URL=process.env.RESPAN_BASE_URL;\n`,
);
if (current) {
  await mkdir(join(app, "agent", "instrumentation"), { recursive: true });
  await mkdir(join(app, "agent/memory"), { recursive: true });
  await cp(
    join(root, "profiles/current/memory.ts"),
    join(app, "agent/memory/profile.ts"),
  );
  for (const name of ["otel", "respan"])
    await cp(
      join(root, "profiles", "current", name + ".ts"),
      join(app, "agent", "instrumentation", name + ".ts"),
    );
  for (const agent of [
    join(app, "agent"),
    join(app, "agent", "subagents", "researcher"),
  ]) {
    await mkdir(join(agent, "sandbox"), { recursive: true });
    await cp(
      join(root, "profiles/current/sandbox.ts"),
      join(agent, "sandbox/sandbox.ts"),
    );
  }
  await mkdir(join(app, "agent/channels"), { recursive: true });
  await cp(
    join(root, "profiles/current/channel.ts"),
    join(app, "agent/channels/eve.ts"),
  );
} else
  await cp(
    join(root, "profiles/legacy/instrumentation.ts"),
    join(app, "agent/instrumentation.ts"),
  );
const result = spawnSync(
  process.execPath,
  [join(eveRoot, "bin/eve.js"), "build"],
  {
    cwd: app,
    env: { ...process.env, EVE_TELEMETRY_DISABLED: "1" },
    stdio: "inherit",
  },
);
process.exitCode = result.status ?? 1;
