"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

export default function GmailAuth() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    if (user) {
      checkAuthStatus();
    } else {
      setLoading(false);
    }
  }, [user]);

  // Check for Gmail auth success
  useEffect(() => {
    if (searchParams.get("gmail_auth") === "success") {
      // Refresh auth status
      checkAuthStatus();
    }
  }, [searchParams]);

  const checkAuthStatus = async () => {
    try {
      const response = await api.get("/api/auth/gmail/status");
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error("Error checking Gmail auth status:", error);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const connectGoogle = async () => {
    try {
      setConnecting(true);
      const response = await api.get("/api/auth/google/gmail");

      // Redirect to Google OAuth
      window.location.href = response.data.authorization_url;
    } catch (error) {
      console.error("Error connecting Gmail:", error);
      alert("Failed to connect Gmail. Please try again.");
      setConnecting(false);
    }
  };

  const disconnect = async () => {
    try {
      await api.post("/api/auth/gmail/disconnect");
      setIsAuthenticated(false);
    } catch (error) {
      console.error("Error disconnecting:", error);
      alert("Failed to disconnect. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="pointer-events-auto w-80 bg-black/90 border border-cyan-400/50 rounded-lg p-6 glow-box backdrop-blur-sm">
        <h2 className="text-cyan-400 font-mono text-lg font-bold mb-4">
          GMAIL
        </h2>
        <div className="text-cyan-300 font-mono text-sm">
          Checking Gmail connection...
        </div>
      </div>
    );
  }

  return (
    <div className="pointer-events-auto w-80 bg-black/90 border border-cyan-400/50 rounded-lg p-6 glow-box backdrop-blur-sm">
      <h2 className="text-cyan-400 font-mono text-lg font-bold mb-4">GMAIL</h2>
      {isAuthenticated ? (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-cyan-300 font-mono text-sm">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span>✅ Gmail connected</span>
          </div>
          <Button
            onClick={disconnect}
            className="w-full bg-red-500/20 border border-red-400 text-red-300 hover:bg-red-500/30 font-mono"
          >
            Disconnect Gmail
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-cyan-300 font-mono text-sm">
            Connect Gmail to send emails through JARVIS
          </p>
          <Button
            onClick={connectGoogle}
            disabled={connecting}
            className="w-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono"
          >
            {connecting ? "Connecting..." : "Connect Gmail"}
          </Button>
        </div>
      )}
    </div>
  );
}
