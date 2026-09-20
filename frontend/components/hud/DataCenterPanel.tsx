"use client";

import { useState } from "react";
import Panel from "./Panel";

export interface OrbControls {
  rotationSpeed: number;
  audioReactivity: number;
  distortion: number;
  resolution: number;
  sensitivity: number;
}

interface DataCenterPanelProps {
  controls: OrbControls;
  onControlsChange: (next: OrbControls) => void;
}

const TABS = ["tools", "controls", "tasks", "memory"] as const;
type Tab = (typeof TABS)[number];

/** Mirrors backend ALL_TOOLS in jarvis/agent/tools/__init__.py. */
const TOOL_GROUPS: { group: string; tools: string[] }[] = [
  {
    group: "Gmail",
    tools: [
      "search_email",
      "read_email",
      "draft_email",
      "send_email",
      "archive_email",
      "trash_email",
    ],
  },
  { group: "Calendar", tools: ["list_events", "create_event", "delete_event"] },
  {
    group: "Browser",
    tools: [
      "open_url",
      "search_the_web",
      "read_page",
      "inspect_page",
      "go_back",
      "take_screenshot",
      "click",
      "confirm_browser_action",
      "type_text",
      "scroll",
      "press_key",
    ],
  },
];

function Slider({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-[9px]">
        <span className="text-text-dim">{label}</span>
        <span className="text-text-secondary">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="hud-slider"
      />
    </div>
  );
}

function AwaitingBackend({ what, endpoint }: { what: string; endpoint: string }) {
  return (
    <div className="flex h-full flex-col justify-center gap-1 text-center">
      <p className="text-[10px] text-text-secondary">No {what} source</p>
      <p className="text-[9px] leading-relaxed text-text-dim normal-case">
        Add <code>{endpoint}</code> to the API to populate this panel.
      </p>
    </div>
  );
}

export default function DataCenterPanel({
  controls,
  onControlsChange,
}: DataCenterPanelProps) {
  const [tab, setTab] = useState<Tab>("tools");

  const set = <K extends keyof OrbControls>(key: K, value: OrbControls[K]) =>
    onControlsChange({ ...controls, [key]: value });

  const toolCount = TOOL_GROUPS.reduce((n, g) => n + g.tools.length, 0);

  return (
    <Panel
      title="Data Center"
      meta={tab === "tools" ? `${toolCount} TOOLS` : undefined}
      panelId="data"
      className="h-[340px] w-[300px]"
      bodyClassName="flex flex-col gap-2 pt-0"
    >
      <nav className="flex shrink-0 border-b border-[rgba(var(--accent-rgb),0.15)]">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`tab-btn flex-1 ${tab === t ? "active" : ""}`}
          >
            {t}
          </button>
        ))}
      </nav>

      <div className="chat-scroll min-h-0 flex-1 overflow-y-auto pr-1">
        {tab === "tools" && (
          <div className="flex flex-col gap-2.5">
            {TOOL_GROUPS.map((g) => (
              <div key={g.group}>
                <div className="mb-1 text-[9px] tracking-[0.15em] text-accent">
                  {g.group}
                </div>
                <div className="flex flex-wrap gap-1">
                  {g.tools.map((t) => (
                    <span
                      key={t}
                      className="rounded border border-[rgba(var(--accent-rgb),0.2)] bg-[rgba(var(--accent-rgb),0.06)] px-1.5 py-0.5 text-[8px] text-text-secondary normal-case"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "controls" && (
          <div className="flex flex-col gap-2.5">
            <Slider
              label="Mic sensitivity"
              value={controls.sensitivity}
              min={1}
              max={20}
              step={0.5}
              onChange={(v) => set("sensitivity", v)}
            />
            <Slider
              label="Rotation"
              value={controls.rotationSpeed}
              min={0}
              max={4}
              step={0.1}
              onChange={(v) => set("rotationSpeed", v)}
            />
            <Slider
              label="Reactivity"
              value={controls.audioReactivity}
              min={0}
              max={5}
              step={0.1}
              onChange={(v) => set("audioReactivity", v)}
            />
            <Slider
              label="Distortion"
              value={controls.distortion}
              min={0}
              max={3}
              step={0.1}
              onChange={(v) => set("distortion", v)}
            />
            <Slider
              label="Resolution"
              value={controls.resolution}
              min={8}
              max={64}
              step={8}
              onChange={(v) => set("resolution", v)}
            />

            <p className="text-[8px] leading-relaxed text-text-dim normal-case">
              Colour lives in the sidebar under Appearance.
            </p>
          </div>
        )}

        {tab === "tasks" && (
          <AwaitingBackend what="task" endpoint="GET /api/tasks" />
        )}
        {tab === "memory" && (
          <AwaitingBackend what="memory" endpoint="GET /api/memory" />
        )}
      </div>
    </Panel>
  );
}
