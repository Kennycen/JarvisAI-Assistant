"use client";

/** Shared by the sidebar sections that have no backend yet, so the gap is
 *  visible and named rather than silently missing. Mirrors the AwaitingBackend
 *  treatment inside the data centre panel. */
export default function PlaceholderSection({
  blurb,
  endpoint,
}: {
  blurb: string;
  endpoint: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-[9px] leading-relaxed text-text-secondary normal-case">
        {blurb}
      </p>
      <p className="text-[8px] leading-relaxed text-text-dim normal-case">
        Not wired up yet. Add <code>{endpoint}</code> to the API to bring this
        section to life.
      </p>
    </div>
  );
}
