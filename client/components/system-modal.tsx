"use client";

import { Button } from "@/components/ui/button";

interface SystemModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SystemModal({ isOpen, onClose }: SystemModalProps) {
  if (!isOpen) return null;

  return (
    <div className="pointer-events-auto w-72 md:w-80 bg-black/90 border border-cyan-400/50 rounded-lg p-4 md:p-6 glow-box backdrop-blur-sm max-h-[90vh] overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-cyan-400 font-mono text-base md:text-lg font-bold">
          SYSTEM STATUS
        </h2>
        <Button
          onClick={onClose}
          variant="ghost"
          size="icon-sm"
          className="text-cyan-400 hover:text-cyan-300"
        >
          ×
        </Button>
      </div>
      <div className="space-y-4 text-cyan-300 font-mono text-xs md:text-sm">
        <div className="flex justify-between">
          <span>CPU Usage:</span>
          <span className="text-cyan-400">12.5%</span>
        </div>
        <div className="flex justify-between">
          <span>RAM Usage:</span>
          <span className="text-cyan-400">4.2 GB / 16 GB</span>
        </div>
        <div className="flex justify-between">
          <span>Network:</span>
          <span className="text-cyan-400">Active</span>
        </div>
        <div className="flex justify-between">
          <span>Status:</span>
          <span className="text-green-400">Operational</span>
        </div>
      </div>
    </div>
  );
}
