// Contrat de POST /api/v1/chat (services/api/app/routers/chat.py).
import { API_URL } from "./capabilities";

export type ChatTurn = { role: "user" | "assistant"; content: string };

export type ChatReply = {
  reply: string;
  provider: string;
  model: string;
  truncated: boolean;
  status: "experimental";
  verified: false;
};

export const MAX_MESSAGES = 20;
export const MAX_CHARS = 4000;

export type ChatErrorCode =
  | "not_configured"
  | "rate_limited"
  | "refused"
  | "unavailable"
  | "provider_error"
  | "invalid"
  | "network";

export class ChatError extends Error {
  constructor(public code: ChatErrorCode) {
    super(code);
  }
}

const KNOWN: ChatErrorCode[] = [
  "not_configured",
  "rate_limited",
  "refused",
  "unavailable",
  "provider_error",
];

export async function sendChat(messages: ChatTurn[]): Promise<ChatReply> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
  } catch {
    throw new ChatError("network");
  }
  if (response.ok) return (await response.json()) as ChatReply;

  const body = (await response.json().catch(() => null)) as {
    detail?: { code?: string };
  } | null;
  const code = body?.detail?.code as ChatErrorCode | undefined;
  throw new ChatError(code && KNOWN.includes(code) ? code : "invalid");
}
