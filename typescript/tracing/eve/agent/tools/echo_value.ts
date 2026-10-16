import { defineTool } from "eve/tools";
import { z } from "zod";
export default defineTool({
  description: "Return a synthetic false, zero, or empty string unchanged.",
  inputSchema: z.object({
    value: z.union([z.boolean(), z.number(), z.string()]),
  }),
  execute: ({ value }) => value,
});
