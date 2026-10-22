import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const target =
  process.env.RESPAN_FLUE_PACKAGE_TARBALL ??
  (process.env.RESPAN_SDK_ROOT
    ? join(
        process.env.RESPAN_SDK_ROOT,
        "javascript-sdks/instrumentations/respan-instrumentation-flue",
      )
    : undefined);
if (!target || !existsSync(target))
  throw new Error(
    "Set RESPAN_FLUE_PACKAGE_TARBALL to a built package, or RESPAN_SDK_ROOT to the Respan checkout containing its built dist directory.",
  );
const npm = process.env.npm_execpath;
const result = npm
  ? spawnSync(
      process.execPath,
      [npm, "install", "--no-save", "--package-lock=false", target],
      { cwd: fileURLToPath(new URL("..", import.meta.url)), stdio: "inherit" },
    )
  : spawnSync("npm", ["install", "--no-save", "--package-lock=false", target], {
      cwd: fileURLToPath(new URL("..", import.meta.url)),
      stdio: "inherit",
    });
process.exitCode = result.status ?? 1;
