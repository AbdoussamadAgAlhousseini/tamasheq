// Contrat de POST /api/v1/chat (services/api/app/routers/chat.py).
import { postJson } from "./api";

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

export function sendChat(messages: ChatTurn[]): Promise<ChatReply> {
  return postJson<ChatReply>("/api/v1/chat", { messages });
}
