import { API_URL } from "@/lib/api";

export type ConnectorStatus =
  | "connected"
  | "disconnected"
  | "expired"
  | "unavailable";

export interface Connector {
  id: string;
  name: string;
  description: string;
  category: string;
  provider: string;
  available: boolean;
  status: ConnectorStatus;
  account: string | null;
  connected_at: string | null;
}

/** The OAuth popup posts back from the API's origin, not the app's. */
export const API_ORIGIN = new URL(API_URL).origin;

export interface OAuthMessage {
  source: "jarvis-oauth";
  connectorId: string;
  ok: boolean;
  error: string | null;
}

export function isOAuthMessage(data: unknown): data is OAuthMessage {
  return (
    typeof data === "object" &&
    data !== null &&
    (data as { source?: unknown }).source === "jarvis-oauth"
  );
}

async function failure(res: Response, fallback: string): Promise<string> {
  try {
    const body: unknown = await res.json();
    const detail = (body as { detail?: unknown })?.detail;
    if (typeof detail === "string") return detail;
  } catch {
    // Non-JSON error body; fall through.
  }
  return `${fallback} (${res.status})`;
}

export async function fetchConnectors(): Promise<Connector[]> {
  const res = await fetch(`${API_URL}/api/connectors`);
  if (!res.ok) {
    throw new Error(
      `Could not load connectors. Is the Jarvis API running on ${API_URL}?`,
    );
  }
  return res.json();
}

/** Returns the Google consent URL for the caller to open in a popup. */
export async function startConnect(connectorId: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/connectors/${connectorId}/connect`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await failure(res, "Could not start authorization"));
  const body: { authorization_url: string } = await res.json();
  return body.authorization_url;
}

export async function disconnectConnector(
  connectorId: string,
): Promise<Connector> {
  const res = await fetch(`${API_URL}/api/connectors/${connectorId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await failure(res, "Could not disconnect"));
  return res.json();
}
