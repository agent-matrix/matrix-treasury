/**
 * LoginPage Component
 * JWT authentication login page
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, User } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { api } from "../api/endpoints";

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await api.login(username, password);
      login(response.access_token);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo / Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-green-400 mb-2">
            MATRIX TREASURY
          </h1>
          <p className="text-green-600 text-sm">MISSION CONTROL ACCESS</p>
        </div>

        {/* Login Form */}
        <div className="bg-gray-900 border-2 border-green-400 rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username */}
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                USERNAME
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-green-600" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-black border border-green-700 rounded pl-12 pr-4 py-3 text-green-400 focus:outline-none focus:border-green-400"
                  placeholder="Enter username"
                  required
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                PASSWORD
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-green-600" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-black border border-green-700 rounded pl-12 pr-4 py-3 text-green-400 focus:outline-none focus:border-green-400"
                  placeholder="Enter password"
                  required
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-green-900 hover:bg-green-800 border-2 border-green-400 rounded font-semibold text-green-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "AUTHENTICATING..." : "LOGIN"}
            </button>
          </form>
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center text-green-600 text-xs">
          <p>AUTHORIZED PERSONNEL ONLY</p>
          <p className="mt-1">ALL ACCESS IS LOGGED AND MONITORED</p>
        </div>
      </div>
    </div>
  );
}
