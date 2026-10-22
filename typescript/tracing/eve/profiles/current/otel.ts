import { otel } from "eve/instrumentation/otel";
export default otel({
  functionId: "eve_typescript_" + process.env.RESPAN_EXAMPLE_RUN_ID,
  tracePolicy: () => ({ emit: true, recordInputs: true, recordOutputs: true }),
});
