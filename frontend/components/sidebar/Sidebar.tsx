"use client";

import { useState } from "react";
import AppearanceSection from "./AppearanceSection";
import ConnectorsSection from "./ConnectorsSection";
import PlaceholderSection from "./PlaceholderSection";
import ProfileSection from "./ProfileSection";
import {
  ActivityIcon,
  ClockIcon,
  CloseIcon,
  MemoryIcon,
  PaletteIcon,
  PlugIcon,
  UserIcon,
} from "./icons";

const SECTIONS = [
  { id: "connectors", label: "Connectors", Icon: PlugIcon },
  { id: "profile", label: "Profile", Icon: UserIcon },
  { id: "appearance", label: "Appearance", Icon: PaletteIcon },
  { id: "memory", label: "Memory", Icon: MemoryIcon },
  { id: "automations", label: "Automations", Icon: ClockIcon },
  { id: "activity", label: "Activity", Icon: ActivityIcon },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];

const STORAGE_KEY = "jarvis-sidebar-section";

function isSectionId(value: string | null): value is SectionId {
  return SECTIONS.some((section) => section.id === value);
}

/** Lazy state seed. Safe on first render because the HUD never renders on the
 *  server, so there is no hydration pass to disagree with. */
function storedSection(): SectionId | null {
  if (typeof localStorage === "undefined") return null;
  const stored = localStorage.getItem(STORAGE_KEY);
  return isSectionId(stored) ? stored : null;
}

function content(id: SectionId) {
  switch (id) {
    case "connectors":
      return <ConnectorsSection />;
    case "profile":
      return <ProfileSection />;
    case "appearance":
      return <AppearanceSection />;
    case "memory":
      return (
        <PlaceholderSection
          blurb="Long-term recall: what Jarvis has learned across sessions, and the ability to correct or forget it."
          endpoint="GET /api/memory"
        />
      );
    case "automations":
      return (
        <PlaceholderSection
          blurb="Scheduled and triggered routines - a morning briefing, a nightly inbox sweep, a reminder when a calendar gap closes."
          endpoint="GET /api/automations"
        />
      );
    case "activity":
      return (
        <PlaceholderSection
          blurb="A running log of the tool calls Jarvis makes, so you can see what he actually did rather than what he said he did."
          endpoint="GET /api/activity"
        />
      );
  }
}

export default function Sidebar() {
  const [open, setOpen] = useState<SectionId | null>(storedSection);

  const toggle = (id: SectionId) => {
    const next = open === id ? null : id;
    setOpen(next);
    try {
      if (next) localStorage.setItem(STORAGE_KEY, next);
      else localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Private browsing; the drawer just won't reopen on reload.
    }
  };

  const active = SECTIONS.find((section) => section.id === open);

  return (
    <aside className="pointer-events-auto absolute inset-y-0 left-0 z-30 flex">
      <nav className="sidebar-rail">
        {SECTIONS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => toggle(id)}
            title={label}
            aria-label={label}
            aria-pressed={open === id}
            className={`sidebar-rail-btn ${open === id ? "active" : ""}`}
          >
            <Icon />
          </button>
        ))}
      </nav>

      {active ? (
        <div className="sidebar-drawer">
          <header className="flex shrink-0 items-center justify-between px-3 pt-3 pb-2">
            <span className="panel-title">{active.label}</span>
            <button
              onClick={() => toggle(active.id)}
              aria-label="Close"
              className="text-text-dim transition-colors hover:text-accent"
            >
              <CloseIcon className="h-3.5 w-3.5" />
            </button>
          </header>
          <div className="panel-divider mx-3" />
          <div className="chat-scroll min-h-0 flex-1 overflow-y-auto px-3 py-3">
            {content(active.id)}
          </div>
        </div>
      ) : null}
    </aside>
  );
}
