"use client";

import dynamic from "next/dynamic";

// The orb needs WebGL and the HUD owns a LiveKit Room, so nothing here can run
// on the server. `ssr: false` is only legal inside a Client Component, which is
// why this file carries the directive.
const Hud = dynamic(() => import("@/components/Hud"), {
  ssr: false,
  loading: () => <div className="h-screen w-screen bg-hud-bg" />,
});

export default function Page() {
  return <Hud />;
}
