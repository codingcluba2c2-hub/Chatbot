"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Bug } from "lucide-react";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatBody } from "@/components/chat/ChatBody";
import { InputArea, InputAreaRef } from "@/components/chat/InputArea";
import { MessageProps } from "@/components/chat/ChatMessage";
import { RefreshDialog } from "@/components/chat/RefreshDialog";
import { Toast } from "@/components/chat/Toast";
import { DeveloperSidebar } from "@/components/dev/DeveloperSidebar";

export default function Home() {
  const [sessionId] = useState(() => typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString());
  const [conversationId] = useState(() => typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString());
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [input, setInput] = useState("");
  const [botState, setBotState] = useState<'idle' | 'thinking' | 'typing'>('idle');
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline'>('online');
  const [isRefreshDialogOpen, setIsRefreshDialogOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [responseTimes, setResponseTimes] = useState<number[]>([]);
  
  // Developer Mode States
  const [isDevModeOpen, setIsDevModeOpen] = useState(false);
  const [selectedTraceMessageId, setSelectedTraceMessageId] = useState<string | null>(null);
  
  const inputRef = useRef<InputAreaRef>(null);

  const avgResponseTime = responseTimes.length > 0 
    ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length / 1000 
    : 0;

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ctrl+L to clear chat
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        setIsRefreshDialogOpen(true);
      }
      // / to focus input (if not already focused)
      if (e.key === '/' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault();
        focusInput();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Connection Monitoring
  useEffect(() => {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    
    const checkConnection = async () => {
      try {
        // Just pinging root or any simple endpoint if it existed, 
        // since we only have /chat we might just assume it's online unless a fetch fails.
        // Or we can do a simple GET to backendUrl (if it has a health route).
        // For now, let's do a simple GET and ignore 404/405 as long as we get a response.
        await fetch(`${backendUrl}/`, { method: "GET" }).catch(() => {});
        if (backendStatus === 'offline') setBackendStatus('online');
      } catch (err) {
        if (backendStatus === 'online') {
          setBackendStatus('offline');
          showToast("Unable to reach backend.");
        }
      }
    };
    
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, [backendStatus, showToast]);

  // Focus management wrapper
  const focusInput = useCallback(() => {
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, []);

  const handleClearChat = useCallback(async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${backendUrl}/api/session/clear?session_id=${sessionId}`, { method: 'DELETE' });
    } catch (e) {
      console.error("Failed to clear backend session:", e);
    }
    setMessages([]);
    setBotState('idle');
    setResponseTimes([]);
    setIsRefreshDialogOpen(false);
    showToast("Conversation cleared successfully.");
    focusInput();
  }, [focusInput, showToast, sessionId]);

  const sendMessage = useCallback(async (textToSend: string) => {
    if (!textToSend) {
      console.warn("sendMessage blocked: empty textToSend");
      return;
    }
    if (botState !== 'idle') {
      console.warn("sendMessage blocked: botState is not idle, it is", botState);
      return;
    }
    console.log("Sending message:", textToSend);

    const userMessage: MessageProps = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
      timestamp: Date.now(),
      status: "sent"
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setBotState('thinking');
    focusInput();

    const startTime = Date.now();

    try {
      // Simulate delivered status (removed delay for instant response)
      setTimeout(() => {
        setMessages((prev) => 
          prev.map(m => m.id === userMessage.id ? { ...m, status: "delivered" } : m)
        );
      }, 0);

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: textToSend,
          session_id: sessionId,
          conversation_id: conversationId
        }),
      });
      
      const endTime = Date.now();
      setResponseTimes(prev => [...prev, endTime - startTime]);

      // Switch to typing state (removed delay for instant response)
      setBotState('typing');
      const typingDelay = 0;

      // Simulate read status
      setMessages((prev) => 
        prev.map(m => m.id === userMessage.id ? { ...m, status: "read" } : m)
      );

      if (!response.ok) {
        throw new Error("Failed to connect to the server");
      }

      const data = await response.json();
      
      setTimeout(() => {
        const botMessage: MessageProps = {
          id: Date.now().toString(),
          role: "bot",
          content: data.response || "Sorry, I didn't understand that.",
          intent: data.intent,
          timestamp: Date.now(),
          components: data.components,
          actions: data.actions,
          trace: data.trace
        };
        
        setMessages((prev) => [...prev, botMessage]);
        setBotState('idle');
        focusInput();
      }, typingDelay);

    } catch (error) {
      console.error(error);
      setTimeout(() => {
        const errorMessage: MessageProps = {
          id: Date.now().toString(),
          role: "bot",
          content: "Oops! Something went wrong connecting to the backend. Please check if your Python server is running.",
          intent: "fallback",
          timestamp: Date.now()
        };
        setMessages((prev) => [...prev, errorMessage]);
        setBotState('idle');
        setBackendStatus('offline');
        showToast("Unable to reach backend.");
        focusInput();
      }, 0);
    }
  }, [botState, focusInput, showToast, sessionId, conversationId]);

  const sendActionMessage = useCallback(async (actionType: string, payload: any) => {
    if (botState !== 'idle') return;
    
    // For quick replies, just send the text normally
    if (actionType === 'send_message' && payload.text) {
      return sendMessage(payload.text);
    }

    const textToSend = payload.action || 'Action Executed';
    
    const userMessage: MessageProps = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
      timestamp: Date.now(),
      status: "sent"
    };

    setMessages((prev) => [...prev, userMessage]);
    setBotState('thinking');
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: textToSend,
          session_id: sessionId,
          conversation_id: conversationId,
          metadata: { action: payload.action, data: payload.data }
        }),
      });
      
      setBotState('typing');

      if (!response.ok) throw new Error("Failed to connect to the server");
      const data = await response.json();
      
      const botMessage: MessageProps = {
        id: Date.now().toString(),
        role: "bot",
        content: data.response || "Sorry, I didn't understand that.",
        intent: data.intent,
        timestamp: Date.now(),
        components: data.components,
        actions: data.actions,
        trace: data.trace
      };
      
      setMessages((prev) => [...prev, botMessage]);
      setBotState('idle');
      focusInput();

    } catch (error) {
      console.error(error);
      setBotState('idle');
      showToast("Unable to reach backend for action.");
    }
  }, [botState, sendMessage, sessionId, conversationId, focusInput, showToast]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    console.log("handleSuggestionClick triggered with:", suggestion);
    sendMessage(suggestion);
  }, [sendMessage]);

  const handleSend = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const currentInput = input.trim();
    if (currentInput) {
      sendMessage(currentInput);
    }
  }, [input, sendMessage]);

  return (
    <main className="min-h-screen flex items-center justify-center p-0 sm:p-4 bg-gradient-to-br from-blue-50/50 via-slate-50 to-blue-50/80 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 bg-[length:200%_200%] animate-gradient-xy">
      {/* Abstract Background pattern */}
      <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] dark:opacity-[0.01] pointer-events-none mix-blend-multiply dark:mix-blend-screen"></div>
      
      <div className="w-full max-w-2xl h-[100dvh] sm:h-[calc(100vh-32px)] sm:max-h-[800px] flex flex-col bg-[var(--color-cards)]/80 dark:bg-[var(--color-cards)]/60 backdrop-blur-xl sm:rounded-2xl border-0 sm:border border-[var(--color-border)] shadow-[0_8px_40px_rgb(0,0,0,0.06)] dark:shadow-[0_8px_40px_rgb(0,0,0,0.2)] relative overflow-hidden z-10 sm:ring-1 ring-[var(--color-border)]/50 transition-colors duration-300">
        
        <ChatHeader 
          status={backendStatus} 
          model="Python API" 
          latency={Math.round(avgResponseTime * 1000) || 0.01} 
          onRefreshClick={() => setIsRefreshDialogOpen(true)}
        />
        
        <ChatBody 
          messages={messages} 
          botState={botState} 
          onSuggestionClick={handleSuggestionClick}
          onReplayMessage={(id) => {
            setSelectedTraceMessageId(id);
            setIsDevModeOpen(true);
          }}
          onAction={sendActionMessage}
        />
        
        <InputArea 
          ref={inputRef}
          input={input} 
          setInput={setInput} 
          handleSend={handleSend} 
          isLoading={botState !== 'idle'} 
          onSuggestionClick={handleSuggestionClick}
        />
        
        <RefreshDialog 
          isOpen={isRefreshDialogOpen} 
          onConfirm={handleClearChat} 
          onCancel={() => {
            setIsRefreshDialogOpen(false);
            focusInput();
          }} 
        />
        
        <Toast 
          message={toastMessage} 
          isVisible={!!toastMessage} 
          onClose={() => setToastMessage("")} 
        />
      </div>

      {/* Floating Developer Mode Button */}
      <button 
        onClick={() => setIsDevModeOpen(true)}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-slate-900 text-slate-300 hover:text-white p-3 py-4 rounded-l-xl shadow-lg border border-r-0 border-slate-700/50 flex flex-col items-center gap-2 transition-all hover:bg-slate-800 z-40 group"
      >
        <Bug size={18} className="text-emerald-500 group-hover:animate-pulse" />
        <span className="text-[10px] uppercase font-bold tracking-widest" style={{ writingMode: 'vertical-rl' }}>Dev Mode</span>
      </button>

      {/* Developer Sidebar */}
      <DeveloperSidebar 
        isOpen={isDevModeOpen}
        onClose={() => setIsDevModeOpen(false)}
        messages={messages}
        selectedMessageId={selectedTraceMessageId}
      />
    </main>
  );
}
