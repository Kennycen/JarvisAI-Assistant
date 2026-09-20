"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  API_ORIGIN,
  type Connector,
  disconnectConnector,
  fetchConnectors,
  isOAuthMessage,
  startConnect,
} from "@/lib/connectors";

const POPUP_FEATURES = "width=520,height=680,menubar=no,toolbar=no";

/** Covers the case where the user completes or abandons consent in a way that
 *  never posts back - closing the window, or a browser that blocks opener. */
const POLL_INTERVAL_MS = 1500;

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function useConnectors() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const popupRef = useRef<Window | null>(null);

  const refresh = useCallback(async () => {
    try {
      setConnectors(await fetchConnectors());
      setError(null);
    } catch (err) {
      setError(message(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // Inlined rather than calling refresh(), so the initial load can be abandoned
  // if the drawer closes before it resolves.
  useEffect(() => {
    let cancelled = false;
    fetchConnectors()
      .then((rows) => {
        if (!cancelled) setConnectors(rows);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(message(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // The callback page posts here the moment the token exchange finishes.
  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      // The popup lives on the API's origin, so anything else is not ours.
      if (event.origin !== API_ORIGIN || !isOAuthMessage(event.data)) return;
      if (!event.data.ok && event.data.error) setError(event.data.error);
      setBusyId(null);
      void refresh();
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [refresh]);

  useEffect(() => {
    if (!busyId) return;
    const timer = window.setInterval(() => {
      const popup = popupRef.current;
      if (popup && popup.closed) {
        popupRef.current = null;
        setBusyId(null);
      }
      void refresh();
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [busyId, refresh]);

  const connect = useCallback(async (connectorId: string) => {
    setError(null);
    setBusyId(connectorId);
    try {
      const url = await startConnect(connectorId);
      popupRef.current = window.open(url, "jarvis-oauth", POPUP_FEATURES);
      if (!popupRef.current) {
        setError("Your browser blocked the sign-in window. Allow popups and retry.");
        setBusyId(null);
      }
    } catch (err) {
      setError(message(err));
      setBusyId(null);
    }
  }, []);

  const disconnect = useCallback(
    async (connectorId: string) => {
      setError(null);
      setBusyId(connectorId);
      try {
        await disconnectConnector(connectorId);
        await refresh();
      } catch (err) {
        setError(message(err));
      } finally {
        setBusyId(null);
      }
    },
    [refresh],
  );

  return { connectors, loading, error, busyId, connect, disconnect, refresh };
}
