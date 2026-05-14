"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, FileBarChart, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// 1. Define our strict TypeScript interfaces matching the Python backend
interface Citation {
  chunk_id: string;
  text: string;
  images_base64: string[];
  tables_html: string[];
}

interface Message {
  role: "user" | "ai";
  content: string;
  citations?: Citation[];
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Add user message to UI
    const newMessages: Message[] = [...messages, { role: "user", content: query }];
    setMessages(newMessages);
    setQuery("");
    setIsLoading(true);

    try {
      // 2. Call our FastAPI Backend
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) throw new Error("Failed to fetch from API");

      const data = await response.json();

      // 3. Add AI message and citations to UI
      setMessages([
        ...newMessages,
        {
          role: "ai",
          content: data.answer,
          citations: data.citations,
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages([
        ...newMessages,
        { role: "ai", content: "Sorry, I encountered an error connecting to the knowledge base." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-2 shadow-sm z-10">
        <FileBarChart className="text-blue-600 w-6 h-6" />
        <h1 className="text-xl font-semibold text-slate-800">FinancialMe Enterprise RAG</h1>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 w-full max-w-4xl mx-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
            <Bot className="w-16 h-16 text-slate-300" />
            <p className="text-lg">Ask a question about the financial documents...</p>
          </div>
        ) : (
          <div className="space-y-8">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                
                {/* AI Avatar */}
                {msg.role === "ai" && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`max-w-[85%] rounded-2xl p-5 shadow-sm ${
                    msg.role === "user"
                      ? "bg-slate-800 text-white rounded-tr-none"
                      : "bg-white border border-slate-200 text-slate-800 rounded-tl-none"
                  }`}
                >
                  {/* Markdown Content */}
                  <div className="prose prose-sm max-w-none prose-slate">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>

                  {/* Render Citations (Images and Tables) */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-6 space-y-6 border-t border-slate-100 pt-4">
                      {msg.citations.map((citation, cIdx) => (
                        <div key={cIdx} className="space-y-4">
                          
                          {/* Render HTML Tables from Docling */}
                          {citation.tables_html.map((tableHtml, tIdx) => (
                            <div key={`table-${tIdx}`} className="bg-slate-50 border border-slate-200 rounded-lg p-4 overflow-x-auto text-xs">
                              <div className="text-slate-500 font-semibold mb-2 flex items-center gap-2">
                                <FileBarChart className="w-4 h-4"/> Table Citation
                              </div>
                              {/* Inject the raw HTML extracted by the backend safely */}
                              <div dangerouslySetInnerHTML={{ __html: tableHtml }} />
                            </div>
                          ))}

                          {/* Render Base64 Images */}
                          {citation.images_base64.map((base64, iIdx) => (
                            <div key={`img-${iIdx}`} className="bg-slate-50 border border-slate-200 rounded-lg p-2 overflow-hidden">
                              <div className="text-slate-500 font-semibold mb-2 ml-2 text-xs flex items-center gap-2">
                                <FileBarChart className="w-4 h-4"/> Image Citation
                              </div>
                              <img 
                                src={`data:image/png;base64,${base64}`} 
                                alt={`Citation from document chunk ${citation.chunk_id}`}
                                className="w-full h-auto rounded-md"
                              />
                            </div>
                          ))}

                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* User Avatar */}
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-slate-300 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-5 h-5 text-slate-600" />
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-4 justify-start">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-5 h-5 text-white animate-pulse" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-5 shadow-sm flex items-center gap-3">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  <span className="text-slate-500 text-sm">Synthesizing financial data...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Area */}
      <footer className="bg-white border-t border-slate-200 p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about revenue, margins, or specific charts..."
            className="w-full bg-slate-100 border-none text-slate-800 rounded-full pl-6 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-inner"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute right-2 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:hover:bg-blue-600"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </footer>
    </div>
  );
}