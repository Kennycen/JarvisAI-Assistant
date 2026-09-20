# Jarvis Frontend

Next.js 16 + React 19 + Tailwind v4 HUD for the Jarvis voice assistant. The
interface is a port of [openclaw-jarvis-ui](../openclaw-jarvis-ui) recoloured to
blue and rewired from that project's SSE/WebSocket backend onto LiveKit.

## Running

Three processes are needed:

```bash
# 1. API (mints LiveKit tokens)
cd ../backend && uv run uvicorn jarvis.api.main:app --port 8000

# 2. Agent worker (must be running, or you join an empty room)
cd ../backend && uv run python -m jarvis.agent.worker dev

# 3. This app
npm run dev
```

`.env.local` needs only:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## How the orb moves

Two independent signals drive it:

- **Agent state** sets the baseline energy. `useVoiceAssistant()` exposes the
  `lk.agent.state` attribute the agent framework publishes; `listening`,
  `thinking` and `speaking` map onto the orb's idle / thinking / responding
  modes in `components/JarvisStage.tsx`.
- **Audio amplitude** drives per-frame vertex displacement and rotation.
  `hooks/useAgentAudioLevel.ts` taps the agent's audio track with an
  `AnalyserNode` and writes a 0..1 value into a ref, which
  `components/orb/OrbCanvas.tsx` reads once per frame.

Two non-obvious constraints keep this working:

1. **`<RoomAudioRenderer />` must stay mounted.** In Chrome a remote WebRTC track
   feeds silence into Web Audio unless the same track is also attached to a live
   `HTMLAudioElement`. That component provides one, so the analyser depends on it
   even though it looks like it only handles playback.
2. **The level never goes through React state.** It updates ~60x/second; as state
   it would re-render the whole HUD every frame.

Only the first 256 FFT bins (~0-6kHz) are summed. The original averaged all 1024,
which at 48kHz spreads the measurement to 24kHz and dilutes a talking voice by
roughly 6x, leaving the orb nearly still.

## Chat rendering

Agent replies go through `components/hud/Markdown.tsx`, which renders to React
elements rather than an HTML string. That is a security decision, not a style one:
Jarvis has `read_page` and `search_the_web`, so anything it echoes back is
untrusted input. Building nodes means React escapes every text child, making
markup injection structurally impossible, and link hrefs are checked against an
`https?:`/`mailto:` allowlist so `javascript:` and `data:` URLs degrade to plain
text. Do not "simplify" this into `dangerouslySetInnerHTML`.

User messages render verbatim so typed asterisks stay asterisks.

## Theming

Every accent derives from a single `--hue` on `:root`. `lib/theme.ts` sets it and
the matching RGB channels; the Three.js shaders read the resulting CSS custom
properties back out via `getComputedStyle`, so one hue change recolours the DOM
and the WebGL scene together. Blue is 220. Presets and a hue slider live in the
left sidebar under **Appearance**. Drag HUD panels by the grip in the header;
positions persist in `localStorage` on wide screens, and Appearance can reset them.

## Sidebar

The 56px rail on the left expands into a drawer:

- **Connectors** — Gmail and Google Calendar OAuth, plus greyed-out placeholders.
- **Profile** — context Jarvis reads at the start of the next session.
- **Appearance** — hue presets, custom hue, reset panel layout.
- **Memory / Automations / Activity** — named placeholders awaiting backend work.

Connectors talk to `/api/connectors`; the profile form talks to `/api/profile`.

## Routes

- `/` — the HUD.

## Known behaviour

The mic stays open for the whole session, and Gemini's server-side turn detection
will transcribe ambient room noise as short spurious user turns (observed: `.`,
`うん。`), which can prompt a confused reply. Use **Mute** between turns, or tune
turn detection in `backend/src/jarvis/agent/worker.py`.

## Panels without a backend

The `tasks` and `memory` tabs in Data Center, and the Memory / Automations /
Activity sidebar sections, are placeholders that name the endpoint that would
populate them. The `tools` tab mirrors `ALL_TOOLS` in
`backend/src/jarvis/agent/tools/__init__.py` and must be updated by hand if that
list changes.
