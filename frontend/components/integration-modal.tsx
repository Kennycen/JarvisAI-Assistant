"use client";

import { Button } from "@/components/ui/button";

interface IntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenModal: (modal: string) => void;
}

export default function IntegrationModal({
  isOpen,
  onClose,
  onOpenModal,
}: IntegrationModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto">
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-96 bg-black/95 border-2 border-cyan-400/50 rounded-lg p-8 glow-box">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-cyan-400 font-mono text-xl font-bold">
            INTEGRATIONS
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
        <div className="space-y-4">
          <Button
            onClick={() => {
              onOpenModal("system");
              onClose();
            }}
            className="w-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono"
          >
            SYSTEM STATUS
          </Button>
          <Button
            onClick={() => {
              onOpenModal("weather");
              onClose();
            }}
            className="w-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono"
          >
            WEATHER
          </Button>
          <Button
            onClick={() => {
              onOpenModal("status");
              onClose();
            }}
            className="w-full bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono"
          >
            SERVICE STATUS
          </Button>
        </div>
      </div>
    </div>
  );
}
