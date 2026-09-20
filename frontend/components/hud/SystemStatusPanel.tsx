"use client";

import { useEffect, useState } from "react";
import type { ConnectionState } from "@/hooks/useJarvisRoom";
import Panel from "./Panel";

interface SystemStatusPanelProps {
  connectionState: ConnectionState;
  agentStateLabel: string;
  roomName?: string;
  agentIdentity?: string;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-[9px] text-text-dim">{label}</span>
      <span className="truncate text-[10px] text-text-secondary">{value}</span>
    </div>
  );
}

export default function SystemStatusPanel({
  connectionState,
  agentStateLabel,
  roomName,
  agentIdentity,
}: SystemStatusPanelProps) {
  const [clock, setClock] = useState("--:--:--");
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const tick = () => {
      setClock(new Date().toLocaleTimeString("en-GB", { hour12: false }));
      setUptime(Math.floor((Date.now() - started) / 1000));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const uptimeLabel = `${String(Math.floor(uptime / 3600)).padStart(2, "0")}:${String(
    Math.floor((uptime % 3600) / 60),
  ).padStart(2, "0")}:${String(uptime % 60).padStart(2, "0")}`;

  return (
    <Panel
      title="System Status"
      meta={clock}
      panelId="status"
      className="w-[280px]"
      bodyClassName="flex flex-col gap-1.5"
    >
      <div className="mb-1 flex items-center gap-2">
        <span
          className="status-dot"
          style={
            connectionState === "connected"
              ? undefined
              : { background: "#6b7480", boxShadow: "none", animation: "none" }
          }
        />
        <span className="text-[10px] tracking-[0.15em] text-text-secondary">
          {connectionState.toUpperCase()}
        </span>
      </div>

      <Row label="AGENT" value={agentStateLabel} />
      <Row label="MODEL" value="gemini-2.5-flash native audio" />
      <Row label="VOICE" value="Charon" />
      <Row label="ROOM" value={roomName ?? "—"} />
      <Row label="WORKER" value={agentIdentity ?? "awaiting dispatch"} />
      <Row label="SESSION" value={uptimeLabel} />
    </Panel>
  );
}
