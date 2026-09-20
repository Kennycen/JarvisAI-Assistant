import { API_URL } from "@/lib/api";

/** Mirrors jarvis.core.profile.Profile. */
export interface Profile {
  preferred_name: string;
  location: string;
  occupation: string;
  about: string;
  preferences: string;
}

export const EMPTY_PROFILE: Profile = {
  preferred_name: "",
  location: "",
  occupation: "",
  about: "",
  preferences: "",
};

export async function fetchProfile(): Promise<Profile> {
  const res = await fetch(`${API_URL}/api/profile`);
  if (!res.ok) throw new Error(`Could not load your profile (${res.status}).`);
  return res.json();
}

export async function saveProfile(profile: Profile): Promise<Profile> {
  const res = await fetch(`${API_URL}/api/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(`Could not save your profile (${res.status}).`);
  return res.json();
}
