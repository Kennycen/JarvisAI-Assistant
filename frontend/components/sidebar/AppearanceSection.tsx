"use client";

import { useState } from "react";
import { clearLayout } from "@/lib/layout";
import { getStoredHue, setThemeHue, THEME_PRESETS } from "@/lib/theme";

export default function AppearanceSection() {
  // Lazy rather than an effect: the HUD is a client-only tree, so localStorage
  // is available on first render and there is no server pass to mismatch.
  const [hue, setHue] = useState(getStoredHue);

  const apply = (next: number) => {
    setThemeHue(next);
    setHue(next);
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-1.5 text-[9px] tracking-[0.15em] text-accent">
          Colour theme
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          {THEME_PRESETS.map((preset) => (
            <button
              key={preset.hue}
              onClick={() => apply(preset.hue)}
              className="theme-swatch"
              style={{
                // Independent of --hue so every swatch shows its own colour.
                borderColor:
                  hue === preset.hue
                    ? `hsl(${preset.hue}, 100%, 63%)`
                    : "rgba(255,255,255,0.12)",
              }}
            >
              <span
                className="theme-swatch-dot"
                style={{ background: `hsl(${preset.hue}, 100%, 63%)` }}
              />
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-1 flex justify-between text-[9px]">
          <span className="text-text-dim">Custom hue</span>
          <span className="text-text-secondary">{hue}</span>
        </div>
        <input
          type="range"
          min={0}
          max={360}
          step={1}
          value={hue}
          onChange={(e) => apply(Number(e.target.value))}
          className="hud-slider"
        />
        <p className="mt-1.5 text-[8px] leading-relaxed text-text-dim normal-case">
          The orb, the background and every panel derive from this one hue.
        </p>
      </div>

      <div>
        <div className="mb-1.5 text-[9px] tracking-[0.15em] text-accent">
          Layout
        </div>
        <button onClick={clearLayout} className="hud-btn">
          Reset panel positions
        </button>
        <p className="mt-1.5 text-[8px] leading-relaxed text-text-dim normal-case">
          Drag a panel by the grip in its header. Positions are remembered per
          browser, on wide screens only.
        </p>
      </div>
    </div>
  );
}
