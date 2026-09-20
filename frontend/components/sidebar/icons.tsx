/** Inline so the HUD keeps its zero-dependency footprint. All stroke-only,
 *  inheriting currentColor so the accent hue drives them. */

import type { ReactNode } from "react";

type IconProps = { className?: string };

function Svg({ children, className }: IconProps & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className ?? "h-[18px] w-[18px]"}
      aria-hidden
    >
      {children}
    </svg>
  );
}

export function PlugIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M9 3v6M15 3v6" />
      <path d="M6 9h12v3a6 6 0 0 1-12 0z" />
      <path d="M12 18v3" />
    </Svg>
  );
}

export function UserIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20a7 7 0 0 1 14 0" />
    </Svg>
  );
}

export function PaletteIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M12 3.5A8.5 8.5 0 1 0 15 19c.8 0 1.5-.7 1.5-1.5 0-.4-.2-.8-.4-1.1-.3-.4-.1-1 .3-1.2A8.5 8.5 0 0 0 12 3.5z" />
      <circle cx="8.2" cy="10" r="1" />
      <circle cx="10.8" cy="7.4" r="1" />
      <circle cx="14.4" cy="8.2" r="1" />
      <circle cx="7.6" cy="13.5" r="1" />
    </Svg>
  );
}

export function MemoryIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <rect x="5" y="5" width="14" height="14" rx="2" />
      <path d="M9 9h6M9 12h6M9 15h3" />
    </Svg>
  );
}

export function ClockIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </Svg>
  );
}

export function ActivityIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M3 12h4l3-7 4 14 3-7h4" />
    </Svg>
  );
}

export function CloseIcon(props: IconProps) {
  return (
    <Svg {...props}>
      <path d="M6 6l12 12M18 6L6 18" />
    </Svg>
  );
}
