"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import {
  RoomAudioRenderer,
  StartAudio,
  useRoomContext,
  useVoiceAssistant,
} from "@livekit/components-react";
import type { OrbAgentState } from "@/components/orb/scene";
import { useAgentAudioLevel } from "@/hooks/useAgentAudioLevel";
import type { ConnectionState } from "@/hooks/useJarvisRoom";
import ChatPanel from "@/components/hud/ChatPanel";
import DataCenterPanel, { type OrbControls } from "@/components/hud/DataCenterPanel";
import SpectrumPanel from "@/components/hud/SpectrumPanel";
import SystemStatusPanel from "@/components/hud/SystemStatusPanel";

const OrbCanvas = dynamic(() => import("@/components/orb/OrbCanvas"), {
  ssr: false,
});

interface JarvisStageProps {
  connectionState: ConnectionState;
  micEnabled: boolean;
  onToggleMic: () => void;
  onDisconnect: () => void;
}

/** The orb only distinguishes three levels of engagement. */
function toOrbState(state: string): OrbAgentState {
  if (state === "thinking") return "thinking";
  if (state === "speaking") return "responding";
  return "idle";
}

type PanelId = "status" | "data" | "audio";

const PANEL_TOGGLES: { id: PanelId; label: string }[] = [
  { id: "status", label: "Sys" },
  { id: "data", label: "Data" },
  { id: "audio", label: "♪" },
];

export default function JarvisStage({
  connectionState,
  micEnabled,
  onToggleMic,
  onDisconnect,
}: JarvisStageProps) {
  const room = useRoomContext();
  const { state: agentState, audioTrack, agent } = useVoiceAssistant();

  const [controls, setControls] = useState<OrbControls>({
    rotationSpeed: 1,
    audioReactivity: 1.5,
    distortion: 1,
    resolution: 32,
    sensitivity: 5,
  });
  // Which side panel is revealed on narrow viewports; ignored at xl and up.
  const [openPanel, setOpenPanel] = useState<PanelId | null>(null);

  // The raw MediaStreamTrack is what Web Audio needs; the TrackReference wraps
  // a publication that may not have resolved a track yet.
  const mediaStreamTrack = audioTrack?.publication?.track?.mediaStreamTrack;

  const { levelRef, binsRef } = useAgentAudioLevel(mediaStreamTrack, {
    sensitivity: controls.sensitivity,
  });

  const orbState = toOrbState(agentState);

  return (
    <>
      {/* Must stay mounted: it owns playback, and in Chrome a remote track
          feeds silence into Web Audio unless it's also attached to an audio
          element -- so the orb depends on this too. */}
      <RoomAudioRenderer />

      <OrbCanvas
        levelRef={levelRef}
        agentState={orbState}
        rotationSpeed={controls.rotationSpeed}
        audioReactivity={controls.audioReactivity}
        distortion={controls.distortion}
        resolution={controls.resolution}
        zoomed={orbState === "responding"}
      />

      {/*
        Below `xl` there isn't room for four fixed panels without overlap, so the
        side panels collapse behind the rail toggles and chat goes full width.
      */}
      <div className="pointer-events-none absolute inset-0 z-10">
        {/* Compact status strip, small screens only. Left offsets throughout
            clear the 56px sidebar rail. */}
        <div className="pointer-events-none absolute top-3 left-[68px] flex items-center gap-2 xl:hidden">
          <span
            className="status-dot"
            style={
              connectionState === "connected"
                ? undefined
                : { background: "#6b7480", boxShadow: "none", animation: "none" }
            }
          />
          <span className="text-[9px] tracking-[0.18em] text-text-secondary">
            {agentState.toUpperCase()}
          </span>
        </div>

        <div
          className={`absolute top-5 left-[76px] ${openPanel === "status" ? "" : "hidden"} xl:block`}
        >
          <SystemStatusPanel
            connectionState={connectionState}
            agentStateLabel={agentState.toUpperCase()}
            roomName={room?.name}
            agentIdentity={agent?.identity}
          />
        </div>

        <div
          className={`absolute top-5 right-5 ${openPanel === "data" ? "" : "hidden"} xl:block`}
        >
          <DataCenterPanel controls={controls} onControlsChange={setControls} />
        </div>

        {/* Full width below xl, fixed width above. */}
        <div className="absolute right-3 bottom-3 left-[68px] xl:right-auto xl:bottom-5 xl:left-[76px]">
          <ChatPanel className="h-[220px] w-full sm:h-[260px] xl:h-[320px] xl:w-[460px]" />
        </div>

        <div
          className={`absolute right-5 bottom-[248px] ${
            openPanel === "audio" ? "" : "hidden"
          } xl:bottom-[60px] xl:block`}
        >
          <SpectrumPanel binsRef={binsRef} levelRef={levelRef} />
        </div>

        {/* Right-hand rail: panel toggles below xl, session controls always. */}
        <div className="pointer-events-auto absolute top-1/2 right-3 flex -translate-y-1/2 flex-col gap-1.5 xl:top-auto xl:bottom-5 xl:translate-y-0 xl:flex-row">
          {PANEL_TOGGLES.map((p) => (
            <button
              key={p.id}
              onClick={() => setOpenPanel(openPanel === p.id ? null : p.id)}
              className="hud-btn xl:hidden"
              style={
                openPanel === p.id
                  ? { background: "rgba(var(--accent-rgb),0.3)" }
                  : undefined
              }
            >
              {p.label}
            </button>
          ))}
          <button onClick={onToggleMic} className="hud-btn">
            {micEnabled ? "Mute" : "Unmute"}
          </button>
          <button onClick={onDisconnect} className="hud-btn">
            End
          </button>
        </div>
      </div>

      {/* Only renders when the browser blocks autoplay. */}
      <div className="absolute top-5 left-1/2 z-50 -translate-x-1/2">
        <StartAudio label="Click to enable audio" className="hud-btn" />
      </div>
    </>
  );
}
