"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  LAYOUT_RESET_EVENT,
  loadPanelOffset,
  savePanelOffset,
  type PanelOffset,
} from "@/lib/layout";

/** How much of a panel must stay on screen. */
const EDGE_MARGIN = 8;

/** Tailwind's `xl`. Below it the HUD collapses panels behind rail toggles and
 *  positions them itself, so a user-set offset would fight the layout. */
const DRAG_BREAKPOINT = "(min-width: 1280px)";

/** Module-level so a freshly grabbed panel always lands above its neighbours. */
let topZ = 20;

const ORIGIN: PanelOffset = { x: 0, y: 0 };

/**
 * Handle-based panel dragging, modelled on openclaw's GSAP Draggable setup but
 * without the dependency.
 *
 * The offset is applied as a transform straight to the DOM rather than held in
 * React state: dragging would otherwise re-render the panel on every pointer
 * move. Same reasoning as useAgentAudioLevel's refs.
 */
export function useDraggablePanel(panelId?: string) {
  const elementRef = useRef<HTMLElement | null>(null);
  const offsetRef = useRef<PanelOffset>(ORIGIN);
  const [enabled, setEnabled] = useState(false);

  const apply = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;
    const { x, y } = offsetRef.current;
    element.style.transform = x || y ? `translate3d(${x}px, ${y}px, 0)` : "";
  }, []);

  /** Keeps a panel reachable no matter how the window changed since the drag. */
  const clamp = useCallback((next: PanelOffset): PanelOffset => {
    const element = elementRef.current;
    if (!element) return next;

    const rect = element.getBoundingClientRect();
    // Where the panel would sit with no offset, i.e. wherever CSS put it.
    const baseLeft = rect.left - offsetRef.current.x;
    const baseTop = rect.top - offsetRef.current.y;

    const minX = EDGE_MARGIN - baseLeft;
    const minY = EDGE_MARGIN - baseTop;
    // A panel taller or wider than the viewport pins to the top-left rather
    // than inverting its bounds.
    const maxX = Math.max(minX, window.innerWidth - EDGE_MARGIN - rect.width - baseLeft);
    const maxY = Math.max(minY, window.innerHeight - EDGE_MARGIN - rect.height - baseTop);

    return {
      x: Math.min(Math.max(next.x, minX), maxX),
      y: Math.min(Math.max(next.y, minY), maxY),
    };
  }, []);

  useEffect(() => {
    if (!panelId) return;
    const query = window.matchMedia(DRAG_BREAKPOINT);
    const sync = () => setEnabled(query.matches);
    sync();
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, [panelId]);

  // Restore the stored offset, or drop it when dragging turns off.
  useEffect(() => {
    if (!panelId) return;

    if (!enabled) {
      offsetRef.current = ORIGIN;
      apply();
      return;
    }

    offsetRef.current = loadPanelOffset(panelId) ?? ORIGIN;
    apply(); // so the rect clamp() measures reflects the restored offset
    offsetRef.current = clamp(offsetRef.current);
    apply();
  }, [panelId, enabled, apply, clamp]);

  useEffect(() => {
    if (!panelId || !enabled) return;
    const onResize = () => {
      offsetRef.current = clamp(offsetRef.current);
      apply();
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [panelId, enabled, apply, clamp]);

  useEffect(() => {
    if (!panelId) return;
    const onReset = () => {
      offsetRef.current = ORIGIN;
      apply();
    };
    window.addEventListener(LAYOUT_RESET_EVENT, onReset);
    return () => window.removeEventListener(LAYOUT_RESET_EVENT, onReset);
  }, [panelId, apply]);

  const onPointerDown = useCallback(
    (event: React.PointerEvent<HTMLElement>) => {
      if (!panelId || !enabled || event.button !== 0) return;
      if (!elementRef.current) return;

      event.preventDefault(); // suppress text selection while dragging
      topZ += 1;
      // Each HUD panel sits in its own absolutely-positioned wrapper, so a
      // z-index on the panel itself never competes with its neighbours.
      const stacking = elementRef.current.parentElement ?? elementRef.current;
      stacking.style.zIndex = String(topZ);
      elementRef.current.style.zIndex = String(topZ);

      const handle = event.currentTarget;
      const pointerId = event.pointerId;
      const startX = event.clientX;
      const startY = event.clientY;
      const start = offsetRef.current;

      // Capture retargets subsequent moves to the handle, so the drag survives
      // the cursor outrunning the panel.
      handle.setPointerCapture(pointerId);

      const onMove = (moveEvent: PointerEvent) => {
        offsetRef.current = clamp({
          x: start.x + (moveEvent.clientX - startX),
          y: start.y + (moveEvent.clientY - startY),
        });
        apply();
      };

      const onUp = () => {
        handle.releasePointerCapture(pointerId);
        handle.removeEventListener("pointermove", onMove);
        handle.removeEventListener("pointerup", onUp);
        handle.removeEventListener("pointercancel", onUp);
        savePanelOffset(panelId, offsetRef.current);
      };

      handle.addEventListener("pointermove", onMove);
      handle.addEventListener("pointerup", onUp);
      handle.addEventListener("pointercancel", onUp);
    },
    [panelId, enabled, apply, clamp],
  );

  return {
    elementRef,
    draggable: Boolean(panelId) && enabled,
    handleProps: { onPointerDown },
  };
}
