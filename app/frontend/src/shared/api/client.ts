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

/**
 * Download an authorized file as a Blob plus the filename the server chose. Inputs: an API path
 * such as `/inventory/export.xlsx`. Output: `{ blob, filename }`; the filename comes from the
 * `Content-Disposition` header and falls back to `fallbackName`. Side effects: one authenticated
 * GET. Errors: `ApiError` with the server's plain `detail` text when present (for example a 429
 * rate limit), never the response body of a file. The caller saves the Blob.
 */
export async function downloadFile(
  path: string,
  fallbackName: string,
): Promise<{ blob: Blob; filename: string }> {
  const {
    data: { session },
  } = await auth.auth.getSession();
  if (!session) throw new ApiError("Sign in again to download this file.", 401);
  const response = await fetch(`/api${path}`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      typeof error.detail === "string"
        ? error.detail
        : "The file could not be downloaded. Try again.",
      response.status,
    );
  }
  const header = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^";]+)"?/i.exec(header);
  return { blob: await response.blob(), filename: match?.[1] ?? fallbackName };
}
