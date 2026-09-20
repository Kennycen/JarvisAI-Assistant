"use client";

import { useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { RoomContext } from "@livekit/components-react";
import { useJarvisRoom } from "@/hooks/useJarvisRoom";
import JarvisStage from "@/components/JarvisStage";
import Sidebar from "@/components/sidebar/Sidebar";
import { initTheme } from "@/lib/theme";

const OrbCanvas = dynamic(() => import("@/components/orb/OrbCanvas"), {
  ssr: false,
});

export default function Hud() {
  const { room, state, error, micEnabled, connect, disconnect, toggleMic } =
    useJarvisRoom();

  // Idle orb before connecting: no audio source, so the level stays 0 and the
  // orb just breathes.
  const idleLevelRef = useRef(0);

  useEffect(() => {
    initTheme();
  }, []);

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-hud-bg">
      <div className="space-background" />
      <div className="grid-overlay" />
      <div className="vignette" />

      {/* Outside the room branch: connectors and profile are worth reaching
          before a session exists. */}
      <Sidebar />

      {room ? (
        <RoomContext.Provider value={room}>
          <JarvisStage
            connectionState={state}
            micEnabled={micEnabled}
            onToggleMic={() => void toggleMic()}
            onDisconnect={() => void disconnect()}
          />
        </RoomContext.Provider>
      ) : (
        <>
          <OrbCanvas levelRef={idleLevelRef} agentState="idle" />

          <div className="absolute inset-0 z-10 flex items-center justify-center">
            <div className="flex flex-col items-center gap-5 pt-[300px]">
              <h1 className="text-[13px] tracking-[0.45em] text-accent">
                J A R V I S
              </h1>

              <button
                onClick={() => void connect()}
                disabled={state === "connecting"}
                className="hud-btn !px-6 !py-2 !text-[11px]"
              >
                {state === "connecting" ? "Connecting…" : "Initialize"}
              </button>

              {error ? (
                <p className="max-w-sm text-center text-[10px] leading-relaxed text-red-400 normal-case">
                  {error}
                </p>
              ) : (
                <p className="text-[9px] tracking-[0.2em] text-text-dim">
                  Microphone access required
                </p>
              )}
            </div>
          </div>
        </>
      )}
    </main>
  );
}
