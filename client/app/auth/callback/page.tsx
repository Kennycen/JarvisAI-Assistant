"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/contexts/AuthContext";

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    const handleAuthCallback = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Auth error:", error);
        router.push("/login");
      } else if (data.session) {
        router.push("/");
      }
    };

    handleAuthCallback();
  }, [router]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="text-cyan-400 font-mono text-xl animate-pulse">
        AUTHENTICATING...
      </div>
    </div>
  );
}
