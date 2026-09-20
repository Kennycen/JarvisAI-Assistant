"use client";

import { useCallback, useEffect, useState } from "react";
import {
  EMPTY_PROFILE,
  fetchProfile,
  type Profile,
  saveProfile,
} from "@/lib/profile";

/** How long the "saved" confirmation stays up. */
const CONFIRM_MS = 2500;

export function useProfile() {
  const [profile, setProfile] = useState<Profile>(EMPTY_PROFILE);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchProfile()
      .then((loaded) => {
        if (!cancelled) setProfile(loaded);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!saved) return;
    const timer = window.setTimeout(() => setSaved(false), CONFIRM_MS);
    return () => window.clearTimeout(timer);
  }, [saved]);

  const setField = useCallback(<K extends keyof Profile>(key: K, value: Profile[K]) => {
    setProfile((current) => ({ ...current, [key]: value }));
    setDirty(true);
    setSaved(false);
  }, []);

  const save = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      setProfile(await saveProfile(profile));
      setDirty(false);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }, [profile]);

  return { profile, setField, save, loading, saving, saved, dirty, error };
}
