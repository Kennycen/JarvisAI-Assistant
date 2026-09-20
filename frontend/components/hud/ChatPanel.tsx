"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useChat, useRoomContext, useTranscriptions } from "@livekit/components-react";
import Markdown from "./Markdown";
import Panel from "./Panel";

type Role = "user" | "agent";

interface TimelineEntry {
  id: string;
  role: Role;
  text: string;
  timestamp: number;
  /** Voice transcriptions arrive incrementally; typed chat does not. */
  streaming: boolean;
}

export default function ChatPanel({ className = "" }: { className?: string }) {
  const room = useRoomContext();
  const { send, chatMessages, isSending } = useChat();
  const transcriptions = useTranscriptions();

  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const localIdentity = room?.localParticipant?.identity;

  /**
   * Voice turns arrive as transcriptions and typed turns as chat messages, on
   * two separate topics. Merging by timestamp is what makes a spoken question
   * and a typed one land in the same thread.
   */
  const timeline = useMemo<TimelineEntry[]>(() => {
    const entries: TimelineEntry[] = [];

    for (const t of transcriptions) {
      if (!t.text.trim()) continue;
      entries.push({
        id: t.streamInfo.id,
        role: t.participantInfo.identity === localIdentity ? "user" : "agent",
        text: t.text,
        timestamp: t.streamInfo.timestamp,
        streaming: t.streamInfo.attributes?.["lk.transcription_final"] !== "true",
      });
    }

    for (const m of chatMessages) {
      if (!m.message.trim()) continue;
      entries.push({
        id: m.id,
        role: m.from?.identity === localIdentity ? "user" : "agent",
        text: m.message,
        timestamp: m.timestamp,
        streaming: false,
      });
    }

    return entries.sort((a, b) => a.timestamp - b.timestamp);
  }, [transcriptions, chatMessages, localIdentity]);

  // Pin to the bottom as new turns arrive.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [timeline]);

  async function handleSend() {
    const text = draft.trim();
    if (!text || isSending) return;
    setDraft("");
    try {
      await send(text);
    } catch {
      setDraft(text); // Put it back so the user doesn't lose the message.
    }
  }

  return (
    <Panel
      title="Jarvis // Channel"
      meta={`${timeline.length} MSG`}
      panelId="chat"
      className={className}
      bodyClassName="flex flex-col gap-2"
    >
      <div
        ref={scrollRef}
        className="chat-scroll flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1"
      >
        {timeline.length === 0 ? (
          <p className="text-[10px] leading-relaxed text-text-dim">
            Channel open. Speak, or type below.
          </p>
        ) : (
          timeline.map((entry) => (
            <div
              key={entry.id}
              className={`animate-fade-in-up flex flex-col gap-0.5 ${
                entry.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <span className="text-[8px] tracking-[0.18em] text-text-dim">
                {entry.role === "user" ? "You" : "Jarvis"}
              </span>
              <div
                className={`max-w-[85%] px-2.5 py-1.5 text-[11px] leading-snug normal-case ${
                  entry.role === "user" ? "bubble-user" : "bubble-agent"
                } ${entry.streaming ? "opacity-70" : ""}`}
              >
                {/* Only agent output is markdown; the user's own text renders
                    verbatim so typed asterisks stay asterisks. */}
                {entry.role === "agent" ? (
                  <Markdown text={entry.text} />
                ) : (
                  entry.text
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="flex shrink-0 gap-1.5">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void handleSend();
            }
          }}
          placeholder="Message Jarvis"
          className="chat-input min-w-0 flex-1 rounded px-2 py-1.5 text-[11px]"
        />
        <button
          onClick={() => void handleSend()}
          disabled={isSending || !draft.trim()}
          className="hud-btn shrink-0"
        >
          Send
        </button>
      </div>
    </Panel>
  );
}
