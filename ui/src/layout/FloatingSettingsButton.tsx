/**
 * FloatingSettingsButton Component
 * Floating action button to open settings modal
 */

import { Settings } from "lucide-react";
import { useState } from "react";
import { SettingsModal } from "../components/SettingsModal";

export function FloatingSettingsButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-8 right-8 w-14 h-14 bg-green-900 hover:bg-green-800 border-2 border-green-400 rounded-full flex items-center justify-center shadow-lg shadow-green-900/50 transition-all hover:scale-110 z-40"
        title="Settings"
      >
        <Settings className="w-6 h-6 text-green-400" />
      </button>

      <SettingsModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
