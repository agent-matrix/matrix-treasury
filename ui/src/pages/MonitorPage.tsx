/**
 * MonitorPage Component
 * Real-time dashboard with live transaction stream
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Activity, AlertTriangle, CheckCircle, XCircle, Clock } from "lucide-react";
import { api } from "../api/endpoints";
import type { LogEntry, Status } from "../types";

export function MonitorPage() {
  const qc = useQueryClient();

  // Fetch vitals with 5-second polling
  const vitalsQ = useQuery({
    queryKey: ["vitals"],
    queryFn: api.getVitals,
    refetchInterval: 5000,
  });

  // Fetch network health
  const networkQ = useQuery({
    queryKey: ["network"],
    queryFn: api.getNetworkHealth,
    refetchInterval: 10000,
  });

  // Fetch logs with 3-second polling
  const logsQ = useQuery({
    queryKey: ["logs"],
    queryFn: () => api.getLogs(50),
    refetchInterval: 3000,
  });

  // Fetch pending approvals
  const pendingQ = useQuery({
    queryKey: ["pending"],
    queryFn: api.getPendingApprovals,
    refetchInterval: 5000,
  });

  // Fetch CFO insights
  const insightsQ = useQuery({
    queryKey: ["insights"],
    queryFn: api.getCFOInsights,
    refetchInterval: 30000,
  });

  // Approve mutation
  const approveMut = useMutation({
    mutationFn: (id: number) => api.approveTransaction(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pending"] });
      qc.invalidateQueries({ queryKey: ["logs"] });
    },
  });

  // Deny mutation
  const denyMut = useMutation({
    mutationFn: (id: number) => api.denyTransaction(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pending"] });
      qc.invalidateQueries({ queryKey: ["logs"] });
    },
  });

  const vitals = vitalsQ.data;
  const network = networkQ.data;
  const logs = logsQ.data || [];
  const pending = pendingQ.data || [];
  const insights = insightsQ.data || [];

  // Status colors
  const getStatusColor = (status: Status) => {
    switch (status) {
      case "APPROVED":
        return "text-green-400 border-green-700 bg-green-950/20";
      case "DENIED":
        return "text-red-400 border-red-700 bg-red-950/20";
      case "PENDING":
        return "text-yellow-400 border-yellow-700 bg-yellow-950/20";
      default:
        return "text-gray-400 border-gray-700 bg-gray-950/20";
    }
  };

  const getStatusIcon = (status: Status) => {
    switch (status) {
      case "APPROVED":
        return <CheckCircle className="w-4 h-4" />;
      case "DENIED":
        return <XCircle className="w-4 h-4" />;
      case "PENDING":
        return <Clock className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Vitals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Treasury Balance */}
        <div className="bg-gray-900 border border-green-700 rounded-lg p-4">
          <div className="text-sm text-green-600 mb-1">TREASURY BALANCE</div>
          <div className="text-2xl font-bold text-green-400">
            ${vitals?.usdc_balance.toLocaleString() || "0"}
          </div>
        </div>

        {/* Coverage Ratio */}
        <div className="bg-gray-900 border border-green-700 rounded-lg p-4">
          <div className="text-sm text-green-600 mb-1">COVERAGE RATIO</div>
          <div className="text-2xl font-bold text-green-400">
            {vitals?.coverage_ratio.toFixed(2) || "0.00"}x
          </div>
        </div>

        {/* Runway */}
        <div className="bg-gray-900 border border-green-700 rounded-lg p-4">
          <div className="text-sm text-green-600 mb-1">RUNWAY</div>
          <div className="text-2xl font-bold text-green-400">
            {vitals?.runway_days || "0"} days
          </div>
        </div>

        {/* Health Status */}
        <div className="bg-gray-900 border border-green-700 rounded-lg p-4">
          <div className="text-sm text-green-600 mb-1">SYSTEM HEALTH</div>
          <div
            className={`text-2xl font-bold ${
              vitals?.health_status === "HEALTHY"
                ? "text-green-400"
                : vitals?.health_status === "WARNING"
                ? "text-yellow-400"
                : "text-red-400"
            }`}
          >
            {vitals?.health_status || "UNKNOWN"}
          </div>
        </div>
      </div>

      {/* Network Health */}
      {network && (
        <div className="bg-gray-900 border border-green-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-green-400 mb-3">
            NETWORK HEALTH
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-green-600">Akash Nodes:</span>{" "}
              <span className="text-green-400">
                {network.akash_nodes_active}/{network.akash_nodes_total}
              </span>
            </div>
            <div>
              <span className="text-green-600">Compute Load:</span>{" "}
              <span className="text-green-400">
                {network.compute_load_percent.toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-green-600">Status:</span>{" "}
              <span
                className={
                  network.infrastructure_health === "HEALTHY"
                    ? "text-green-400"
                    : "text-yellow-400"
                }
              >
                {network.infrastructure_health}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Pending Approvals */}
      {pending.length > 0 && (
        <div className="bg-gray-900 border border-yellow-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-yellow-400 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            PENDING APPROVALS ({pending.length})
          </h3>
          <div className="space-y-2">
            {pending.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 bg-black/50 border border-yellow-900 rounded"
              >
                <div className="flex-1">
                  <div className="text-green-400 font-semibold">
                    {item.agent_id}
                  </div>
                  <div className="text-sm text-green-600">
                    {item.action} - ${item.cost_usd.toFixed(2)}
                  </div>
                  <div className="text-xs text-green-700 mt-1">
                    {item.reason}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => approveMut.mutate(item.id)}
                    disabled={approveMut.isPending}
                    className="px-3 py-1 bg-green-900 hover:bg-green-800 border border-green-400 rounded text-xs transition-colors"
                  >
                    APPROVE
                  </button>
                  <button
                    onClick={() => denyMut.mutate(item.id)}
                    disabled={denyMut.isPending}
                    className="px-3 py-1 bg-red-900 hover:bg-red-800 border border-red-400 rounded text-xs transition-colors"
                  >
                    DENY
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CFO Insights */}
      {insights.length > 0 && (
        <div className="bg-gray-900 border border-blue-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-blue-400 mb-3">
            CFO INSIGHTS
          </h3>
          <div className="space-y-2">
            {insights.map((insight, i) => (
              <div
                key={i}
                className={`p-3 border rounded ${
                  insight.priority === "HIGH"
                    ? "border-red-700 bg-red-950/20 text-red-400"
                    : insight.priority === "MEDIUM"
                    ? "border-yellow-700 bg-yellow-950/20 text-yellow-400"
                    : "border-blue-700 bg-blue-950/20 text-blue-400"
                }`}
              >
                <div className="text-sm">{insight.message}</div>
                <div className="text-xs opacity-60 mt-1">
                  {new Date(insight.timestamp).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transaction Log */}
      <div className="bg-gray-900 border border-green-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-green-400 mb-3">
          LIVE TRANSACTION STREAM
        </h3>
        <div className="space-y-1 max-h-96 overflow-y-auto">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`flex items-center justify-between p-2 border rounded text-sm ${getStatusColor(
                log.status
              )}`}
            >
              <div className="flex items-center gap-3 flex-1">
                <div className="flex-shrink-0">
                  {getStatusIcon(log.status)}
                </div>
                <div className="flex-1">
                  <span className="font-mono text-xs opacity-60">
                    {log.time}
                  </span>
                  {" • "}
                  <span className="font-semibold">{log.agent}</span>
                  {" • "}
                  <span>{log.action}</span>
                </div>
                <div className="font-mono font-bold">
                  {log.type === "EXPENSE" ? "-" : "+"}$
                  {log.cost.toFixed(2)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
