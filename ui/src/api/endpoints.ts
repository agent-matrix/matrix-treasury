/**
 * API Endpoint Wrappers for Matrix Treasury Backend
 * All backend API calls go through these typed functions
 */

import { apiFetch } from "./http";
import type {
  LoginResponse,
  AuthMe,
  DashboardVitals,
  NetworkHealth,
  PendingApproval,
  CFOInsight,
  LogEntry,
  AnalyticsDashboard,
  MultiCurrencyBalances,
  PaymentMethods,
  WithdrawalRequest,
  ChatMessage,
  SettingsData,
} from "../types";

// ===========================
// Auth Endpoints
// ===========================

export async function login(username: string, password: string) {
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ username, password }),
  });
}

export async function getMe() {
  return apiFetch<AuthMe>("/auth/me", { method: "GET" });
}

// ===========================
// Dashboard / Vitals
// ===========================

export async function getVitals() {
  return apiFetch<DashboardVitals>("/api/v1/treasury/status", { method: "GET" });
}

export async function getNetworkHealth() {
  return apiFetch<NetworkHealth>("/api/v1/network/health", { method: "GET" });
}

export async function getAnalyticsDashboard() {
  return apiFetch<AnalyticsDashboard>("/api/v1/analytics/dashboard", { method: "GET" });
}

// ===========================
// Transaction Logs
// ===========================

export async function getLogs(limit: number = 50) {
  return apiFetch<LogEntry[]>(`/api/v1/logs?limit=${limit}`, { method: "GET" });
}

// ===========================
// Governance / Approvals
// ===========================

export async function getPendingApprovals() {
  return apiFetch<PendingApproval[]>("/api/v1/governance/pending", { method: "GET" });
}

export async function approveTransaction(id: number) {
  return apiFetch<{ status: string }>(`/api/v1/governance/approve/${id}`, {
    method: "POST",
  });
}

export async function denyTransaction(id: number) {
  return apiFetch<{ status: string }>(`/api/v1/governance/deny/${id}`, {
    method: "POST",
  });
}

export async function toggleAutopilot(enabled: boolean) {
  return apiFetch<{ status: string; autopilot: boolean }>("/api/v1/governance/autopilot", {
    method: "POST",
    body: JSON.stringify({ enabled }),
  });
}

// ===========================
// CFO Insights
// ===========================

export async function getCFOInsights() {
  return apiFetch<CFOInsight[]>("/api/v1/cfo/insights", { method: "GET" });
}

// ===========================
// Multi-Currency
// ===========================

export async function getMultiCurrencyBalances() {
  return apiFetch<MultiCurrencyBalances>("/api/v1/multicurrency/balances", { method: "GET" });
}

export async function withdrawFunds(request: WithdrawalRequest) {
  return apiFetch<{ status: string; tx_hash?: string }>("/api/v1/multicurrency/withdraw", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// ===========================
// Admin Payment Methods
// ===========================

export async function getPaymentMethods() {
  return apiFetch<PaymentMethods>("/api/v1/admin/payment-methods", { method: "GET" });
}

export async function addBankAccount(account: any) {
  return apiFetch<{ status: string }>("/api/v1/admin/add-bank-account", {
    method: "POST",
    body: JSON.stringify(account),
  });
}

export async function addCryptoWallet(wallet: any) {
  return apiFetch<{ status: string }>("/api/v1/admin/add-crypto-wallet", {
    method: "POST",
    body: JSON.stringify(wallet),
  });
}

// ===========================
// Chat / Neural Link
// ===========================

export async function sendChatMessage(message: string) {
  return apiFetch<{ response: string }>("/api/v1/chat/message", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function getChatHistory() {
  return apiFetch<ChatMessage[]>("/api/v1/chat/history", { method: "GET" });
}

// ===========================
// Settings
// ===========================

export async function getSettings() {
  return apiFetch<SettingsData>("/api/v1/settings", { method: "GET" });
}

export async function updateSettings(settings: Partial<SettingsData>) {
  return apiFetch<{ status: string }>("/api/v1/settings", {
    method: "POST",
    body: JSON.stringify(settings),
  });
}

// Export all endpoints as a single object for convenience
export const api = {
  // Auth
  login,
  getMe,

  // Dashboard
  getVitals,
  getNetworkHealth,
  getAnalyticsDashboard,

  // Logs
  getLogs,

  // Governance
  getPendingApprovals,
  approveTransaction,
  denyTransaction,
  toggleAutopilot,

  // CFO
  getCFOInsights,

  // Multi-Currency
  getMultiCurrencyBalances,
  withdrawFunds,

  // Admin
  getPaymentMethods,
  addBankAccount,
  addCryptoWallet,

  // Chat
  sendChatMessage,
  getChatHistory,

  // Settings
  getSettings,
  updateSettings,
};
