export const runtime: typeof import("@flue/runtime");
export const current: boolean;
export const VECTOR: number[];
export const BODY: string;
export function nativeRuntime(options?: Record<string, unknown>): Promise<any>;
