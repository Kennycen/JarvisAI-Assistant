"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/contexts/AuthContext";

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          console.error("Auth error:", error);
          router.push("/login?error=auth_failed");
        } else if (data.session) {
          // Redirect to dashboard after successful authentication
          router.push("/dashboard");
        } else {
          router.push("/login");
        }
      } catch (err) {
        console.error("Callback error:", err);
        router.push("/login?error=callback_error");
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
