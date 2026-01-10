/**
 * App Component
 * Main application with routing and authentication
 */

import { useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthProvider";
import { RequireAuth } from "./auth/RequireAuth";
import { AppShell } from "./layout/AppShell";
import { LoginPage } from "./pages/LoginPage";
import { MonitorPage } from "./pages/MonitorPage";
import { AdminOpsPage } from "./pages/AdminOpsPage";
import { WiresPage } from "./pages/WiresPage";
import { ChatPage } from "./pages/ChatPage";
import type { Tab } from "./types";

function Dashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>("MONITOR");

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    // Update URL
    navigate(`/${tab.toLowerCase()}`);
  };

  return (
    <AppShell activeTab={activeTab} onTabChange={handleTabChange}>
      <Routes>
        <Route path="/monitor" element={<MonitorPage />} />
        <Route path="/admin" element={<AdminOpsPage />} />
        <Route path="/wires" element={<WiresPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/" element={<Navigate to="/monitor" replace />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
      </Routes>
    </AuthProvider>
  );
}
