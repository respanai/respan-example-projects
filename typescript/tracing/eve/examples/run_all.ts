import {
  runBasicTurn,
  runSubagentLineage,
  runToolCall,
  runValuesAndError,
  runContinuation,
  runStreamAndLarge,
  runMemory,
} from "./_cases.js";
import { runWithEveServer } from "./_shared.js";

await runWithEveServer(async (client) => [
  await runBasicTurn(client),
  await runToolCall(client),
  await runSubagentLineage(client),
  ...(await runValuesAndError(client)),
  await runContinuation(client),
  await runStreamAndLarge(client),
  ...(await runMemory(client)),
]);
