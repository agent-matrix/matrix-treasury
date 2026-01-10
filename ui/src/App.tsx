import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  AlertTriangle,
  DollarSign,
  Activity,
  Power,
  Lock,
  Send,
  Cpu,
  Zap,
  TrendingDown,
  MessageSquare,
  LayoutDashboard,
  Settings as SettingsIcon,
  Bot,
  Key,
  CreditCard,
  Check,
  X,
  Save
} from 'lucide-react';

// --- TYPES ---
type TransactionType = 'EXPENSE' | 'INCOME' | 'SYSTEM';
type Status = 'APPROVED' | 'DENIED' | 'PENDING';
type Tab = 'MONITOR' | 'ADMIN' | 'CHAT';

interface LogEntry {
  id: number;
  time: string;
  agent: string;
  action: string;
  cost: number;
  type: TransactionType;
  status: Status;
  reason?: string;
}

interface ChatMessage {
  id: number;
  sender: 'USER' | 'SYSTEM' | string;
  text: string;
  timestamp: string;
}

interface AppSettings {
  llmProvider: 'OpenAI' | 'Anthropic' | 'Local';
  apiKey: string;
  adminWallet: string;
  organizationId: string;
}

// --- MOCK DATA GENERATORS ---
const AGENTS = ['Agent-Alpha', 'Agent-Beta', 'Agent-007', 'Agent-Coder', 'Agent-Analyst'];
const CONTACTS = [
  { id: 'cfo', name: 'Treasury (CFO)', role: 'Financial Governance', status: 'online' },
  { id: 'alpha', name: 'Agent-Alpha', role: 'Field Ops', status: 'busy' },
  { id: 'beta', name: 'Agent-Beta', role: 'Data Analyst', status: 'idle' },
  { id: 'sys', name: 'Matrix System', role: 'Infrastructure', status: 'online' },
];

const ACTIONS = [
  { name: 'GPT-4 Query', cost: 0.05, type: 'EXPENSE' },
  { name: 'Akash Server Rent', cost: 1.50, type: 'EXPENSE' },
  { name: 'Tool: Web Search', cost: 0.02, type: 'EXPENSE' },
  { name: 'Human Payment (Job)', cost: 50.00, type: 'INCOME' },
  { name: 'DeFi Yield Farm', cost: 5.20, type: 'INCOME' },
  { name: 'System Maintenance', cost: 0.10, type: 'SYSTEM' },
];

