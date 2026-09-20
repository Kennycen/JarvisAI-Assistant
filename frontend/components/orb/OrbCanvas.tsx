"use client";

import { useEffect, useRef } from "react";
import { createOrbScene, type OrbAgentState, type OrbScene } from "./scene";

export interface OrbCanvasProps {
  /**
   * Live audio amplitude, read once per frame. This is a ref and not a prop
   * value on purpose: it changes 60x/second and routing it through state would
   * re-render the entire HUD every frame.
   */
  levelRef: React.RefObject<number>;
  agentState: OrbAgentState;
  /** 0..1 text streaming speed; drives the orb while it types. */
  streamIntensity?: number;
  rotationSpeed?: number;
  audioReactivity?: number;
  distortion?: number;
  resolution?: number;
  zoomed?: boolean;
}

export default function OrbCanvas({
  levelRef,
  agentState,
  streamIntensity = 0,
  rotationSpeed = 1,
  audioReactivity = 1.5,
  distortion = 1,
  resolution = 32,
  zoomed = false,
}: OrbCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<OrbScene | null>(null);

  // Mirrored into refs so changing them doesn't tear down the render loop.
  const rotationRef = useRef(rotationSpeed);
  const reactivityRef = useRef(audioReactivity);

  useEffect(() => {
    rotationRef.current = rotationSpeed;
    reactivityRef.current = audioReactivity;
  }, [rotationSpeed, audioReactivity]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = createOrbScene(container);
    sceneRef.current = scene;

    let raf = 0;
    const loop = () => {
      scene.animate(levelRef.current ?? 0, rotationRef.current, reactivityRef.current);
      raf = requestAnimationFrame(loop);
    };
    loop();

    const observer = new ResizeObserver(() => scene.resize());
    observer.observe(container);

    const onThemeChange = () => scene.refreshTheme();
    window.addEventListener("jarvis-theme-change", onThemeChange);

    // Pausing on a hidden tab keeps a background tab off the GPU.
    const onVisibility = () => {
      if (document.hidden) {
        cancelAnimationFrame(raf);
      } else {
        cancelAnimationFrame(raf);
        loop();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      window.removeEventListener("jarvis-theme-change", onThemeChange);
      document.removeEventListener("visibilitychange", onVisibility);
      scene.dispose();
      sceneRef.current = null;
    };
    // levelRef is a stable ref object; the loop must not restart on prop churn.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    sceneRef.current?.setAgentState(agentState);
  }, [agentState]);

  useEffect(() => {
    sceneRef.current?.setStreamIntensity(streamIntensity);
  }, [streamIntensity]);

  useEffect(() => {
    sceneRef.current?.setDistortion(distortion);
  }, [distortion]);

  useEffect(() => {
    sceneRef.current?.setResolution(resolution);
  }, [resolution]);

  useEffect(() => {
    sceneRef.current?.setZoomed(zoomed);
  }, [zoomed]);

  return <div ref={containerRef} className="absolute inset-0 z-[1]" />;
}
