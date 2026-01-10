/**
 * AdminOpsPage Component
 * Admin operations: autopilot, analytics, multi-currency balances
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ToggleLeft, ToggleRight, TrendingUp, DollarSign } from "lucide-react";
import { api } from "../api/endpoints";

export function AdminOpsPage() {
  const qc = useQueryClient();

  // Fetch analytics dashboard
  const analyticsQ = useQuery({
    queryKey: ["analytics"],
    queryFn: api.getAnalyticsDashboard,
    refetchInterval: 10000,
  });

  // Fetch multi-currency balances
  const balancesQ = useQuery({
    queryKey: ["balances"],
    queryFn: api.getMultiCurrencyBalances,
    refetchInterval: 10000,
  });

  // Fetch settings for autopilot status
  const settingsQ = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
  });

  // Toggle autopilot mutation
  const autopilotMut = useMutation({
    mutationFn: (enabled: boolean) => api.toggleAutopilot(enabled),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
    },
  });

  const analytics = analyticsQ.data;
  const balances = balancesQ.data;
  const autopilotEnabled = settingsQ.data?.autopilot_enabled || false;

  return (
    <div className="space-y-6">
      {/* Autopilot Control */}
      <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold text-green-400 mb-2">
              AUTOPILOT MODE
            </h3>
            <p className="text-sm text-green-600">
              {autopilotEnabled
                ? "CFO is making autonomous decisions"
                : "Manual approval required for all operations"}
            </p>
          </div>
          <button
            onClick={() => autopilotMut.mutate(!autopilotEnabled)}
            disabled={autopilotMut.isPending}
            className={`
              flex items-center gap-2 px-6 py-3 border-2 rounded-lg font-semibold transition-all
              ${
                autopilotEnabled
                  ? "bg-green-900 border-green-400 text-green-400 hover:bg-green-800"
                  : "bg-gray-800 border-gray-600 text-gray-400 hover:bg-gray-700"
              }
            `}
          >
            {autopilotEnabled ? (
              <>
                <ToggleRight className="w-6 h-6" />
                <span>ENABLED</span>
              </>
            ) : (
              <>
                <ToggleLeft className="w-6 h-6" />
                <span>DISABLED</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Multi-Currency Balances */}
      {balances && (
        <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-green-400 mb-4 flex items-center gap-2">
            <DollarSign className="w-6 h-6" />
            MULTI-CURRENCY TREASURY
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">USDC</div>
              <div className="text-2xl font-bold text-green-400">
                ${balances.USDC.toLocaleString()}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">EUR</div>
              <div className="text-2xl font-bold text-green-400">
                €{balances.EUR.toLocaleString()}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">BTC</div>
              <div className="text-2xl font-bold text-green-400">
                ₿{balances.BTC.toFixed(8)}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-blue-900 rounded">
              <div className="text-sm text-blue-600 mb-1">
                TOTAL USD EQUIVALENT
              </div>
              <div className="text-2xl font-bold text-blue-400">
                ${balances.total_usd_equivalent.toLocaleString()}
              </div>
            </div>
          </div>
          <div className="mt-4 text-sm text-green-600">
            Network: <span className="text-green-400">{balances.network}</span>
          </div>
        </div>
      )}

      {/* System Analytics */}
      {analytics && (
        <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-green-400 mb-4 flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            SYSTEM ANALYTICS
          </h3>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">
                TOTAL TRANSACTIONS
              </div>
              <div className="text-2xl font-bold text-green-400">
                {analytics.total_transactions.toLocaleString()}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">TOTAL VOLUME</div>
              <div className="text-2xl font-bold text-green-400">
                ${analytics.total_volume.toLocaleString()}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">ACTIVE AGENTS</div>
              <div className="text-2xl font-bold text-green-400">
                {analytics.active_agents}
              </div>
            </div>
          </div>

          {/* System Health */}
          <div className="p-4 bg-black/50 border border-green-900 rounded mb-6">
            <h4 className="text-sm font-semibold text-green-400 mb-3">
              SYSTEM HEALTH
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-green-600">Status:</span>{" "}
                <span
                  className={
                    analytics.system_health.status === "healthy"
                      ? "text-green-400"
                      : "text-yellow-400"
                  }
                >
                  {analytics.system_health.status.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-green-600">Solvency Ratio:</span>{" "}
                <span className="text-green-400">
                  {analytics.system_health.solvency_ratio.toFixed(2)}x
                </span>
              </div>
              <div>
                <span className="text-green-600">Runway:</span>{" "}
                <span className="text-green-400">
                  {analytics.system_health.runway_days} days
                </span>
              </div>
            </div>
          </div>

          {/* Top Agents */}
          <div className="p-4 bg-black/50 border border-green-900 rounded">
            <h4 className="text-sm font-semibold text-green-400 mb-3">
              TOP PERFORMING AGENTS
            </h4>
            <div className="space-y-2">
              {analytics.top_agents.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="flex items-center justify-between p-2 bg-black/50 border border-green-950 rounded"
                >
                  <div className="text-green-400 font-mono">
                    {agent.agent_id}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-green-600">
                      Earned: ${agent.earned.toLocaleString()}
                    </div>
                    <div className="text-sm text-green-600">
                      Score: {agent.credit_score.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
