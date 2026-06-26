"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import DashboardLayout from "@/components/layout/dashboard-layout";
import MedicalKnowledgeGraph from "@/components/chat/medical-knowledge-graph";
import { Answer } from "@/components/chat/answer";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { Send, Loader2, PanelRight, PanelRightClose } from "lucide-react";

interface GraphData {
  nodes: Array<{ id: string; label: string; group: string }>;
  links: Array<{ source: string; target: string; label: string }>;
}

interface Citation {
  id: number;
  text: string;
  metadata: Record<string, any>;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  graph_data?: GraphData | null;
  citations?: Citation[];
}

export default function ChatPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const { toast } = useToast();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionTitle, setSessionTitle] = useState("Chat");
  const [showGraph, setShowGraph] = useState(true);
  const [currentGraphData, setCurrentGraphData] = useState<GraphData | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load existing session messages on mount
  useEffect(() => {
    const loadSession = async () => {
      try {
        const session = await api.get(`/api/v1/chat/${sessionId}`);
        setSessionTitle(session.title || "Chat");
        const msgs: Message[] = (session.messages || []).map((m: any) => ({
          id: String(m.id),
          role: m.role as "user" | "assistant",
          content: m.content,
          graph_data: m.graph_data,
          citations: m.citations || [],
        }));
        setMessages(msgs);
        
        // Set graph data from last assistant message
        const lastAssistant = [...msgs].reverse().find((m) => m.role === "assistant" && m.graph_data);
        if (lastAssistant?.graph_data) setCurrentGraphData(lastAssistant.graph_data);
      } catch (err) {
        toast({ title: "Error", description: "Failed to load chat session", variant: "destructive" });
      }
    };
    loadSession();
  }, [sessionId, toast]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  };

  const sendMessage = useCallback(async () => {
    const query = input.trim();
    if (!query || isLoading) return;

    // Optimistically add user message
    const userMsg: Message = { id: `user-${Date.now()}`, role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsLoading(true);

    try {
      const response = await api.post(`/api/v1/chat/${sessionId}/messages`, {
        message: query,
      });

      const assistantMsg: Message = {
        id: response.id || `asst-${Date.now()}`,
        role: "assistant",
        content: response.content,
        graph_data: response.graph_data ?? null,
        citations: response.citations || [],
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Update knowledge graph if data came back
      if (response.graph_data?.nodes?.length > 0) {
        setCurrentGraphData(response.graph_data);
      }
    } catch (err) {
      const errMsg =
        err instanceof ApiError ? err.message : "Failed to get a response. Please try again.";
      toast({ title: "Error", description: errMsg, variant: "destructive" });
      // Remove the optimistic user message on failure
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      setInput(query); // restore input
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, sessionId, toast]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <DashboardLayout>
      <div className="flex h-[calc(100vh-8rem)] gap-4 overflow-hidden">
        {/* ── Chat Panel ── */}
        <div className="flex flex-col flex-1 min-w-0 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 flex-shrink-0">
            <div>
              <h1 className="font-bold text-slate-900 text-lg truncate max-w-xs">{sessionTitle}</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                {messages.length} message{messages.length !== 1 ? "s" : ""}
              </p>
            </div>
            <button
              onClick={() => setShowGraph((v) => !v)}
              className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
              title={showGraph ? "Hide Knowledge Graph" : "Show Knowledge Graph"}
            >
              {showGraph ? <PanelRightClose className="h-5 w-5" /> : <PanelRight className="h-5 w-5" />}
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center h-full text-center py-16">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                  <Send className="h-7 w-7 text-primary" />
                </div>
                <h2 className="text-xl font-semibold text-slate-800">Ready to assist</h2>
                <p className="text-slate-500 mt-2 max-w-sm text-sm">
                  Ask any medical question. Your documents are searched privately — no data shared between doctors.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "user" ? (
                  <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm text-primary-foreground shadow-sm">
                    {message.content}
                  </div>
                ) : (
                  <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-slate-50 border border-slate-200 px-4 py-3 text-sm text-slate-800 shadow-sm">
                    {/* Fixed: Props aligned to match Answer.tsx parameters */}
                    <Answer 
                      markdown={message.content} 
                      citations={message.citations || []} 
                    />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex items-center gap-2 text-slate-500 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Searching your knowledge base...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-slate-200 px-4 py-4 flex-shrink-0">
            <div className="flex items-end gap-3 bg-slate-50 rounded-xl border border-slate-200 px-4 py-3 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask a medical question… (Enter to send, Shift+Enter for new line)"
                rows={1}
                disabled={isLoading}
                className="flex-1 resize-none bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none disabled:opacity-50 min-h-[24px] max-h-[160px]"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="flex-shrink-0 rounded-lg bg-primary p-2 text-primary-foreground disabled:opacity-40 hover:bg-primary/90 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-2 text-center">
              All queries are isolated to your private knowledge base.
            </p>
          </div>
        </div>

        {/* ── Knowledge Graph Panel ── */}
        {showGraph && (
          <div className="hidden lg:flex w-96 flex-shrink-0 rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <MedicalKnowledgeGraph graphData={currentGraphData} />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}