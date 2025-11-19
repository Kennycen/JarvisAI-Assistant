"use client";

import { Button } from "@/components/ui/button";

interface WeatherModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function WeatherModal({ isOpen, onClose }: WeatherModalProps) {
  if (!isOpen) return null;

  return (
    <div className="pointer-events-auto w-80 bg-black/90 border border-cyan-400/50 rounded-lg p-6 glow-box backdrop-blur-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-cyan-400 font-mono text-lg font-bold">WEATHER</h2>
        <Button
          onClick={onClose}
          variant="ghost"
          size="icon-sm"
          className="text-cyan-400 hover:text-cyan-300"
        >
          ×
        </Button>
      </div>
      <div className="space-y-4 text-cyan-300 font-mono text-sm">
        <div className="text-center">
          <div className="text-4xl text-cyan-400 mb-2">22°C</div>
          <div className="text-cyan-300">Clear Sky</div>
        </div>
        <div className="border-t border-cyan-400/30 pt-4 space-y-2">
          <div className="flex justify-between">
            <span>Humidity:</span>
            <span className="text-cyan-400">45%</span>
          </div>
          <div className="flex justify-between">
            <span>Wind:</span>
            <span className="text-cyan-400">8 km/h</span>
          </div>
        </div>
      </div>
    </div>
  );
}
