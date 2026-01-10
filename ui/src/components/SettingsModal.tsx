/**
 * SettingsModal Component
 * Configure LLM provider and sync settings with backend
 */

import { X, Save } from "lucide-react";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/endpoints";
import type { SettingsData } from "../types";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const qc = useQueryClient();

  // Fetch current settings from backend
  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
    enabled: isOpen,
  });

  // Local form state
  const [formData, setFormData] = useState<SettingsData>({
    llm_provider: "openai",
    autopilot_enabled: false,
  });

  // Update form when settings are fetched
  useEffect(() => {
    if (settingsQuery.data) {
      setFormData(settingsQuery.data);
    }
  }, [settingsQuery.data]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: (data: Partial<SettingsData>) => api.updateSettings(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
      onClose();
    },
  });

  const handleSave = () => {
    saveMutation.mutate(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border-2 border-green-400 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-green-900">
          <h2 className="text-xl font-bold text-green-400">SYSTEM SETTINGS</h2>
          <button
            onClick={onClose}
            className="text-green-600 hover:text-green-400 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* LLM Provider Selection */}
          <div>
            <label className="block text-sm font-semibold text-green-400 mb-2">
              LLM PROVIDER
            </label>
            <select
              value={formData.llm_provider}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  llm_provider: e.target.value as any,
                })
              }
              className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="watsonx">IBM WatsonX.ai</option>
              <option value="ollama">Ollama (Local)</option>
            </select>
          </div>

          {/* OpenAI Key */}
          {formData.llm_provider === "openai" && (
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                OPENAI API KEY
              </label>
              <input
                type="password"
                value={formData.openai_key || ""}
                onChange={(e) =>
                  setFormData({ ...formData, openai_key: e.target.value })
                }
                placeholder="sk-..."
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
              />
            </div>
          )}

          {/* Anthropic Key */}
          {formData.llm_provider === "anthropic" && (
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                ANTHROPIC API KEY
              </label>
              <input
                type="password"
                value={formData.anthropic_key || ""}
                onChange={(e) =>
                  setFormData({ ...formData, anthropic_key: e.target.value })
                }
                placeholder="sk-ant-..."
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
              />
            </div>
          )}

          {/* WatsonX Key */}
          {formData.llm_provider === "watsonx" && (
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                WATSONX API KEY
              </label>
              <input
                type="password"
                value={formData.watsonx_key || ""}
                onChange={(e) =>
                  setFormData({ ...formData, watsonx_key: e.target.value })
                }
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
              />
            </div>
          )}

          {/* Ollama Host */}
          {formData.llm_provider === "ollama" && (
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                OLLAMA HOST
              </label>
              <input
                type="text"
                value={formData.ollama_host || "http://localhost:11434"}
                onChange={(e) =>
                  setFormData({ ...formData, ollama_host: e.target.value })
                }
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
              />
            </div>
          )}

          {/* Autopilot Toggle */}
          <div className="flex items-center justify-between p-4 bg-black/50 border border-green-900 rounded">
            <div>
              <div className="font-semibold text-green-400">AUTOPILOT MODE</div>
              <div className="text-xs text-green-600 mt-1">
                Enable autonomous decision-making
              </div>
            </div>
            <button
              onClick={() =>
                setFormData({
                  ...formData,
                  autopilot_enabled: !formData.autopilot_enabled,
                })
              }
              className={`
                w-14 h-8 rounded-full transition-colors relative
                ${
                  formData.autopilot_enabled
                    ? "bg-green-600"
                    : "bg-gray-700"
                }
              `}
            >
              <div
                className={`
                  absolute top-1 w-6 h-6 bg-white rounded-full transition-transform
                  ${
                    formData.autopilot_enabled
                      ? "translate-x-7"
                      : "translate-x-1"
                  }
                `}
              />
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-green-900">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-800 hover:bg-gray-700 border border-green-700 rounded transition-colors"
          >
            CANCEL
          </button>
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="flex items-center gap-2 px-6 py-2 bg-green-900 hover:bg-green-800 border border-green-400 rounded transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saveMutation.isPending ? "SAVING..." : "SAVE"}</span>
          </button>
        </div>

        {/* Error Display */}
        {saveMutation.isError && (
          <div className="px-6 pb-4">
            <div className="p-3 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm">
              Failed to save settings. Please try again.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