export default function MissionControl() {
  // --- STATE ---
  const [activeTab, setActiveTab] = useState<Tab>('MONITOR');
  const [balance, setBalance] = useState<number>(5432.50);
  const [autopilot, setAutopilot] = useState<boolean>(true);
  const [panicMode, setPanicMode] = useState<boolean>(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [withdrawAmount, setWithdrawAmount] = useState<string>('');
  const [showSettings, setShowSettings] = useState<boolean>(false);

  // Settings State
  const [settings, setSettings] = useState<AppSettings>({
    llmProvider: 'OpenAI',
    apiKey: 'sk-........................',
    adminWallet: '0x71C...9A23',
    organizationId: 'ORG-8821'
  });

  // Pending Decisions Queue
  const [pendingQueue, setPendingQueue] = useState<LogEntry[]>([]);

  // Chat State
  const [activeContact, setActiveContact] = useState(CONTACTS[0]);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<Record<string, ChatMessage[]>>({
    cfo: [{ id: 1, sender: 'Treasury (CFO)', text: 'Greetings, Admin. Financial logic is operating at 99.9% efficiency. How may I assist?', timestamp: '10:00' }]
  });

  // Simulation Refs
  const logIdCounter = useRef(1);

  // --- SIMULATION LOOP ---
  useEffect(() => {
    if (panicMode) return; // Stop simulation if panic mode is on

    const interval = setInterval(() => {
      generateRandomEvent();
    }, 3000); // Slower event generation for better readability

    return () => clearInterval(interval);
  }, [panicMode, autopilot, balance]);

  // --- HELPERS ---
  const generateRandomEvent = () => {
    const randomAgent = AGENTS[Math.floor(Math.random() * AGENTS.length)];
    const randomAction = ACTIONS[Math.floor(Math.random() * ACTIONS.length)];
    const isExpense = randomAction.type === 'EXPENSE' || randomAction.type === 'SYSTEM';

    // DECISION LOGIC (The "Brain")
    let status: Status = 'APPROVED';
    let reason = 'Within budget';

    if (isExpense) {
      if (!autopilot) {
        status = 'PENDING'; // Human in loop
        reason = 'Awaiting Admin Review';
      } else if (balance < 100 && randomAction.cost > 10) {
        status = 'DENIED';
        reason = 'Insolvency Risk';
      } else if (Math.random() > 0.9) {
        status = 'DENIED';
        reason = 'Low ROI predicted by CFO';
      }
    }

    // Only deduct immediate balance if approved automatically
    if (status === 'APPROVED') {
      setBalance(prev => isExpense ? prev - randomAction.cost : prev + randomAction.cost);
    }

    const newLog: LogEntry = {
      id: logIdCounter.current++,
      time: new Date().toLocaleTimeString('en-US', { hour12: false }),
      agent: randomAgent,
      action: randomAction.name,
      cost: randomAction.cost,
      type: randomAction.type as TransactionType,
      status,
      reason: status === 'DENIED' || status === 'PENDING' ? reason : undefined
    };

    setLogs(prev => [newLog, ...prev].slice(0, 50));

    if (status === 'PENDING') {
      setPendingQueue(prev => [newLog, ...prev]);
    }
  };

  const handleManualDecision = (id: number, decision: 'APPROVE' | 'DENY') => {
    // Update the pending queue
    const item = pendingQueue.find(i => i.id === id);
    if (!item) return;

    setPendingQueue(prev => prev.filter(i => i.id !== id));

    // Update the main log
    setLogs(prev => prev.map(log => {
      if (log.id === id) {
        return {
          ...log,
          status: decision === 'APPROVE' ? 'APPROVED' : 'DENIED',
          reason: decision === 'APPROVE' ? 'Manual Approval' : 'Manual Rejection'
        };
      }
      return log;
    }));

    // Update balance if approved
    if (decision === 'APPROVE') {
      const isExpense = item.type === 'EXPENSE' || item.type === 'SYSTEM';
      setBalance(prev => isExpense ? prev - item.cost : prev + item.cost);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now(),
      sender: 'USER',
      text: chatInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const contactId = activeContact.id;

    setChatHistory(prev => ({
      ...prev,
      [contactId]: [...(prev[contactId] || []), newMessage]
    }));
    setChatInput('');

    // Simulate Reply
    setTimeout(() => {
      let replyText = "I acknowledge your request.";
      if (contactId === 'cfo') {
        if (chatInput.toLowerCase().includes('status')) replyText = `Current solvency is stable. Runway estimated at ${Math.floor(balance/125)} days.`;
        else if (chatInput.toLowerCase().includes('risk')) replyText = "Risk levels are nominal. No anomalous spending patterns detected.";
        else replyText = "I am optimizing the budget allocation. Do you have a specific financial override command?";
      } else if (contactId === 'alpha') {
        replyText = "Currently engaged in data extraction. I can prioritize your task if you authorize extra compute.";
      }

      const botReply: ChatMessage = {
        id: Date.now() + 1,
        sender: activeContact.name,
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setChatHistory(prev => ({
        ...prev,
        [contactId]: [...(prev[contactId] || []), botReply]
      }));
    }, 1000);
  };

  // --- HANDLERS ---
  const handlePanic = () => {
    if (panicMode) {
      setPanicMode(false);
      setLogs(prev => [{
        id: logIdCounter.current++,
        time: new Date().toLocaleTimeString(),
        agent: 'SYSTEM',
        action: 'EMERGENCY OVERRIDE',
        cost: 0,
        type: 'SYSTEM',
        status: 'APPROVED',
        reason: 'System Rebooted by Admin'
      }, ...prev]);
    } else {
      if (window.confirm("⚠️ CRITICAL WARNING: This will freeze all Agent Wallets. Continue?")) {
        setPanicMode(true);
      }
    }
  };

  const handleWithdraw = () => {
    const amount = parseFloat(withdrawAmount);
    if (!amount || amount <= 0) return;
    if (amount > balance) {
      alert("Insufficient funds!");
      return;
    }
    setBalance(prev => prev - amount);
    setLogs(prev => [{
      id: logIdCounter.current++,
      time: new Date().toLocaleTimeString(),
      agent: 'ADMIN',
      action: `Transfer to ${settings.adminWallet}`,
      cost: amount,
      type: 'EXPENSE',
      status: 'APPROVED',
      reason: 'Manual Override'
    }, ...prev]);
    setWithdrawAmount('');
  };

  // --- RENDER ---
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono flex flex-col selection:bg-green-500 selection:text-black relative overflow-hidden">

      {/* --- SETTINGS MODAL --- */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl shadow-2xl">
            <div className="p-6 border-b border-gray-800 flex justify-between items-center">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <SettingsIcon className="w-5 h-5 text-blue-400" /> Enterprise Configuration
              </h2>
              <button onClick={() => setShowSettings(false)} className="text-gray-500 hover:text-white"><X className="w-6 h-6" /></button>
            </div>

            <div className="p-6 space-y-8">
              {/* LLM Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                  <Bot className="w-4 h-4" /> Cognitive Core Provider
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-xs text-gray-500">Provider</label>
                    <select
                      value={settings.llmProvider}
                      onChange={(e) => setSettings({...settings, llmProvider: e.target.value as any})}
                      className="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white focus:border-blue-500 focus:outline-none"
                    >
                      <option value="OpenAI">OpenAI (GPT-4 Turbo)</option>
                      <option value="Anthropic">Anthropic (Claude 3.5)</option>
                      <option value="Local">Local (Ollama/Llama3)</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs text-gray-500">Organization ID</label>
                    <input
                      type="text"
                      value={settings.organizationId}
                      onChange={(e) => setSettings({...settings, organizationId: e.target.value})}
                      className="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-gray-500">API Credentials</label>
                  <div className="relative">
                    <Key className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
                    <input
                      type="password"
                      value={settings.apiKey}
                      onChange={(e) => setSettings({...settings, apiKey: e.target.value})}
                      className="w-full bg-black border border-gray-700 rounded-lg py-2.5 pl-10 pr-4 text-white focus:border-blue-500 focus:outline-none font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Financial Section */}
              <div className="space-y-4 pt-4 border-t border-gray-800">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                  <CreditCard className="w-4 h-4" /> Liquidity Settlements
                </h3>
                <div className="space-y-2">
                  <label className="text-xs text-gray-500">Admin Wallet Address (EVM)</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={settings.adminWallet}
                      onChange={(e) => setSettings({...settings, adminWallet: e.target.value})}
                      className="w-full bg-black border border-gray-700 rounded-lg p-2.5 text-white focus:border-green-500 focus:outline-none font-mono text-sm"
                    />
                    <button className="bg-gray-800 border border-gray-700 text-gray-300 px-4 rounded-lg text-xs hover:bg-gray-700">Verify</button>
                  </div>
                  <p className="text-[10px] text-gray-500">This address will be used as the destination for all surplus liquidity withdrawals.</p>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-800 bg-gray-900/50 flex justify-end gap-3 rounded-b-xl">
              <button onClick={() => setShowSettings(false)} className="px-4 py-2 text-gray-400 hover:text-white text-sm">Cancel</button>
              <button onClick={() => { alert('Configuration Saved'); setShowSettings(false); }} className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-bold flex items-center gap-2">
                <Save className="w-4 h-4" /> Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- TOP BAR --- */}
      <header className={`bg-gray-900 px-6 py-4 border-b border-gray-800 shadow-xl z-20 sticky top-0 ${panicMode ? 'border-red-900/50' : ''}`}>
        <div className="flex flex-col md:flex-row justify-between items-center max-w-7xl mx-auto w-full">
          <div className="flex items-center gap-4 mb-4 md:mb-0 w-full md:w-auto">
            <div className={`p-2 rounded-lg ${panicMode ? 'bg-red-900/50 animate-pulse' : 'bg-green-900/20'}`}>
              {panicMode ? <AlertTriangle className="w-6 h-6 text-red-500" /> : <Shield className="w-6 h-6 text-green-400" />}
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                MATRIX MISSION CONTROL
              </h1>
              <p className="text-xs text-gray-400 flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${panicMode ? 'bg-red-500' : 'bg-green-500 animate-pulse'}`}></span>
                {panicMode ? "SYSTEM FROZEN" : "SYSTEM ONLINE"}
              </p>
            </div>
          </div>

          {/* GLOBAL VITALS (Always Visible) */}
          <div className="flex gap-6 text-right w-full md:w-auto justify-end">
            <div>
              <p className="text-gray-500 text-[10px] uppercase tracking-wider">Vault Balance</p>
              <p className={`text-xl font-bold flex items-center justify-end gap-1 ${balance < 1000 ? 'text-red-400' : 'text-white'}`}>
                <DollarSign className="w-4 h-4 text-gray-600" />
                {balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="hidden sm:block">
              <p className="text-gray-500 text-[10px] uppercase tracking-wider">Runway</p>
              <p className="text-xl font-bold text-blue-400 flex items-center justify-end gap-1">
                <Activity className="w-4 h-4" />
                {Math.floor(balance / 125)} Days
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* --- NAVIGATION TABS --- */}
      <div className="bg-gray-900/50 border-b border-gray-800 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex gap-1 px-4">
          <button
            onClick={() => setActiveTab('MONITOR')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'MONITOR' ? 'border-green-500 text-green-400 bg-green-500/5' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" /> MONITOR
          </button>
          <button
            onClick={() => setActiveTab('ADMIN')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'ADMIN' ? 'border-blue-500 text-blue-400 bg-blue-500/5' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <SettingsIcon className="w-4 h-4" /> ADMIN OPS
          </button>
          <button
            onClick={() => setActiveTab('CHAT')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-bold border-b-2 transition-colors ${
              activeTab === 'CHAT' ? 'border-purple-500 text-purple-400 bg-purple-500/5' : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <MessageSquare className="w-4 h-4" /> NEURAL LINK
          </button>
        </div>
      </div>

      {/* --- MAIN CONTENT AREA --- */}
      <main className="flex-grow p-4 md:p-6 max-w-7xl mx-auto w-full pb-20">

        {/* === VIEW 1: MONITOR === */}
        {activeTab === 'MONITOR' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Live Feed */}
            <div className="lg:col-span-2 flex flex-col gap-6">

              {/* PENDING ACTIONS (Manual Mode) */}
              {pendingQueue.length > 0 && (
                <div className="bg-yellow-950/20 border border-yellow-900/50 rounded-xl p-4 animate-in fade-in slide-in-from-top-4">
                  <h3 className="text-sm font-bold text-yellow-500 mb-3 flex items-center gap-2">
                    <Lock className="w-4 h-4" /> PENDING APPROVALS ({pendingQueue.length})
                  </h3>
                  <div className="space-y-2">
                    {pendingQueue.map(item => (
                      <div key={item.id} className="bg-gray-900 border border-gray-800 p-3 rounded-lg flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <span className="text-xs font-mono text-gray-500">{item.time}</span>
                          <div>
                            <div className="text-sm font-bold text-white">{item.action}</div>
                            <div className="text-xs text-gray-400">{item.agent} • ${item.cost.toFixed(2)}</div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleManualDecision(item.id, 'APPROVE')}
                            className="bg-green-900/30 hover:bg-green-900/50 text-green-400 border border-green-900 rounded p-1.5 transition-colors"
                            title="Approve"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleManualDecision(item.id, 'DENY')}
                            className="bg-red-900/30 hover:bg-red-900/50 text-red-400 border border-red-900 rounded p-1.5 transition-colors"
                            title="Deny"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Transaction Stream */}
              <div className="bg-gray-900 rounded-xl border border-gray-800 flex flex-col shadow-xl overflow-hidden h-[600px]">
                <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/80">
                  <h2 className="text-sm font-bold flex items-center gap-2 text-gray-200">
                    <Activity className="w-4 h-4 text-purple-400" />
                    LIVE TRANSACTION STREAM
                  </h2>
                  <div className="flex items-center gap-2 text-[10px] text-gray-500 uppercase">
                    {autopilot ? (
                      <span className="flex items-center gap-1 text-green-400"><Zap className="w-3 h-3" /> Auto</span>
                    ) : (
                      <span className="flex items-center gap-1 text-yellow-400"><Lock className="w-3 h-3" /> Manual</span>
                    )}
                  </div>
                </div>

                <div className="flex-grow overflow-y-auto p-2 space-y-1 scrollbar-thin scrollbar-thumb-gray-700">
                  {logs.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600">
                      <Activity className="w-8 h-8 opacity-20 mb-2" />
                      <p className="text-sm">Initializing connection...</p>
                    </div>
                  )}
                  {logs.map((log) => (
                    <div key={log.id} className={`flex items-center justify-between text-xs p-3 rounded border transition-all ${
                      log.status === 'DENIED' ? 'bg-red-950/10 border-red-900/20 text-red-100' :
                      log.status === 'PENDING' ? 'bg-yellow-950/10 border-yellow-900/20 text-yellow-100' :
                      log.type === 'INCOME' ? 'bg-green-950/10 border-green-900/20 text-green-100' :
                      'bg-gray-800/20 border-gray-800 text-gray-300'
                    }`}>
                      <div className="flex items-center gap-3">
                        <span className="text-gray-500 font-mono w-14">{log.time}</span>
                        <div className="w-24 font-bold truncate">{log.agent}</div>
                        <div className="text-gray-400 w-40 truncate">{log.action}</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className={`font-mono ${log.type === 'INCOME' ? 'text-green-400' : 'text-gray-400'}`}>
                          {log.type === 'INCOME' ? '+' : '-'}${log.cost.toFixed(2)}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold w-20 text-center ${
                          log.status === 'APPROVED' ? 'bg-green-900/30 text-green-400' :
                          log.status === 'PENDING' ? 'bg-yellow-900/30 text-yellow-400 animate-pulse' :
                          'bg-red-900/30 text-red-400'
                        }`}>{log.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Vitals Panel */}
            <div className="flex flex-col gap-4">
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 shadow-lg">
                 <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Network Health</h3>
                 <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">Akash Nodes</span>
                        <span className="text-green-400">12 Active</span>
                      </div>
                      <div className="w-full bg-gray-800 h-1 rounded-full"><div className="bg-green-500 w-[80%] h-full"></div></div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">Compute Load</span>
                        <span className="text-blue-400">64%</span>
                      </div>
                      <div className="w-full bg-gray-800 h-1 rounded-full"><div className="bg-blue-500 w-[64%] h-full"></div></div>
                    </div>
                 </div>
              </div>

              <div className="bg-blue-900/10 rounded-xl border border-blue-900/30 p-5">
                 <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-2">CFO Insight</h3>
                 <p className="text-sm text-blue-200 italic">
                   "Spending is within nominal parameters. 94% of agents are profitable this hour."
                 </p>
              </div>
            </div>
          </div>
        )}

        {/* === VIEW 2: ADMIN OPS === */}
        {activeTab === 'ADMIN' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

            {/* Control 1: Autopilot */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 shadow-lg relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Cpu className="w-24 h-24" />
              </div>
              <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-blue-400" /> Autonomy Level
              </h2>
              <p className="text-sm text-gray-400 mb-6">
                Control the CFO's permission to authorize transactions without human intervention.
              </p>
              <div className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                autopilot ? 'bg-blue-950/20 border-blue-900/30' : 'bg-yellow-950/20 border-yellow-900/30'
              }`}>
                <div>
                  <p className={`font-bold ${autopilot ? 'text-blue-400' : 'text-yellow-400'}`}>
                    {autopilot ? "CFO Autopilot ON" : "Manual Mode"}
                  </p>
                  <p className="text-[10px] text-gray-500">
                    {autopilot ? "AI Approving <$10" : "Approval Required for All"}
                  </p>
                </div>
                <button
                  onClick={() => !panicMode && setAutopilot(!autopilot)}
                  disabled={panicMode}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    autopilot ? 'bg-blue-600' : 'bg-gray-700'
                  }`}
                >
                  <span className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${
                    autopilot ? 'translate-x-6' : 'translate-x-0'
                  }`} />
                </button>
              </div>
            </div>

            {/* Control 2: Withdraw */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 shadow-lg relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <TrendingDown className="w-24 h-24" />
              </div>
              <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-green-400" /> Liquidity Extraction
              </h2>
              <p className="text-sm text-gray-400 mb-6">
                Transfer surplus USDC from the Treasury Vault to the Developer Wallet.
              </p>
              <div className="flex gap-2">
                <div className="relative flex-grow">
                  <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                  <input
                    type="number"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    placeholder="0.00"
                    disabled={panicMode}
                    className="w-full bg-black border border-gray-700 rounded-lg py-2 pl-7 pr-4 text-white focus:border-green-500 focus:outline-none"
                  />
                </div>
                <button
                  onClick={handleWithdraw}
                  disabled={panicMode}
                  className="bg-green-600 hover:bg-green-500 text-black font-bold px-4 rounded-lg flex items-center gap-2 disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[10px] text-gray-500 mt-2 text-right">Target: {settings.adminWallet.substring(0,6)}...</p>
            </div>

            {/* Control 3: Kill Switch */}
            <div className="bg-red-950/10 rounded-xl border border-red-900/30 p-6 shadow-lg relative overflow-hidden md:col-span-2 lg:col-span-1">
              <h2 className="text-lg font-bold text-red-500 mb-2 flex items-center gap-2">
                <Power className="w-5 h-5" /> EMERGENCY STOP
              </h2>
              <p className="text-sm text-red-200/60 mb-6">
                Immediately revokes all wallet keys, cancels pending transactions, and stops server renewals.
              </p>
              <button
                onClick={handlePanic}
                className={`w-full font-bold py-4 rounded-xl flex items-center justify-center gap-2 transition-all border shadow-lg ${
                  panicMode
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-red-900/20 border-red-900 text-red-500 hover:bg-red-900 hover:text-white'
                }`}
              >
                {panicMode ? <>REBOOT SYSTEM</> : <>KILL SWITCH</>}
              </button>
            </div>

             {/* Log Dump */}
             <div className="md:col-span-2 lg:col-span-3 bg-gray-900 rounded-xl border border-gray-800 p-4 font-mono text-[10px] text-gray-500 h-32 overflow-hidden relative">
               <div className="absolute top-2 right-2 text-xs font-bold text-gray-600">SYSTEM KERNEL LOG</div>
               {logs.slice(0,6).map((l, i) => (
                 <div key={i} className="opacity-50">
                   [{l.time}] KERNEL_OP: {l.agent.toUpperCase()} EXECUTE {l.action} -- {l.status}
                 </div>
               ))}
               <div className="absolute bottom-0 left-0 w-full h-12 bg-gradient-to-t from-gray-900 to-transparent"></div>
             </div>

          </div>
        )}

        {/* === VIEW 3: NEURAL LINK (CHAT) === */}
        {activeTab === 'CHAT' && (
          <div className="flex flex-col md:flex-row h-[600px] bg-gray-900 rounded-xl border border-gray-800 shadow-2xl overflow-hidden">

            {/* Contact List */}
            <div className="w-full md:w-64 border-r border-gray-800 bg-gray-900/50 flex flex-col">
              <div className="p-4 border-b border-gray-800 font-bold text-sm text-gray-400">ACTIVE LINKS</div>
              <div className="flex-grow overflow-y-auto">
                {CONTACTS.map(contact => (
                  <button
                    key={contact.id}
                    onClick={() => setActiveContact(contact)}
                    className={`w-full text-left p-4 hover:bg-gray-800 transition-colors border-l-2 ${
                      activeContact.id === contact.id ? 'bg-gray-800 border-green-500' : 'border-transparent'
                    }`}
                  >
                    <div className="font-bold text-sm text-gray-200">{contact.name}</div>
                    <div className="text-xs text-gray-500">{contact.role}</div>
                    <div className="mt-2 flex items-center gap-1.5">
                       <span className={`w-2 h-2 rounded-full ${
                         contact.status === 'online' ? 'bg-green-500' :
                         contact.status === 'busy' ? 'bg-yellow-500' : 'bg-gray-500'
                       }`}></span>
                       <span className="text-[10px] uppercase text-gray-600">{contact.status}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Area */}
            <div className="flex-grow flex flex-col bg-gray-950">
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-800 flex items-center gap-3">
                 <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center">
                   <Bot className="w-6 h-6 text-blue-400" />
                 </div>
                 <div>
                   <h3 className="font-bold text-white">{activeContact.name}</h3>
                   <p className="text-xs text-gray-500">Secure Encrypted Channel • Matrix-ID: {activeContact.id.toUpperCase()}</p>
                 </div>
              </div>

              {/* Messages */}
              <div className="flex-grow overflow-y-auto p-4 space-y-4">
                {(chatHistory[activeContact.id] || []).map((msg) => (
                  <div key={msg.id} className={`flex ${msg.sender === 'USER' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[70%] rounded-xl p-3 text-sm ${
                      msg.sender === 'USER' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-800 text-gray-200 rounded-bl-none'
                    }`}>
                      <div className="text-[10px] opacity-50 mb-1 flex justify-between gap-4">
                        <span>{msg.sender === 'USER' ? 'ADMIN' : msg.sender.toUpperCase()}</span>
                        <span>{msg.timestamp}</span>
                      </div>
                      {msg.text}
                    </div>
                  </div>
                ))}
                {(chatHistory[activeContact.id] || []).length === 0 && (
                   <div className="h-full flex flex-col items-center justify-center text-gray-600 opacity-50">
                     <MessageSquare className="w-12 h-12 mb-2" />
                     <p>Channel Open. No history.</p>
                   </div>
                )}
              </div>

              {/* Input */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-800 bg-gray-900">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder={`Message ${activeContact.name}...`}
                    className="flex-grow bg-black border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-green-500 focus:outline-none"
                  />
                  <button type="submit" className="bg-green-600 hover:bg-green-500 text-black font-bold p-2 rounded-lg">
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>

      {/* --- FIXED BOTTOM LEFT SETTINGS --- */}
      <button
        onClick={() => setShowSettings(true)}
        className="fixed bottom-6 left-6 p-3 bg-gray-900 hover:bg-gray-800 border border-gray-700 rounded-full shadow-2xl text-gray-400 hover:text-blue-400 transition-all z-30 group"
      >
        <SettingsIcon className="w-6 h-6 group-hover:rotate-90 transition-transform" />
        <span className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-gray-800 text-xs px-2 py-1 rounded border border-gray-700 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
          System Config
        </span>
      </button>

    </div>
  );
}
