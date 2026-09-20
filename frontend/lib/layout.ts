/**
 * Where the user dragged each panel, as an offset from its CSS position rather
 * than an absolute coordinate. Storing offsets means the responsive `left-5` /
 * `right-5` rules still decide the starting point at every breakpoint.
 */

const STORAGE_KEY = "jarvis-panel-layout";

/** Fired after the layout is cleared so mounted panels can snap back. */
export const LAYOUT_RESET_EVENT = "jarvis-layout-reset";

export interface PanelOffset {
  x: number;
  y: number;
}

type Layout = Record<string, PanelOffset>;

function isOffset(value: unknown): value is PanelOffset {
  if (typeof value !== "object" || value === null) return false;
  const { x, y } = value as Record<string, unknown>;
  return Number.isFinite(x) && Number.isFinite(y);
}

export function loadLayout(): Layout {
  if (typeof localStorage === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return {};
    return Object.fromEntries(
      Object.entries(parsed as Record<string, unknown>).filter(([, v]) =>
        isOffset(v),
      ),
    ) as Layout;
  } catch {
    return {};
  }
}

export function loadPanelOffset(panelId: string): PanelOffset | null {
  return loadLayout()[panelId] ?? null;
}

export function savePanelOffset(panelId: string, offset: PanelOffset) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...loadLayout(), [panelId]: offset }),
    );
  } catch {
    // Private browsing; the layout just won't survive a reload.
  }
}

export function clearLayout() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear.
  }
  window.dispatchEvent(new CustomEvent(LAYOUT_RESET_EVENT));
}
