"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Room, RoomEvent } from "livekit-client";
import { fetchJarvisToken } from "@/lib/api";

export type ConnectionState = "idle" | "connecting" | "connected" | "error";

/**
 * Owns the LiveKit Room lifecycle.
 *
 * Connection is deliberately user-triggered rather than automatic: browsers
 * require a gesture before granting microphone access or unmuting playback, so
 * auto-connecting on mount produces a silent room with a blocked mic.
 */
export function useJarvisRoom(identity = "kenny") {
  const [room, setRoom] = useState<Room | null>(null);
  const [state, setState] = useState<ConnectionState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [micEnabled, setMicEnabled] = useState(false);

  // Guards against a second connect from a Strict Mode double-invoke or an
  // impatient double-click.
  const connectingRef = useRef(false);
  const roomRef = useRef<Room | null>(null);

  const connect = useCallback(async () => {
    if (connectingRef.current || roomRef.current) return;
    connectingRef.current = true;
    setState("connecting");
    setError(null);

    try {
      const { server_url, token } = await fetchJarvisToken(identity);

      const next = new Room({
        adaptiveStream: true,
        audioCaptureDefaults: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      next.on(RoomEvent.Disconnected, () => {
        roomRef.current = null;
        setRoom(null);
        setState("idle");
        setMicEnabled(false);
      });

      await next.connect(server_url, token);

      // A blocked or missing mic must not fail the connection: the room is
      // usable text-only, and the agent still speaks.
      try {
        await next.localParticipant.setMicrophoneEnabled(true);
        setMicEnabled(true);
      } catch {
        setMicEnabled(false);
        setError("Microphone unavailable — text chat only.");
      }

      roomRef.current = next;
      setRoom(next);
      setState("connected");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setState("error");
    } finally {
      connectingRef.current = false;
    }
  }, [identity]);

  const disconnect = useCallback(async () => {
    await roomRef.current?.disconnect();
    roomRef.current = null;
    setRoom(null);
    setState("idle");
  }, []);

  const toggleMic = useCallback(async () => {
    const current = roomRef.current;
    if (!current) return;
    const next = !current.localParticipant.isMicrophoneEnabled;
    await current.localParticipant.setMicrophoneEnabled(next);
    setMicEnabled(next);
  }, []);

  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
      roomRef.current = null;
    };
  }, []);

  return { room, state, error, micEnabled, connect, disconnect, toggleMic };
}
