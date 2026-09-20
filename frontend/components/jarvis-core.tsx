"use client";

import { useEffect, useState } from "react";

interface JarvisCoreProps {
  onClick?: () => void;
  isConnected?: boolean;
  isConnecting?: boolean;
}

export default function JarvisCore({
  onClick,
  isConnected = false,
  isConnecting = false,
}: JarvisCoreProps) {
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsActive((prev) => !prev);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Update active state based on connection
  useEffect(() => {
    if (isConnected) {
      setIsActive(true);
    }
  }, [isConnected]);

  return (
    <div
      className="relative w-96 h-96 flex items-center justify-center cursor-pointer transition-all duration-300 hover:scale-105"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          onClick?.();
        }
      }}
      aria-label={isConnected ? "Disconnect from JARVIS" : "Connect to JARVIS"}
    >
      <div className="absolute inset-0 rounded-full bg-gradient-to-b from-cyan-500/30 to-blue-600/20 blur-3xl opacity-80" />
      <div
        className="absolute inset-0 rounded-full bg-radial-gradient opacity-40 blur-2xl"
        style={{
          background:
            "radial-gradient(circle, rgba(0,217,255,0.2) 0%, transparent 70%)",
        }}
      />

      <div
        className={`absolute w-96 h-96 rounded-full border-8 border-cyan-400/80 shadow-[0_0_50px_rgba(34,211,238,1),0_0_100px_rgba(0,217,255,0.5),inset_0_0_50px_rgba(34,211,238,0.2),inset_0_0_100px_rgba(0,217,255,0.1)] transition-all duration-300 ${
          isConnected
            ? "border-green-400/80 shadow-[0_0_50px_rgba(34,211,238,1),0_0_100px_rgba(0,217,255,0.5),0_0_30px_rgba(34,197,94,0.8)]"
            : ""
        } ${isConnecting ? "animate-pulse" : ""}`}
        style={{
          animation: isConnecting
            ? "pulse-ring 1s ease-in-out infinite"
            : "pulse-ring 3s ease-in-out infinite",
        }}
      />

      <div className="absolute w-96 h-96 rounded-full">
        {Array.from({ length: 32 }).map((_, i) => (
          <div
            key={i}
            className={`absolute bg-cyan-400/70 shadow-[0_0_6px_rgba(0,217,255,0.8)] transition-colors duration-300 ${
              isConnected
                ? "bg-green-400/70 shadow-[0_0_6px_rgba(34,197,94,0.8)]"
                : ""
            }`}
            style={{
              width: i % 4 === 0 ? "3px" : "1.5px",
              height: i % 4 === 0 ? "8px" : "4px",
              top: "6px",
              left: "50%",
              transform: `translateX(-50%) rotate(${(i * 360) / 32}deg)`,
              transformOrigin: "0 192px",
            }}
          />
        ))}
      </div>

      <div
        className="absolute w-88 h-88 rounded-full border-2 border-yellow-400/40 shadow-[0_0_20px_rgba(250,204,21,0.4)]"
        style={{ animation: "rotate-slow 20s linear infinite" }}
      />

      <div
        className="absolute w-80 h-80 rounded-full border-4 border-yellow-500/70 shadow-[0_0_35px_rgba(234,179,8,0.7),inset_0_0_25px_rgba(234,179,8,0.15)]"
        style={{ animation: "rotate-slow-reverse 15s linear infinite" }}
      />

      <div
        className={`absolute w-64 h-64 rounded-full border-6 border-cyan-400/90 shadow-[0_0_40px_rgba(0,217,255,1),0_0_80px_rgba(0,217,255,0.5),inset_0_0_40px_rgba(0,217,255,0.3)] transition-all duration-300 ${
          isConnected
            ? "border-green-400/90 shadow-[0_0_40px_rgba(34,197,94,1),0_0_80px_rgba(34,197,94,0.5),inset_0_0_40px_rgba(34,197,94,0.3)]"
            : ""
        }`}
        style={{ animation: "pulse-inner 2s ease-in-out infinite" }}
      />

      <div className="absolute w-64 h-64 rounded-full">
        {Array.from({ length: 16 }).map((_, i) => (
          <div
            key={i}
            className={`absolute w-1 h-2 bg-cyan-300/80 shadow-[0_0_4px_rgba(0,217,255,0.9)] transition-colors duration-300 ${
              isConnected
                ? "bg-green-300/80 shadow-[0_0_4px_rgba(34,197,94,0.9)]"
                : ""
            }`}
            style={{
              top: "4px",
              left: "50%",
              transform: `translateX(-50%) rotate(${(i * 360) / 16}deg)`,
              transformOrigin: "0 128px",
            }}
          />
        ))}
      </div>

      <div className="absolute w-72 h-72 rounded-full">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={`segment-${i}`}
            className={`absolute w-2 h-2 rounded-full bg-yellow-400/60 shadow-[0_0_8px_rgba(250,204,21,0.8)] transition-colors duration-300 ${
              isConnected
                ? "bg-green-400/60 shadow-[0_0_8px_rgba(34,197,94,0.8)]"
                : ""
            }`}
            style={{
              top: "50%",
              left: "50%",
              transform: `translate(-50%, -50%) rotate(${
                (i * 360) / 8
              }deg) translateY(-144px)`,
              animation: `blink ${1.5 + i * 0.15}s ease-in-out ${
                i * 0.2
              }s infinite`,
            }}
          />
        ))}
      </div>

      <div className="absolute w-56 h-56 rounded-full overflow-hidden">
        {/* Outer glossy layer */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-400/20 via-blue-500/10 to-transparent shadow-[inset_-15px_-15px_30px_rgba(0,0,0,0.5),inset_15px_15px_30px_rgba(0,217,255,0.2)]" />

        {/* Main core with glass effect */}
        <div
          className={`absolute inset-2 rounded-full bg-gradient-to-br from-slate-800 via-slate-900 to-black border-2 border-cyan-500/40 flex items-center justify-center transition-all duration-500 ${
            isActive || isConnected
              ? "shadow-[0_0_60px_rgba(0,217,255,0.9),inset_0_0_50px_rgba(0,217,255,0.2),inset_-20px_-20px_40px_rgba(0,0,0,0.8)]"
              : "shadow-[0_0_40px_rgba(0,217,255,0.6),inset_0_0_30px_rgba(0,217,255,0.1)]"
          } ${
            isConnected
              ? "border-green-500/40 shadow-[0_0_60px_rgba(34,197,94,0.9),inset_0_0_50px_rgba(34,197,94,0.2)]"
              : ""
          }`}
        >
          <div className="text-center z-10">
            <div
              className={`text-2xl font-bold text-cyan-300 tracking-widest font-mono glow-text-strong mb-1 transition-colors duration-300 ${
                isConnected ? "text-green-300" : ""
              }`}
            >
              J.A.R.V.I.S
            </div>
            <div
              className={`h-0.5 w-24 mx-auto bg-gradient-to-r from-transparent via-cyan-400 to-transparent mb-2 shadow-[0_0_8px_rgba(0,217,255,0.6)] transition-colors duration-300 ${
                isConnected
                  ? "via-green-400 shadow-[0_0_8px_rgba(34,197,94,0.6)]"
                  : ""
              }`}
            />
            <div
              className={`text-xs text-cyan-400/80 font-mono transition-all duration-500 ${
                isActive || isConnected
                  ? "opacity-100 tracking-wide"
                  : "opacity-50 tracking-normal"
              } ${isConnected ? "text-green-400/80" : ""} ${
                isConnecting ? "animate-pulse" : ""
              }`}
            >
              {isConnecting
                ? "CONNECTING..."
                : isConnected
                ? "CONNECTED"
                : isActive
                ? "ACTIVE"
                : "STANDBY"}
            </div>
          </div>
        </div>

        {/* Highlight reflection for glossy effect */}
        <div className="absolute top-0 left-6 w-20 h-20 rounded-full bg-white/10 blur-2xl" />
      </div>

      <div className="absolute w-64 h-64 rounded-full">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className={`absolute w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_12px_rgba(0,217,255,0.9)] transition-colors duration-300 ${
              isConnected
                ? "bg-green-400 shadow-[0_0_12px_rgba(34,197,94,0.9)]"
                : ""
            }`}
            style={{
              top: "50%",
              left: "50%",
              transform: `translate(-50%, -50%) rotate(${
                i * 60
              }deg) translateY(-132px)`,
              animation: `pulse-dots 2.5s ease-in-out ${i * 0.42}s infinite`,
            }}
          />
        ))}
      </div>

      <div
        className="absolute w-72 h-72 rounded-full border border-cyan-400/20"
        style={{ animation: "rotate-fast 8s linear infinite" }}
      />

      <style jsx>{`
        @keyframes pulse-ring {
          0%,
          100% {
            box-shadow: 0 0 50px rgba(34, 211, 238, 1),
              0 0 100px rgba(0, 217, 255, 0.5),
              inset 0 0 50px rgba(34, 211, 238, 0.2),
              inset 0 0 100px rgba(0, 217, 255, 0.1);
          }
          50% {
            box-shadow: 0 0 70px rgba(34, 211, 238, 1.2),
              0 0 140px rgba(0, 217, 255, 0.7),
              inset 0 0 60px rgba(34, 211, 238, 0.3),
              inset 0 0 120px rgba(0, 217, 255, 0.15);
          }
        }

        @keyframes pulse-inner {
          0%,
          100% {
            box-shadow: 0 0 40px rgba(0, 217, 255, 1),
              0 0 80px rgba(0, 217, 255, 0.5),
              inset 0 0 40px rgba(0, 217, 255, 0.3);
          }
          50% {
            box-shadow: 0 0 60px rgba(0, 217, 255, 1.1),
              0 0 120px rgba(0, 217, 255, 0.7),
              inset 0 0 60px rgba(0, 217, 255, 0.4);
          }
        }

        @keyframes pulse-dots {
          0%,
          100% {
            opacity: 0.4;
            transform: translate(-50%, -50%) rotate(0deg) translateY(-132px)
              scale(1);
          }
          50% {
            opacity: 1;
            transform: translate(-50%, -50%) rotate(0deg) translateY(-132px)
              scale(1.3);
          }
        }

        @keyframes rotate-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes rotate-slow-reverse {
          from {
            transform: rotate(360deg);
          }
          to {
            transform: rotate(0deg);
          }
        }

        @keyframes rotate-fast {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes blink {
          0%,
          100% {
            opacity: 0.3;
          }
          50% {
            opacity: 1;
          }
        }

        .glow-text-strong {
          text-shadow: 0 0 10px rgba(0, 217, 255, 1),
            0 0 20px rgba(0, 217, 255, 0.6), 0 0 30px rgba(0, 217, 255, 0.3);
        }
      `}</style>
    </div>
  );
}
