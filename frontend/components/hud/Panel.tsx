"use client";

import type { ReactNode, RefObject } from "react";
import { useDraggablePanel } from "@/hooks/useDraggablePanel";

interface PanelProps {
  title: string;
  /** Rendered at the right of the title row. */
  meta?: ReactNode;
  /** Set to make the panel draggable by its header grip and remember where it
   *  was left. Omit for panels that should stay put. */
  panelId?: string;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export default function Panel({
  title,
  meta,
  panelId,
  className = "",
  bodyClassName = "",
  children,
}: PanelProps) {
  const { elementRef, draggable, handleProps } = useDraggablePanel(panelId);

  return (
    <section
      ref={elementRef as RefObject<HTMLElement | null>}
      className={`data-panel corner-brackets relative flex flex-col ${className}`}
    >
      <header className="flex items-center justify-between px-3 pt-2.5 pb-2">
        <span className="panel-title">{title}</span>
        <span className="flex items-center gap-2">
          {meta ? <span className="text-[9px] text-text-dim">{meta}</span> : null}
          {draggable ? (
            <span
              {...handleProps}
              className="drag-grip"
              title="Drag to move"
              aria-hidden
            >
              ⣿
            </span>
          ) : null}
        </span>
      </header>
      <div className="panel-divider mx-3" />
      <div className={`min-h-0 flex-1 px-3 py-2.5 ${bodyClassName}`}>
        {children}
      </div>
    </section>
  );
}
