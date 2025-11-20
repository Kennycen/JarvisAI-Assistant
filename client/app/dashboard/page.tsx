"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import JarvisCore from "@/components/jarvis-core";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import UserProfile from "@/components/user-profile";
import CalendarAuth from "@/components/calendar-auth";
import SystemModal from "@/components/system-modal";
import WeatherModal from "@/components/weather-modal";
import StatusModal from "@/components/status-modal";
import IntegrationModal from "@/components/integration-modal";
import { createRoom } from "@/lib/api";
import { connectToRoom, setupAudioHandlers } from "@/lib/livekit";
import { Room } from "livekit-client";
import api from "@/lib/api";

export default function Dashboard() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("Disconnected");
  const [room, setRoom] = useState<Room | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [calendarConnected, setCalendarConnected] = useState(false);
  const [calendarConnecting, setCalendarConnecting] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  // Check calendar status on mount
  useEffect(() => {
    if (user) {
      checkCalendarStatus();
    }
  }, [user]);

  const checkCalendarStatus = async () => {
    try {
      const response = await api.get("/api/auth/calendar/status");
      setCalendarConnected(response.data.authenticated);
    } catch (error) {
      console.error("Error checking calendar status:", error);
      setCalendarConnected(false);
    }
  };

  const handleCalendarConnect = async () => {
    if (calendarConnected) {
      setActiveModal("calendar");
      return;
    }

    try {
      setCalendarConnecting(true);
      const response = await api.get("/api/auth/google/calendar");
      window.location.href = response.data.authorization_url;
    } catch (error) {
      console.error("Error connecting Google Calendar:", error);
      alert("Failed to connect Google Calendar. Please try again.");
      setCalendarConnecting(false);
    }
  };

  const handleConnect = async () => {
    if (isConnected && room) {
      try {
        room.disconnect();
        setRoom(null);
        setIsConnected(false);
        setConnectionStatus("Disconnected");
      } catch (error) {
        console.error("Disconnect error:", error);
      }
      return;
    }

    try {
      setIsConnecting(true);
      setConnectionStatus("Creating room...");

      const { room_name, token, url } = await createRoom();

      setConnectionStatus("Connecting to room...");

      const newRoom = await connectToRoom(url, token);

      if (audioRef.current) {
        setupAudioHandlers(newRoom, audioRef.current);
      }

      await newRoom.localParticipant.setMicrophoneEnabled(true);

      setRoom(newRoom);
      setIsConnected(true);
      setIsConnecting(false);
      setConnectionStatus("Connected - Speak to JARVIS");
    } catch (error: any) {
      console.error("Connection error:", error);
      setConnectionStatus(`Error: ${error.message}`);
      setIsConnected(false);
      setIsConnecting(false);
    }
  };

  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [room]);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("calendar_auth") === "success") {
      checkCalendarStatus();
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center overflow-hidden">
        <div className="text-cyan-400 font-mono text-xl animate-pulse">
          {loading ? "INITIALIZING J.A.R.V.I.S..." : "REDIRECTING..."}
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-black relative overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-20 pointer-events-none">
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

      {/* Top Header */}
      <div className="absolute top-0 left-0 right-0 z-50 p-4 md:p-6 flex justify-between items-start">
        <div className="flex flex-col gap-2">
          <div className="text-cyan-400 font-mono text-xs md:text-sm">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
          <div className="text-cyan-300 font-mono text-sm md:text-lg">
            {new Date().toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </div>
          {connectionStatus && (
            <div
              className={`text-xs font-mono mt-2 ${
                isConnected
                  ? "text-green-400"
                  : isConnecting
                  ? "text-yellow-400"
                  : "text-cyan-400/60"
              }`}
            >
              {connectionStatus}
            </div>
          )}
        </div>
        <div className="flex gap-2 md:gap-4 items-center flex-wrap">
          <Button
            onClick={handleCalendarConnect}
            disabled={calendarConnecting}
            className={`bg-cyan-500/20 border text-cyan-300 hover:bg-cyan-500/30 font-mono text-xs transition-all ${
              calendarConnected
                ? "border-green-400 bg-green-500/20 hover:bg-green-500/30"
                : "border-cyan-400"
            }`}
          >
            {calendarConnecting ? (
              "CONNECTING..."
            ) : calendarConnected ? (
              <>
                <span className="w-2 h-2 bg-green-400 rounded-full inline-block mr-2 animate-pulse" />
                CALENDAR
              </>
            ) : (
              "📅 CALENDAR"
            )}
          </Button>
          <Button
            onClick={() => setActiveModal("integration")}
            className="bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono text-xs"
          >
            INTEGRATIONS
          </Button>
          <UserProfile />
        </div>
      </div>

      {/* Center Core */}
      <div className="h-full w-full flex items-center justify-center relative z-10">
        <JarvisCore
          onClick={handleConnect}
          isConnected={isConnected}
          isConnecting={isConnecting}
        />
      </div>

      {/* Hidden audio element for LiveKit */}
      <audio ref={audioRef} autoPlay className="hidden" />

      {/* Modals positioned around the core */}
      <div className="absolute inset-0 pointer-events-none z-20 overflow-visible">
        <div className="absolute top-20 left-1/2 -translate-x-1/2">
          <SystemModal
            isOpen={activeModal === "system"}
            onClose={() => setActiveModal(null)}
          />
        </div>

        <div className="absolute left-4 md:left-8 top-1/2 -translate-y-1/2">
          <WeatherModal
            isOpen={activeModal === "weather"}
            onClose={() => setActiveModal(null)}
          />
        </div>

        <div className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2">
          <StatusModal
            isOpen={activeModal === "status"}
            onClose={() => setActiveModal(null)}
          />
        </div>

        <div className="absolute bottom-20 left-1/2 -translate-x-1/2">
          <CalendarAuth />
        </div>
      </div>

      {/* Integration Modal */}
      <IntegrationModal
        isOpen={activeModal === "integration"}
        onClose={() => setActiveModal(null)}
        onOpenModal={(modal) => setActiveModal(modal)}
      />

      {/* Calendar Modal */}
      {activeModal === "calendar" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto">
          <div
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
            onClick={() => setActiveModal(null)}
          />
          <div className="relative w-full max-w-md mx-4 bg-black/95 border-2 border-cyan-400/50 rounded-lg p-8 glow-box">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-cyan-400 font-mono text-xl font-bold">
                CALENDAR
              </h2>
              <Button
                onClick={() => setActiveModal(null)}
                variant="ghost"
                size="icon-sm"
                className="text-cyan-400 hover:text-cyan-300"
              >
                ×
              </Button>
            </div>
            <CalendarAuth />
          </div>
        </div>
      )}

      {/* Navigation buttons around core */}
      <div className="absolute inset-0 pointer-events-none z-30">
        <div className="absolute top-[20%] left-1/2 -translate-x-1/2">
          <Button
            onClick={() =>
              setActiveModal(activeModal === "system" ? null : "system")
            }
            className="pointer-events-auto bg-cyan-500/10 border border-cyan-400/50 text-cyan-300 hover:bg-cyan-500/20 font-mono text-xs px-4 py-2"
          >
            SYSTEM
          </Button>
        </div>

        <div className="absolute left-[10%] top-1/2 -translate-y-1/2">
          <Button
            onClick={() =>
              setActiveModal(activeModal === "weather" ? null : "weather")
            }
            className="pointer-events-auto bg-cyan-500/10 border border-cyan-400/50 text-cyan-300 hover:bg-cyan-500/20 font-mono text-xs px-4 py-2"
          >
            WEATHER
          </Button>
        </div>

        <div className="absolute right-[10%] top-1/2 -translate-y-1/2">
          <Button
            onClick={() =>
              setActiveModal(activeModal === "status" ? null : "status")
            }
            className="pointer-events-auto bg-cyan-500/10 border border-cyan-400/50 text-cyan-300 hover:bg-cyan-500/20 font-mono text-xs px-4 py-2"
          >
            STATUS
          </Button>
        </div>
      </div>
    </div>
  );
}
