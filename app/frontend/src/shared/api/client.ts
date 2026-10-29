import { auth } from "../auth/client";

/** Safe server-visible error; payloads and bearer credentials are never attached to it. */
export class ApiError extends Error {
  /** Preserve status so features can distinguish a stale revision, expired session, and transient failure. */
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

/** Call the same-origin business API with the current bearer token and optional stable mutation identity. */
export async function request<T>(
  path: string,
  init: RequestInit = {},
  operationId?: string,
): Promise<T> {
  const {
    data: { session },
  } = await auth.auth.getSession();
  if (!session)
    throw new ApiError("Sign in to access the sales workspace.", 401);
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(operationId ? { "Idempotency-Key": operationId } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "The request failed. Please try again." }));
    throw new ApiError(
      typeof error.detail === "string"
        ? error.detail
        : "Check the entered values and try again.",
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

/** Fetch an authorized document as a temporary browser object URL; the caller must revoke it when closed. */
export async function documentUrl(path: string): Promise<string> {
  const {
    data: { session },
  } = await auth.auth.getSession();
  if (!session) throw new ApiError("Sign in again to view this document.", 401);
  const response = await fetch(`/api${path}`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!response.ok)
    throw new ApiError(
      "The document could not be loaded. Refresh and try again.",
      response.status,
    );
  return URL.createObjectURL(await response.blob());
}
