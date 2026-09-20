export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface TokenResponse {
  server_url: string;
  room: string;
  token: string;
}

/**
 * The token carries a RoomConfiguration that dispatches the Jarvis worker, so
 * minting a token is also what summons the agent into the room. Connecting with
 * a token from anywhere else gets you an empty room.
 */
export async function fetchJarvisToken(
  identity = "kenny",
  room?: string,
): Promise<TokenResponse> {
  const res = await fetch(`${API_URL}/api/livekit/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identity, room: room ?? null }),
  });

  if (!res.ok) {
    throw new Error(
      `Token request failed (${res.status}). Is the Jarvis API running on ${API_URL}?`,
    );
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}
