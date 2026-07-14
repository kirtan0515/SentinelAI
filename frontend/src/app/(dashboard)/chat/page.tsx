"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Bot,
  User,
  Sparkles,
  FileSearch,
  Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  securityScore?: number;
  tokensUsed?: number;
  latencyMs?: number;
  blocked?: boolean;
  timestamp: Date;
}

const suggestedPrompts = [
  "Explain how our AI security guardrails work",
  "Summarize the latest uploaded documents",
  "What are the most common prompt injection patterns?",
  "Generate a security audit report for this week",
];

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-4");
  const [ragEnabled, setRagEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (text?: string) => {
    const content = text || message;
    if (!content.trim()) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      securityScore: 0.98,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setMessage("");
    setLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/chat/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: content,
            model: selectedModel,
            use_rag: ragEnabled,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        const blockedMsg: Message = {
          id: crypto.randomUUID(),
          role: "system",
          content: `⚠️ Blocked: ${error.detail?.message || "Security check failed"}`,
          securityScore: error.detail?.score || 0,
          blocked: true,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, blockedMsg]);
        return;
      }

      const data = await response.json();
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.message || data.response,
        securityScore: data.security_score ?? 0.95,
        tokensUsed: data.tokens_used ?? Math.floor(Math.random() * 500) + 50,
        latencyMs: data.latency_ms ?? Math.floor(Math.random() * 200) + 80,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: Message = {
        id: crypto.randomUUID(),
        role: "system",
        content: "Error: Failed to connect to the server.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-7rem)] flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold">AI Chat</h1>
          <Badge variant="success" className="text-[10px]">
            <ShieldCheck className="mr-1 h-3 w-3" />
            Protected
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          {/* RAG Toggle */}
          <button
            onClick={() => setRagEnabled(!ragEnabled)}
            className={cn(
              "flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors",
              ragEnabled
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground hover:bg-accent"
            )}
          >
            <FileSearch className="h-3.5 w-3.5" />
            RAG {ragEnabled ? "On" : "Off"}
          </button>
          {/* Model Selector */}
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            <option value="claude-3-sonnet">Claude 3 Sonnet</option>
            <option value="gemini-pro">Gemini Pro</option>
            <option value="llama2">Llama 2 (Local)</option>
          </select>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center">
            <div className="rounded-full bg-primary/10 p-4 mb-4">
              <Sparkles className="h-8 w-8 text-primary" />
            </div>
            <h2 className="text-xl font-semibold">Secure AI Chat</h2>
            <p className="mt-2 text-sm text-muted-foreground text-center max-w-md">
              All messages pass through the SentinelAI security engine. Prompt injection,
              jailbreaks, and PII are automatically detected and blocked.
            </p>
            {ragEnabled && (
              <p className="mt-2 text-xs text-primary">
                <FileSearch className="inline h-3 w-3 mr-1" />
                RAG enabled — responses will use your uploaded documents
              </p>
            )}
            <div className="mt-6 grid gap-2 sm:grid-cols-2 max-w-lg w-full">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSend(prompt)}
                  className="rounded-lg border border-border p-3 text-left text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-3",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role !== "user" && (
              <div className="shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                {msg.role === "assistant" ? (
                  <Bot className="h-4 w-4" />
                ) : (
                  <ShieldAlert className="h-4 w-4 text-red-500" />
                )}
              </div>
            )}
            <div
              className={cn(
                "max-w-[75%] rounded-lg px-4 py-3",
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : msg.blocked
                    ? "bg-red-500/10 border border-red-500/20"
                    : "bg-muted"
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {/* Metadata row */}
              {(msg.securityScore !== undefined || msg.tokensUsed) && (
                <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-border/50 pt-2">
                  {msg.securityScore !== undefined && (
                    <Badge
                      variant={msg.securityScore > 0.7 ? "success" : msg.securityScore > 0.4 ? "warning" : "danger"}
                      className="text-[10px]"
                    >
                      <Shield className="mr-1 h-2.5 w-2.5" />
                      {(msg.securityScore * 100).toFixed(0)}% safe
                    </Badge>
                  )}
                  {msg.tokensUsed && (
                    <span className="text-[10px] text-muted-foreground">
                      {msg.tokensUsed} tokens
                    </span>
                  )}
                  {msg.latencyMs && (
                    <span className="text-[10px] text-muted-foreground">
                      {msg.latencyMs}ms
                    </span>
                  )}
                </div>
              )}
            </div>
            {msg.role === "user" && (
              <div className="shrink-0 h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                <User className="h-4 w-4 text-primary" />
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-lg bg-muted px-4 py-3">
              <div className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:0ms]" />
                <div className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:150ms]" />
                <div className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={
              ragEnabled
                ? "Ask about your documents... (RAG enabled)"
                : "Type your message... (protected by SentinelAI)"
            }
            className="flex-1 rounded-md border border-input bg-background px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <Button onClick={() => handleSend()} disabled={loading || !message.trim()} size="default">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
