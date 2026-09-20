"use client";

import ConnectorRow from "./ConnectorRow";
import { useConnectors } from "@/hooks/useConnectors";
import type { Connector } from "@/lib/connectors";

function byCategory(connectors: Connector[]): [string, Connector[]][] {
  const groups = new Map<string, Connector[]>();
  for (const connector of connectors) {
    const existing = groups.get(connector.category);
    if (existing) existing.push(connector);
    else groups.set(connector.category, [connector]);
  }
  return [...groups.entries()];
}

export default function ConnectorsSection() {
  const { connectors, loading, error, busyId, connect, disconnect } =
    useConnectors();

  if (loading) {
    return <p className="text-[9px] text-text-dim">Loading connectors…</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {error ? (
        <p className="text-[9px] leading-relaxed text-red-400 normal-case">
          {error}
        </p>
      ) : null}

      {byCategory(connectors).map(([category, rows]) => (
        <div key={category}>
          <div className="mb-1.5 text-[9px] tracking-[0.15em] text-accent">
            {category}
          </div>
          <div className="flex flex-col gap-1.5">
            {rows.map((connector) => (
              <ConnectorRow
                key={connector.id}
                connector={connector}
                busy={busyId === connector.id}
                onConnect={() => void connect(connector.id)}
                onDisconnect={() => void disconnect(connector.id)}
              />
            ))}
          </div>
        </div>
      ))}

      <p className="text-[8px] leading-relaxed text-text-dim normal-case">
        Connecting opens a Google consent window. Each service is authorized
        separately, so unlinking one leaves the other alone.
      </p>
    </div>
  );
}
