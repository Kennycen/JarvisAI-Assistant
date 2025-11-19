"use client";

import { Button } from "@/components/ui/button";

interface StatusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function StatusModal({ isOpen, onClose }: StatusModalProps) {
  if (!isOpen) return null;

  return (
    <div className="pointer-events-auto w-80 bg-black/90 border border-cyan-400/50 rounded-lg p-6 glow-box backdrop-blur-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-cyan-400 font-mono text-lg font-bold">STATUS</h2>
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
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span>Voice Interface: Active</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span>Calendar: Connected</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span>Email: Ready</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span>Search: Online</span>
        </div>
      </div>
    </div>
  );
}
