/**
 * AppShell Component
 * Main layout wrapper for authenticated pages
 */

import React from "react";
import { TopBar } from "./TopBar";
import { TabsBar } from "./TabsBar";
import { FloatingSettingsButton } from "./FloatingSettingsButton";
import type { Tab } from "../types";

interface AppShellProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  children: React.ReactNode;
}

export function AppShell({ activeTab, onTabChange, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-black text-green-400 font-mono">
      <TopBar />
      <TabsBar activeTab={activeTab} onTabChange={onTabChange} />
      <main className="container mx-auto px-4 pb-8">{children}</main>
      <FloatingSettingsButton />
    </div>
  );
}
