/**
 * TopBar Component
 * Application header with title and logout button
 */

import { LogOut } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useNavigate } from "react-router-dom";

export function TopBar() {
  const { logout, me } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="border-b border-green-900 bg-black/50 backdrop-blur">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-green-400">
            MATRIX TREASURY
          </h1>
          <p className="text-xs text-green-600 mt-1">
            MISSION CONTROL • AUTONOMOUS ECONOMIC SYSTEM
          </p>
        </div>
        <div className="flex items-center gap-4">
          {me && (
            <div className="text-right text-sm">
              <div className="text-green-400">{me.username}</div>
              <div className="text-green-600">
                {me.is_admin ? "ADMIN" : "USER"}
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-800 rounded transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">LOGOUT</span>
          </button>
        </div>
      </div>
    </div>
  );
}
