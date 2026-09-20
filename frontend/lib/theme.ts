/**
 * The entire HUD palette derives from one hue. Three.js reads the resulting CSS
 * custom properties back out via getComputedStyle, so changing the hue here
 * recolours the DOM and the WebGL shaders together.
 */

export const DEFAULT_HUE = 220; // blue

export type ThemePreset = { name: string; hue: number };

export const THEME_PRESETS: ThemePreset[] = [
  { name: "Blue", hue: 220 },
  { name: "Cyan", hue: 190 },
  { name: "Violet", hue: 265 },
  { name: "Green", hue: 150 },
  { name: "Amber", hue: 35 },
  { name: "Red", hue: 5 },
];

const STORAGE_KEY = "jarvis-theme-hue";

function hslToRgb(h: number, s: number, l: number) {
  const sn = s / 100;
  const ln = l / 100;
  const k = (n: number) => (n + h / 30) % 12;
  const a = sn * Math.min(ln, 1 - ln);
  const f = (n: number) =>
    ln - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return {
    r: Math.round(255 * f(0)),
    g: Math.round(255 * f(8)),
    b: Math.round(255 * f(4)),
  };
}

export function setThemeHue(hue: number) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;

  root.style.setProperty("--hue", String(hue));

  // The channels are needed separately because rgba() can't take an hsl().
  const primary = hslToRgb(hue, 100, 63);
  root.style.setProperty("--accent-r", String(primary.r));
  root.style.setProperty("--accent-g", String(primary.g));
  root.style.setProperty("--accent-b", String(primary.b));
  root.style.setProperty(
    "--accent-rgb",
    `${primary.r}, ${primary.g}, ${primary.b}`,
  );

  try {
    localStorage.setItem(STORAGE_KEY, String(hue));
  } catch {
    // Private browsing; the hue just won't persist.
  }

  window.dispatchEvent(new CustomEvent("jarvis-theme-change", { detail: hue }));
}

export function getStoredHue(): number {
  if (typeof localStorage === "undefined") return DEFAULT_HUE;
  const raw = localStorage.getItem(STORAGE_KEY);
  const parsed = raw ? Number.parseInt(raw, 10) : NaN;
  return Number.isFinite(parsed) ? parsed : DEFAULT_HUE;
}

export function initTheme() {
  setThemeHue(getStoredHue());
}
