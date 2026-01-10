/**
 * WiresPage Component
 * Wire transfer management - crypto and bank withdrawals
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Plus, Building, Wallet } from "lucide-react";
import { api } from "../api/endpoints";
import type { WithdrawalRequest } from "../types";

export function WiresPage() {
  const qc = useQueryClient();

  // Fetch payment methods
  const methodsQ = useQuery({
    queryKey: ["payment-methods"],
    queryFn: api.getPaymentMethods,
  });

  // Fetch balances
  const balancesQ = useQuery({
    queryKey: ["balances"],
    queryFn: api.getMultiCurrencyBalances,
  });

  // Withdrawal mutation
  const withdrawMut = useMutation({
    mutationFn: (req: WithdrawalRequest) => api.withdrawFunds(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["balances"] });
      setWithdrawalForm({
        amount: 0,
        currency: "USDC",
        network: "base",
        destination: "",
        method: "crypto",
      });
    },
  });

  // Form state
  const [withdrawalForm, setWithdrawalForm] = useState<WithdrawalRequest>({
    amount: 0,
    currency: "USDC",
    network: "base",
    destination: "",
    method: "crypto",
  });

  const [showAddBank, setShowAddBank] = useState(false);
  const [showAddWallet, setShowAddWallet] = useState(false);

  const methods = methodsQ.data;
  const balances = balancesQ.data;

  const handleWithdraw = () => {
    if (withdrawalForm.amount <= 0 || !withdrawalForm.destination) {
      alert("Please fill in all fields");
      return;
    }
    withdrawMut.mutate(withdrawalForm);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-green-400 mb-2">
          WIRE TRANSFERS
        </h2>
        <p className="text-green-600 text-sm">
          Manage crypto and bank withdrawals from treasury
        </p>
      </div>

      {/* Current Balances */}
      {balances && (
        <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-400 mb-4">
            AVAILABLE BALANCES
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">USDC</div>
              <div className="text-xl font-bold text-green-400">
                ${balances.USDC.toLocaleString()}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">EUR</div>
              <div className="text-xl font-bold text-green-400">
                €{balances.EUR.toLocaleString()}
              </div>
            </div>
            <div className="p-4 bg-black/50 border border-green-900 rounded">
              <div className="text-sm text-green-600 mb-1">BTC</div>
              <div className="text-xl font-bold text-green-400">
                ₿{balances.BTC.toFixed(8)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Withdrawal Form */}
      <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-green-400 mb-4 flex items-center gap-2">
          <Send className="w-5 h-5" />
          NEW WITHDRAWAL
        </h3>

        <div className="space-y-4">
          {/* Method Selection */}
          <div className="flex gap-4">
            <button
              onClick={() =>
                setWithdrawalForm({ ...withdrawalForm, method: "crypto" })
              }
              className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                withdrawalForm.method === "crypto"
                  ? "border-green-400 bg-green-950/20 text-green-400"
                  : "border-gray-700 bg-black/50 text-gray-400 hover:border-green-700"
              }`}
            >
              <Wallet className="w-6 h-6 mx-auto mb-2" />
              <div className="font-semibold">CRYPTO</div>
            </button>
            <button
              onClick={() =>
                setWithdrawalForm({ ...withdrawalForm, method: "wire" })
              }
              className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                withdrawalForm.method === "wire"
                  ? "border-green-400 bg-green-950/20 text-green-400"
                  : "border-gray-700 bg-black/50 text-gray-400 hover:border-green-700"
              }`}
            >
              <Building className="w-6 h-6 mx-auto mb-2" />
              <div className="font-semibold">WIRE TRANSFER</div>
            </button>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Amount */}
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                AMOUNT
              </label>
              <input
                type="number"
                value={withdrawalForm.amount || ""}
                onChange={(e) =>
                  setWithdrawalForm({
                    ...withdrawalForm,
                    amount: parseFloat(e.target.value) || 0,
                  })
                }
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
                placeholder="0.00"
              />
            </div>

            {/* Currency */}
            <div>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                CURRENCY
              </label>
              <select
                value={withdrawalForm.currency}
                onChange={(e) =>
                  setWithdrawalForm({
                    ...withdrawalForm,
                    currency: e.target.value,
                  })
                }
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
              >
                <option value="USDC">USDC</option>
                <option value="EUR">EUR</option>
                <option value="BTC">BTC</option>
              </select>
            </div>

            {/* Network (for crypto) */}
            {withdrawalForm.method === "crypto" && (
              <div>
                <label className="block text-sm font-semibold text-green-400 mb-2">
                  NETWORK
                </label>
                <select
                  value={withdrawalForm.network}
                  onChange={(e) =>
                    setWithdrawalForm({
                      ...withdrawalForm,
                      network: e.target.value,
                    })
                  }
                  className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
                >
                  <option value="base">Base</option>
                  <option value="polygon">Polygon</option>
                  <option value="arbitrum">Arbitrum</option>
                  <option value="optimism">Optimism</option>
                </select>
              </div>
            )}

            {/* Destination */}
            <div className={withdrawalForm.method === "crypto" ? "" : "md:col-span-2"}>
              <label className="block text-sm font-semibold text-green-400 mb-2">
                {withdrawalForm.method === "crypto"
                  ? "WALLET ADDRESS"
                  : "BANK ACCOUNT ID"}
              </label>
              <input
                type="text"
                value={withdrawalForm.destination}
                onChange={(e) =>
                  setWithdrawalForm({
                    ...withdrawalForm,
                    destination: e.target.value,
                  })
                }
                className="w-full bg-black border border-green-700 rounded px-4 py-2 text-green-400 focus:outline-none focus:border-green-400"
                placeholder={
                  withdrawalForm.method === "crypto"
                    ? "0x..."
                    : "admin_bank_usd"
                }
              />
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleWithdraw}
            disabled={withdrawMut.isPending}
            className="w-full py-3 bg-green-900 hover:bg-green-800 border-2 border-green-400 rounded font-semibold text-green-400 transition-colors disabled:opacity-50"
          >
            {withdrawMut.isPending ? "PROCESSING..." : "WITHDRAW FUNDS"}
          </button>

          {/* Success/Error */}
          {withdrawMut.isSuccess && (
            <div className="p-3 bg-green-900/20 border border-green-800 rounded text-green-400 text-sm">
              ✓ Withdrawal successful!
            </div>
          )}
          {withdrawMut.isError && (
            <div className="p-3 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm">
              ✗ Withdrawal failed. Please try again.
            </div>
          )}
        </div>
      </div>

      {/* Saved Payment Methods */}
      {methods && (
        <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-green-400">
              SAVED PAYMENT METHODS
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddBank(true)}
                className="flex items-center gap-2 px-3 py-2 bg-green-900 hover:bg-green-800 border border-green-400 rounded text-sm transition-colors"
              >
                <Plus className="w-4 h-4" />
                ADD BANK
              </button>
              <button
                onClick={() => setShowAddWallet(true)}
                className="flex items-center gap-2 px-3 py-2 bg-green-900 hover:bg-green-800 border border-green-400 rounded text-sm transition-colors"
              >
                <Plus className="w-4 h-4" />
                ADD WALLET
              </button>
            </div>
          </div>

          {/* Bank Accounts */}
          {methods.bank_accounts.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-green-600 mb-2">
                BANK ACCOUNTS
              </h4>
              <div className="space-y-2">
                {methods.bank_accounts.map((bank) => (
                  <div
                    key={bank.account_id}
                    className="p-3 bg-black/50 border border-green-900 rounded"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-green-400 font-semibold">
                          {bank.account_name}
                        </div>
                        <div className="text-sm text-green-600">
                          {bank.bank_name} • {bank.currency} • Account{" "}
                          {bank.account_number}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Crypto Wallets */}
          {methods.crypto_wallets.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-green-600 mb-2">
                CRYPTO WALLETS
              </h4>
              <div className="space-y-2">
                {methods.crypto_wallets.map((wallet) => (
                  <div
                    key={wallet.wallet_id}
                    className="p-3 bg-black/50 border border-green-900 rounded"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-green-400 font-semibold">
                          {wallet.label}
                        </div>
                        <div className="text-sm text-green-600">
                          {wallet.network} • {wallet.currency} •{" "}
                          {wallet.address}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
