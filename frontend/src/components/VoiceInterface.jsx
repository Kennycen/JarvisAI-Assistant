import { useState, useEffect, useRef } from "react";
import { createRoom } from "../utils/api";
import { connectToRoom, setupAudioHandlers } from "../utils/livekit";
import StatusIndicator from "./StatusIndicator";

const VoiceInterface = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [status, setStatus] = useState("Disconnected");
  const [room, setRoom] = useState(null);
  const audioRef = useRef(null);

  const connect = async () => {
    try {
      setStatus("Creating room...");

      // Create room via API
      const { room_name, token, url } = await createRoom();

      setStatus("Connecting to room...");

      // Connect to LiveKit room
      const newRoom = await connectToRoom(url, token);

      // Set up audio handlers
      setupAudioHandlers(newRoom, audioRef.current);

      // Enable microphone
      await newRoom.localParticipant.setMicrophoneEnabled(true);

      setRoom(newRoom);
      setIsConnected(true);
      setIsMuted(false);
      setStatus("Connected - Speak to JARVIS");
    } catch (error) {
      console.error("Connection error:", error);
      setStatus(`Error: ${error.message}`);
      setIsConnected(false);
    }
  };

  const disconnect = async () => {
    if (room) {
      room.disconnect();
      setRoom(null);
      setIsConnected(false);
      setStatus("Disconnected");
    }
  };

  const toggleMute = async () => {
    if (room) {
      const isCurrentlyMuted = !room.localParticipant.isMicrophoneEnabled;
      await room.localParticipant.setMicrophoneEnabled(isCurrentlyMuted);
      setIsMuted(!isCurrentlyMuted);
    }
  };

  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [room]);

  return (
    <div className="voice-interface">
      <StatusIndicator status={status} />

      <div className="controls">
        {!isConnected ? (
          <button onClick={connect} className="btn btn-primary">
            Connect to JARVIS
          </button>
        ) : (
          <>
            <button
              onClick={toggleMute}
              className={`btn ${isMuted ? "btn-muted" : "btn-active"}`}
            >
              {isMuted ? "🔇 Unmute" : "🎤 Mute"}
            </button>
            <button onClick={disconnect} className="btn btn-danger">
              Disconnect
            </button>
          </>
        )}
      </div>

      <audio ref={audioRef} autoPlay />
    </div>
  );
};

export default VoiceInterface;
