import { eveChannel } from "eve/channels/eve";
import { none } from "eve/channels/auth";
// The runner binds only localhost and sends deterministic synthetic messages.
export default eveChannel({ auth: [none()], audience: "public" });
