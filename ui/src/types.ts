/**
 * Frontend Types for Matrix Treasury Mission Control
 * Production-ready TypeScript type definitions
 */

export type TransactionType = "EXPENSE" | "INCOME" | "SYSTEM";
export type Status = "APPROVED" | "DENIED" | "PENDING";
export type Tab = "MONITOR" | "ADMIN" | "WIRES" | "CHAT";

export interface LogEntry {
  id: number | string;
  time: string;
  agent: string;
  action: string;
  cost: number;
  type: TransactionType;
  status: Status;
  reason?: string;
}

export interface DashboardVitals {
  usdc_balance: number;
  mxu_supply: number;
  coverage_ratio: number;
  runway_days: number;
  health_status: "HEALTHY" | "WARNING" | "CRITICAL";
}

export interface NetworkHealth {
  akash_nodes_active: number;
  akash_nodes_total: number;
  compute_load_percent: number;
  infrastructure_health: "HEALTHY" | "WARNING" | "CRITICAL";
}

export interface PendingApproval {
  id: number;
  agent_id: string;
  action: string;
  cost_usd: number;
  reason: string;
  submitted_at: string;
}

export interface CFOInsight {
  message: string;
  timestamp: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
}

export interface AnalyticsDashboard {
  total_transactions: number;
  total_volume: number;
  active_agents: number;
  system_health: {
    status: "healthy" | "warning" | "critical";
    solvency_ratio: number;
    runway_days: number;
  };
  hourly_volume: Array<{ hour: string; volume: number }>;
  top_agents: Array<{
    agent_id: string;
    earned: number;
    credit_score: number;
  }>;
}

export interface MultiCurrencyBalances {
  USDC: number;
  EUR: number;
  BTC: number;
  total_usd_equivalent: number;
  network: string;
}

export interface BankAccount {
  account_id: string;
  account_name: string;
  account_number: string;
  routing_number: string;
  swift_code: string;
  bank_name: string;
  currency: string;
}

export interface CryptoWallet {
  wallet_id: string;
  address: string;
  network: string;
  currency: string;
  label: string;
}

export interface PaymentMethods {
  bank_accounts: BankAccount[];
  crypto_wallets: CryptoWallet[];
}

export interface WithdrawalRequest {
  amount: number;
  currency: string;
  network: string;
  destination: string;
  method: "crypto" | "wire";
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface SettingsData {
  llm_provider: "openai" | "anthropic" | "watsonx" | "ollama";
  openai_key?: string;
  anthropic_key?: string;
  watsonx_key?: string;
  ollama_host?: string;
  autopilot_enabled: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthMe {
  username: string;
  is_admin: boolean;
}
