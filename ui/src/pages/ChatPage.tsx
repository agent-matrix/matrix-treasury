/**
 * ChatPage Component
 * Neural Link - Chat interface with AI CFO
 */

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Bot, User } from "lucide-react";
import { api } from "../api/endpoints";
import type { ChatMessage } from "../types";

export function ChatPage() {
  const qc = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch chat history
  const historyQ = useQuery({
    queryKey: ["chat-history"],
    queryFn: api.getChatHistory,
  });

  // Send message mutation
  const sendMut = useMutation({
    mutationFn: (message: string) => api.sendChatMessage(message),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chat-history"] });
      setInput("");
    },
  });

  const [input, setInput] = useState("");

  const messages = historyQ.data || [];

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMut.mutate(input);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-green-400 mb-2">
          NEURAL LINK
        </h2>
        <p className="text-green-600 text-sm">
          Direct communication channel with AI CFO
        </p>
      </div>

      {/* Chat Container */}
      <div className="bg-gray-900 border border-green-700 rounded-lg flex flex-col h-[600px]">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => {
            const isUser = msg.role === "user";
            const isSystem = msg.role === "system";

            return (
              <div
                key={i}
                className={`flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`
                    flex gap-3 max-w-[80%]
                    ${isUser ? "flex-row-reverse" : "flex-row"}
                  `}
                >
                  {/* Avatar */}
                  <div
                    className={`
                      flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                      ${
                        isUser
                          ? "bg-green-900 border-2 border-green-400"
                          : isSystem
                          ? "bg-blue-900 border-2 border-blue-400"
                          : "bg-purple-900 border-2 border-purple-400"
                      }
                    `}
                  >
                    {isUser ? (
                      <User className="w-5 h-5 text-green-400" />
                    ) : (
                      <Bot className="w-5 h-5 text-purple-400" />
                    )}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`
                      rounded-lg p-4 border
                      ${
                        isUser
                          ? "bg-green-950/20 border-green-700 text-green-400"
                          : isSystem
                          ? "bg-blue-950/20 border-blue-700 text-blue-400"
                          : "bg-purple-950/20 border-purple-700 text-purple-400"
                      }
                    `}
                  >
                    <div className="text-sm opacity-60 mb-1">
                      {isUser ? "YOU" : isSystem ? "SYSTEM" : "AI CFO"}
                    </div>
                    <div className="text-sm whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    <div className="text-xs opacity-40 mt-2">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Loading indicator */}
          {sendMut.isPending && (
            <div className="flex justify-start">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-purple-900 border-2 border-purple-400 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-purple-400" />
                </div>
                <div className="bg-purple-950/20 border border-purple-700 rounded-lg p-4">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <div
                      className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-green-900 p-4">
          <form onSubmit={handleSend} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message to the AI CFO..."
              className="flex-1 bg-black border border-green-700 rounded px-4 py-3 text-green-400 focus:outline-none focus:border-green-400"
              disabled={sendMut.isPending}
            />
            <button
              type="submit"
              disabled={sendMut.isPending || !input.trim()}
              className="px-6 py-3 bg-green-900 hover:bg-green-800 border-2 border-green-400 rounded font-semibold text-green-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              <span>SEND</span>
            </button>
          </form>

          {/* Error display */}
          {sendMut.isError && (
            <div className="mt-3 p-3 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm">
              Failed to send message. Please try again.
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-900 border border-green-700 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-green-400 mb-3">
          QUICK COMMANDS
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <button
            onClick={() => setInput("What is the current treasury status?")}
            className="px-4 py-2 bg-black/50 hover:bg-black border border-green-900 hover:border-green-700 rounded text-sm text-green-600 hover:text-green-400 transition-colors text-left"
          >
            Treasury Status
          </button>
          <button
            onClick={() => setInput("Show me top performing agents")}
            className="px-4 py-2 bg-black/50 hover:bg-black border border-green-900 hover:border-green-700 rounded text-sm text-green-600 hover:text-green-400 transition-colors text-left"
          >
            Top Agents
          </button>
          <button
            onClick={() => setInput("What are the current risks?")}
            className="px-4 py-2 bg-black/50 hover:bg-black border border-green-900 hover:border-green-700 rounded text-sm text-green-600 hover:text-green-400 transition-colors text-left"
          >
            Risk Assessment
          </button>
        </div>
      </div>
    </div>
  );
}
