"use client";

import { useEffect, useRef } from "react";
import Panel from "./Panel";

interface SpectrumPanelProps {
  /** Shared with the orb's analyser so this doesn't need a second one. */
  binsRef: React.RefObject<Uint8Array>;
  levelRef: React.RefObject<number>;
}

/** Bins beyond this are silent during speech and would just render flat. */
const VISIBLE_BINS = 192;
const BAR_GAP = 1;

export default function SpectrumPanel({ binsRef, levelRef }: SpectrumPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const levelBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let accent = "66, 129, 255";

    const readAccent = () => {
      const v = getComputedStyle(document.documentElement)
        .getPropertyValue("--accent-rgb")
        .trim();
      if (v) accent = v;
    };
    readAccent();
    window.addEventListener("jarvis-theme-change", readAccent);

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio, 2);
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      ctx.clearRect(0, 0, w, h);

      const bins = binsRef.current;
      const barCount = Math.min(VISIBLE_BINS, bins.length);
      const barWidth = Math.max(1, w / barCount - BAR_GAP);

      for (let i = 0; i < barCount; i++) {
        const value = bins[i] / 255;
        const barHeight = Math.max(1, value * h);
        const x = i * (barWidth + BAR_GAP);
        // Brighter toward the top of each bar reads as energy rather than a
        // flat block.
        const alpha = 0.25 + value * 0.75;
        ctx.fillStyle = `rgba(${accent}, ${alpha})`;
        ctx.fillRect(x, h - barHeight, barWidth, barHeight);
      }

      // Baseline so the panel doesn't look broken in silence.
      ctx.fillStyle = `rgba(${accent}, 0.25)`;
      ctx.fillRect(0, h - 1, w, 1);

      if (levelBarRef.current) {
        const pct = Math.min(100, (levelRef.current ?? 0) * 100);
        levelBarRef.current.style.width = `${pct}%`;
      }

      raf = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      window.removeEventListener("jarvis-theme-change", readAccent);
    };
  }, [binsRef, levelRef]);

  return (
    <Panel title="♪ Audio" meta="AGENT OUT" panelId="spectrum" className="w-[360px]">
      <canvas ref={canvasRef} className="block h-[70px] w-full" />
      <div className="mt-2 flex items-center gap-2">
        <span className="text-[8px] tracking-[0.15em] text-text-dim">LVL</span>
        <div className="data-bar flex-1">
          <div ref={levelBarRef} className="data-bar-fill" style={{ width: "0%" }} />
        </div>
      </div>
    </Panel>
  );
}
