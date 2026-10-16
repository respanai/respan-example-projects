import { defineMemory } from "eve/memory";
import { fileMemory, inMemory } from "eve/memory/file";
export default defineMemory({
  scope: "respan-synthetic",
  provider: fileMemory({ backend: inMemory() }),
});
