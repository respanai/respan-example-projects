import { defineTool } from "eve/tools";
import { z } from "zod";
export default defineTool({
  description: "Raise a deterministic synthetic tool failure.",
  inputSchema: z.object({}),
  execute() {
    const error = new Error("Synthetic Eve tool error");
    error.name = "SyntheticToolError";
    throw error;
  },
});
