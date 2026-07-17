"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Bug, ArrowRight, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatBody } from "@/components/chat/ChatBody";
import { InputArea, InputAreaRef } from "@/components/chat/InputArea";
import { MessageProps } from "@/components/chat/ChatMessage";
import { RefreshDialog } from "@/components/chat/RefreshDialog";
import { Toast } from "@/components/chat/Toast";
import { DeveloperSidebar } from "@/components/dev/DeveloperSidebar";
import { MemoryService } from "@/services/MemoryService";

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [messages, setMessages] = useState<MessageProps[]>([]);

  useEffect(() => {
    setSessionId(typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString());
    setConversationId(typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString());
  }, []);
  const [input, setInput] = useState("");
  const [botState, setBotState] = useState<'idle' | 'thinking' | 'typing'>('idle');
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline'>('online');
  const [isRefreshDialogOpen, setIsRefreshDialogOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [responseTimes, setResponseTimes] = useState<number[]>([]);
  
  // Enterprise UI States
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);

  // Developer Mode States
  const [isDevModeOpen, setIsDevModeOpen] = useState(false);
  const [selectedTraceMessageId, setSelectedTraceMessageId] = useState<string | null>(null);
  
  const inputRef = useRef<InputAreaRef>(null);

  const avgResponseTime = responseTimes.length > 0 
    ? responseTimes[responseTimes.length - 1] / 1000 
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
        if (!isChatOpen) {
          setIsChatOpen(true);
        }
        e.preventDefault();
        focusInput();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [isChatOpen]);

  const ensureBackend = async () => {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    try {
      await fetch(`${backendUrl}/`, { method: "GET" }).catch(() => {});
      if (backendStatus === 'offline') setBackendStatus('online');
      return true;
    } catch (err) {
      setBackendStatus('offline');
      showToast("Backend Starting... Retrying in 5 seconds.");
      return new Promise((resolve) => setTimeout(async () => {
        try {
          await fetch(`${backendUrl}/`, { method: "GET" }).catch(() => {});
          if (backendStatus === 'offline') setBackendStatus('online');
          resolve(true);
        } catch(e) {
          resolve(false);
        }
      }, 5000));
    }
  };

  const focusInput = useCallback(() => {
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, []);

  const handleClearChat = useCallback(async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
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
    if (!textToSend) return;
    if (botState !== 'idle') return;

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
      setTimeout(() => {
        setMessages((prev) => 
          prev.map(m => m.id === userMessage.id ? { ...m, status: "delivered" } : m)
        );
      }, 0);

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const backendReady = await ensureBackend();
      if (!backendReady) throw new Error("Backend not available after waiting");

      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: textToSend,
          session_id: sessionId,
          conversation_id: conversationId,
          metadata: { memory: MemoryService.loadMemory() }
        }),
      });
      
      const endTime = Date.now();
      setResponseTimes(prev => [...prev, endTime - startTime]);

      setBotState('typing');

      setMessages((prev) => 
        prev.map(m => m.id === userMessage.id ? { ...m, status: "read" } : m)
      );

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'no text');
        throw new Error(`Server returned ${response.status} ${response.statusText}: ${errorText}`);
      }

      const data = await response.json();
      
      if (data.actions) {
        data.actions.forEach((action: any) => {
          if (action.type === 'UPDATE_MEMORY') {
            MemoryService.updateMemory(action.payload);
          }
        });
      }
      
      setTimeout(() => {
        const botMessage: MessageProps = {
          id: Date.now().toString(),
          role: "bot",
          content: data.response || "",
          intent: data.intent,
          timestamp: Date.now(),
          components: data.components,
          actions: data.actions,
          trace: data.trace
        };
        
        setMessages((prev) => [...prev, botMessage]);
        setBotState('idle');
        focusInput();
      }, 0);

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
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const backendReady = await ensureBackend();
      if (!backendReady) throw new Error("Backend not available after waiting");

      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: textToSend,
          session_id: sessionId,
          conversation_id: conversationId,
          metadata: { action: payload.action, data: payload.data, memory: MemoryService.loadMemory() }
        }),
      });
      
      setBotState('typing');

      if (!response.ok) throw new Error("Failed to connect to the server");
      const data = await response.json();
      
      if (data.actions) {
        data.actions.forEach((action: any) => {
          if (action.type === 'UPDATE_MEMORY') {
            MemoryService.updateMemory(action.payload);
          }
        });
      }
      
      const botMessage: MessageProps = {
        id: Date.now().toString(),
        role: "bot",
        content: data.response || "",
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
    <main className="min-h-screen w-full relative bg-black overflow-hidden font-sans text-white selection:bg-blue-500/30 flex flex-col">
      
      {/* Background Globe Image */}
      <div className="absolute top-0 right-[-10%] w-[70%] h-full z-0 opacity-80 pointer-events-none mix-blend-screen overflow-hidden">
        <img 
          src="/globe.png" 
          alt="Globe Network" 
          className="w-full h-full object-cover object-left" 
        />
        {/* Shadow overlay to fade left edge of image smoothly into background */}
        <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-transparent z-10" />
      </div>

      {/* Top Header */}
      <header className="w-full flex items-center justify-between px-6 lg:px-12 py-6 relative z-20 border-b border-white/10 bg-black/50 backdrop-blur-sm">
        <div className="text-2xl font-bold tracking-tight">Mobiloitte</div>
        
        <nav className="hidden lg:flex items-center gap-8 font-semibold text-[15px]">
          <a href="#" className="flex items-center gap-1 hover:text-gray-300">What we do <ChevronDown size={14} /></a>
          <a href="#" className="flex items-center gap-1 hover:text-gray-300">What we think <ChevronDown size={14} /></a>
          <a href="#" className="flex items-center gap-1 hover:text-gray-300">Who we are <ChevronDown size={14} /></a>
          <a href="#" className="hover:text-gray-300">Careers</a>
        </nav>
        
        <button className="hidden md:block px-6 py-2 rounded-full border border-white font-semibold hover:bg-white hover:text-black transition-colors">
          Contact Us
        </button>
      </header>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col justify-center px-6 lg:px-12 xl:px-24 relative z-10 w-full lg:w-[60%]">
        
        {/* Heading */}
        <h1 className="text-4xl md:text-5xl lg:text-[56px] font-bold tracking-tight text-white mb-6 leading-tight">
          RAG Based <br/>
          AI Architectures and Enterprise Integrations
        </h1>
        
        {/* Description */}
        <p className="text-[15px] md:text-[16px] text-white/90 max-w-[650px] mb-8 leading-relaxed font-medium">
          Mobiloitte builds secure AI systems, custom AI software, generative AI solutions, RAG architectures, 
          AI agents, blockchain platforms, cloud infrastructure, cybersecurity solutions, web applications, AI-powered 
          mobile apps, and automation workflows for enterprise digital transformation. From AI consulting and workflow 
          design to development, integration, deployment, governance, and scale, Mobiloitte helps businesses launch 
          production-ready AI solutions, enterprise software platforms, cloud-native applications, blockchain systems, 
          and intelligent automation workflows.
        </p>
        
        {/* CTAs */}
        <div className="flex flex-wrap items-center gap-4 mb-8">
          <button 
            className="px-6 py-3.5 bg-[#0B66D9] hover:bg-blue-600 text-white rounded-lg font-bold flex items-center gap-2 transition-all text-sm shadow-[0_4px_14px_rgba(11,102,217,0.4)]"
          >
            Book an AI Strategy Session <ArrowRight size={18} />
          </button>
          <button className="px-6 py-3.5 bg-black hover:bg-white/5 text-white rounded-lg font-bold border border-white/30 transition-all text-sm">
            See What We Build
          </button>
        </div>
      </div>
      
      {/* Footer Text */}
      <div className="w-full px-6 lg:px-12 xl:px-24 pb-8 relative z-10 max-w-[85%] lg:max-w-[70%]">
        <p className="text-[13px] md:text-[14px] text-white/80 leading-relaxed font-semibold">
          From AI strategy to generative AI development, RAG chatbot development, LLM integration, AI agent development, enterprise software engineering, mobile app development, cloud, DevOps, cybersecurity, and blockchain deployment.
        </p>
      </div>

      {/* Floating Pill Launcher */}
      <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 lg:bottom-10 lg:right-10 z-40 group cursor-pointer" onClick={() => setIsChatOpen(!isChatOpen)}>
        <div className={`absolute inset-0 bg-blue-500 rounded-full blur-xl transition-all duration-500 ${isChatOpen ? 'opacity-0' : 'opacity-40 group-hover:opacity-60 animate-glow-pulse'}`} />
        
        <div className={`relative h-[56px] flex items-center rounded-full bg-white shadow-2xl transition-all duration-300 transform ${isChatOpen ? 'scale-90 opacity-0 pointer-events-none' : 'scale-100 opacity-100 hover:scale-105'} pr-[4px] pl-5 overflow-hidden`}>
          <span className="text-black font-bold text-[13px] sm:text-[14px] mr-3 whitespace-nowrap">Start your Digital Journey...</span>
          <div className="w-[48px] h-[48px] rounded-full flex items-center justify-center text-white relative">
            {/* Custom M logo mimicking the screenshot */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-blue-700 to-blue-500 shadow-inner" />
            <div className="absolute inset-0 rounded-full border-[3px] border-white/20" />
            <span className="relative z-10 font-bold text-2xl italic tracking-tighter" style={{ fontFamily: 'Georgia, serif' }}>M</span>
          </div>
        </div>
      </div>

      {/* Floating Chat Widget */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 40, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.95 }}
            transition={{ duration: 0.4, type: "spring", bounce: 0.15 }}
            className={cn(
              "fixed bg-white dark:bg-slate-900 premium-shadow border border-white/20 dark:border-slate-800 overflow-hidden flex flex-col z-50 backdrop-blur-2xl transition-all duration-500",
              isChatExpanded 
                ? "inset-0 w-full h-full rounded-none" 
                : "top-1/2 -translate-y-1/2 right-4 sm:right-6 lg:right-10 w-[calc(100vw-32px)] sm:w-[350px] md:w-[380px] xl:w-[420px] h-[85vh] max-h-[750px] rounded-[24px]"
            )}
          >
            <ChatHeader 
              status={backendStatus} 
              model="v2.4.1" 
              latency={Math.round(avgResponseTime * 1000) || 0.01} 
              isExpanded={isChatExpanded}
              onExpandClick={() => setIsChatExpanded(!isChatExpanded)}
              onRefreshClick={() => setIsRefreshDialogOpen(true)}
              onClose={() => setIsChatOpen(false)}
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
          </motion.div>
        )}
      </AnimatePresence>

      {/* Dialogs and Toasts outside the main widget to avoid clipping */}
      <RefreshDialog 
        isOpen={isRefreshDialogOpen} 
        onConfirmClearChat={async () => {
          await handleClearChat();
        }} 
        onConfirmClearBoth={async () => {
          await MemoryService.clearMemory();
          await handleClearChat();
        }}
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

      {/* Floating Developer Mode Button */}
      <div className="fixed left-0 top-1/2 -translate-y-1/2 z-40">
        <button 
          onClick={() => setIsDevModeOpen(true)}
          className="glass-panel text-slate-400 hover:text-white p-2 py-5 rounded-r-xl shadow-[10px_0_30px_rgba(0,0,0,0.2)] flex flex-col items-center gap-3 transition-all hover:bg-white/10 group bg-white/5 border border-white/10"
        >
          <Bug size={16} className="text-blue-400 group-hover:animate-pulse" />
          <span className="text-[10px] uppercase font-bold tracking-widest opacity-80" style={{ writingMode: 'vertical-rl' }}>Dev Mode</span>
        </button>
      </div>

      <DeveloperSidebar 
        isOpen={isDevModeOpen}
        onClose={() => setIsDevModeOpen(false)}
        messages={messages}
        selectedMessageId={selectedTraceMessageId}
      />
    </main>
  );
}

