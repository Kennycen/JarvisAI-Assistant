"use client";

import type { Connector, ConnectorStatus } from "@/lib/connectors";

const STATUS_LABEL: Record<ConnectorStatus, string> = {
  connected: "Connected",
  disconnected: "Not connected",
  expired: "Re-auth needed",
  unavailable: "Soon",
};

/** Modifiers on the shared .status-dot so connectors read the same as the
 *  connection indicator in the system status panel. */
const STATUS_DOT: Record<ConnectorStatus, string> = {
  connected: "status-dot",
  disconnected: "status-dot is-off",
  expired: "status-dot is-warn",
  unavailable: "status-dot is-off",
};

interface ConnectorRowProps {
  connector: Connector;
  busy: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export default function ConnectorRow({
  connector,
  busy,
  onConnect,
  onDisconnect,
}: ConnectorRowProps) {
  const { status, available } = connector;
  const isLinked = status === "connected" || status === "expired";

  return (
    <div className={`connector-row ${available ? "" : "is-muted"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className={STATUS_DOT[status]} />
            <span className="truncate text-[10px] text-text-primary">
              {connector.name}
            </span>
          </div>
          <p className="mt-1 text-[9px] leading-relaxed text-text-dim normal-case">
            {connector.description}
          </p>
        </div>

        {available ? (
          <button
            onClick={isLinked ? onDisconnect : onConnect}
            disabled={busy}
            className="hud-btn shrink-0"
          >
            {busy ? "…" : isLinked ? "Unlink" : "Connect"}
          </button>
        ) : (
          <span className="shrink-0 text-[8px] tracking-[0.15em] text-text-dim">
            SOON
          </span>
        )}
      </div>

      <div className="mt-1.5 flex items-center justify-between gap-2 text-[8px] tracking-[0.12em]">
        <span className={status === "connected" ? "text-accent" : "text-text-dim"}>
          {STATUS_LABEL[status]}
        </span>
        {connector.account ? (
          <span className="truncate text-text-secondary normal-case">
            {connector.account}
          </span>
        ) : null}
      </div>
    </div>
  );
}
