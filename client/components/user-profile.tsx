"use client";

import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export default function UserProfile() {
  const { user, signOut } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-cyan-300 font-mono font-bold">
        {user.email?.[0]?.toUpperCase() || "U"}
      </div>
      <div className="flex flex-col">
        <span className="text-cyan-300 font-mono text-xs">
          {user.email?.split("@")[0] || "User"}
        </span>
        <Button
          onClick={signOut}
          variant="ghost"
          size="sm"
          className="text-cyan-400 hover:text-cyan-300 font-mono text-xs h-auto p-0"
        >
          Sign Out
        </Button>
      </div>
    </div>
  );
}
