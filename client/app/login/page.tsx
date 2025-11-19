"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function Login() {
  const { signInWithGoogle, signInWithMicrosoft } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      setError(null);
      await signInWithGoogle();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftSignIn = async () => {
    try {
      setLoading(true);
      setError(null);
      await signInWithMicrosoft();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 opacity-20">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 217, 255, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 217, 255, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: "50px 50px",
          }}
        />
      </div>
      <div className="relative z-10 w-full max-w-md">
        <div className="bg-black/90 border-2 border-cyan-400/50 rounded-lg p-8 glow-box backdrop-blur-sm">
          <h1 className="text-4xl font-bold text-cyan-400 mb-2 font-mono tracking-widest text-center">
            J.A.R.V.I.S
          </h1>
          <p className="text-cyan-300 text-center mb-8 font-mono">
            Sign in to access your AI assistant
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-400/50 rounded text-red-300 text-sm font-mono">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <Button
              onClick={handleGoogleSignIn}
              disabled={loading}
              className="w-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono"
            >
              {loading ? "Loading..." : "Continue with Google"}
            </Button>

            <Button
              onClick={handleMicrosoftSignIn}
              disabled={loading}
              className="w-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono"
            >
              {loading ? "Loading..." : "Continue with Microsoft"}
            </Button>
          </div>

          <p className="mt-6 text-cyan-400/60 text-xs text-center font-mono">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
