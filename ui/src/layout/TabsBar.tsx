/**
 * TabsBar Component
 * Navigation tabs for different sections
 */

import { Monitor, Shield, Send, MessageSquare } from "lucide-react";
import type { Tab } from "../types";

interface TabsBarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const tabs: Array<{ id: Tab; label: string; icon: React.ElementType }> = [
  { id: "MONITOR", label: "MONITOR", icon: Monitor },
  { id: "ADMIN", label: "ADMIN OPS", icon: Shield },
  { id: "WIRES", label: "WIRE TRANSFERS", icon: Send },
  { id: "CHAT", label: "NEURAL LINK", icon: MessageSquare },
];

export function TabsBar({ activeTab, onTabChange }: TabsBarProps) {
  return (
    <div className="border-b border-green-900 bg-black/30">
      <div className="container mx-auto px-4">
        <div className="flex gap-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  flex items-center gap-2 px-6 py-3 border-b-2 transition-colors
                  ${
                    isActive
                      ? "border-green-400 text-green-400 bg-green-950/20"
                      : "border-transparent text-green-600 hover:text-green-400 hover:bg-green-950/10"
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-semibold">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
