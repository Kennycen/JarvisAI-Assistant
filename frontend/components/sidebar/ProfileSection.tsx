"use client";

import { useProfile } from "@/hooks/useProfile";
import type { Profile } from "@/lib/profile";

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[9px] tracking-[0.12em] text-text-dim">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="hud-input"
      />
    </label>
  );
}

function Area({
  label,
  value,
  onChange,
  placeholder,
  rows,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  rows: number;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[9px] tracking-[0.12em] text-text-dim">{label}</span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="hud-input hud-textarea"
      />
    </label>
  );
}

export default function ProfileSection() {
  const { profile, setField, save, loading, saving, saved, dirty, error } =
    useProfile();

  if (loading) {
    return <p className="text-[9px] text-text-dim">Loading profile…</p>;
  }

  const field =
    <K extends keyof Profile>(key: K) =>
    (value: string) =>
      setField(key, value as Profile[K]);

  return (
    <div className="flex flex-col gap-3">
      <p className="text-[9px] leading-relaxed text-text-dim normal-case">
        Anything here is added to Jarvis&rsquo;s instructions, so he can be
        specific instead of generic.
      </p>

      <Field
        label="Preferred name"
        value={profile.preferred_name}
        onChange={field("preferred_name")}
        placeholder="Kenny"
      />
      <Field
        label="Occupation"
        value={profile.occupation}
        onChange={field("occupation")}
        placeholder="Software engineer"
      />
      <Field
        label="Location"
        value={profile.location}
        onChange={field("location")}
        placeholder="New York"
      />
      <Area
        label="About you"
        value={profile.about}
        onChange={field("about")}
        placeholder="Projects you're working on, people he should recognise, context worth remembering."
        rows={6}
      />
      <Area
        label="How he should help"
        value={profile.preferences}
        onChange={field("preferences")}
        placeholder="Be terse. Always confirm before sending email. Default meetings to 30 minutes."
        rows={4}
      />

      {error ? (
        <p className="text-[9px] leading-relaxed text-red-400 normal-case">
          {error}
        </p>
      ) : null}

      <div className="flex items-center gap-2">
        <button
          onClick={() => void save()}
          disabled={saving || !dirty}
          className="hud-btn"
        >
          {saving ? "Saving…" : "Save"}
        </button>
        {saved ? (
          <span className="text-[9px] text-accent">Saved</span>
        ) : null}
      </div>

      <p className="text-[8px] leading-relaxed text-text-dim normal-case">
        Jarvis reads this when a session starts, so changes apply the next time
        you initialize.
      </p>
    </div>
  );
}
