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
import { useWebSocket } from "@/hooks/useWebSocket";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { useSpeechSynthesis } from "@/hooks/useSpeechSynthesis";
import { voiceOutputService } from '@/services/VoiceOutputService';
import { DEFAULT_SPEECH_SETTINGS, VoiceState } from "@/types/speech";

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
  
  // Voice States
  const [speechSettings, setSpeechSettings] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('speechSettings');
      if (saved) {
        try {
          return { ...DEFAULT_SPEECH_SETTINGS, ...JSON.parse(saved) };
        } catch (e) {}
      }
    }
    return DEFAULT_SPEECH_SETTINGS;
  });

  useEffect(() => {
    localStorage.setItem('speechSettings', JSON.stringify(speechSettings));
  }, [speechSettings]);

  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [voiceTranscript, setVoiceTranscript] = useState('');
  
  // Refs for WS callback
  const voiceStateRef = useRef(voiceState);
  useEffect(() => { voiceStateRef.current = voiceState; }, [voiceState]);
  const speechSettingsRef = useRef(speechSettings);
  useEffect(() => { speechSettingsRef.current = speechSettings; }, [speechSettings]);

  const [lastSpokenMessageId, setLastSpokenMessageId] = useState<string | null>(null);

  const { voices, isSpeaking, speak, stopSpeaking } = useSpeechSynthesis();

  const inputRef = useRef<InputAreaRef>(null);

  const avgResponseTime = responseTimes.length > 0 
    ? responseTimes[responseTimes.length - 1] / 1000 
    : 0;

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
  }, []);

  const speakRef = useRef(speak);
  useEffect(() => { speakRef.current = speak; }, [speak]);

  // WebSocket Connection
  const handleWsMessage = useCallback((data: any) => {
    if (data.type === 'step_start') {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'bot') {
            const currentTrace = last.trace || { steps: [] };
            const newSteps = [...(currentTrace.steps || []), { step_name: data.step, status: 'running', start_time: data.start_time }];
            return [...prev.slice(0, -1), { ...last, trace: { ...currentTrace, steps: newSteps } }];
        }
        return prev;
      });
    } 
    else if (data.type === 'step_end') {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'bot') {
            const currentTrace = last.trace || { steps: [] };
            const steps = [...(currentTrace.steps || [])];
            const stepIdx = steps.findIndex(s => s.step_name === data.step && s.status === 'running');
            if (stepIdx >= 0) {
              steps[stepIdx] = { 
                ...steps[stepIdx], 
                status: data.status, 
                duration: data.duration, 
                decision: data.decision,
                metadata: data.metadata || steps[stepIdx].metadata
              };
            }
            return [...prev.slice(0, -1), { ...last, trace: { ...currentTrace, steps } }];
        }
        return prev;
      });
    }
    else if (data.type === 'stream') {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'bot') {
            return [...prev.slice(0, -1), { ...last, content: last.content + data.chunk }];
        }
        return prev;
      });
    }
    else if (data.type === 'error') {
        console.error("WS Pipeline Error:", data.error);
        setBotState('idle');
    }
    else if (data.type === 'done') {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'bot') {
            const hasVoice = last.trace?.steps?.some((s: any) => s.step_name === 'SpeechRecognition');
            const newSteps = [...(data.trace?.steps || [])];
            
            if (hasVoice) {
               newSteps.unshift(last.trace.steps[0]); // Add speech recognition to front
               newSteps.push({
                 step_name: 'VoiceOutputStep',
                 status: 'success',
                 duration: 50,
                 metadata: {
                   voiceEnabled: true,
                   autoSpeak: speechSettings.autoSpeak,
                   voiceName: speechSettings.voiceURI || 'Default System Voice',
                   characters: (data.response || '').length,
                   speechStatus: 'Spoken'
                 }
               });
            }

            return [...prev.slice(0, -1), { 
              ...last, 
              intent: data.intent, 
              components: data.components, 
              actions: data.actions, 
              trace: { ...last.trace, ...data.trace, steps: newSteps, totalBackendTimeMs: data.trace?.totalBackendTimeMs },
              content: data.response || last.content 
            }];
        }
        return prev;
      });
      setBotState('idle');
      setResponseTimes(prev => [...prev, data.trace?.totalBackendTimeMs || 0]);
      
      if (data.actions) {
        data.actions.forEach((a: any) => {
          if (a.type === 'UPDATE_MEMORY') MemoryService.updateMemory(a.payload);
        });
      }
      
      if (voiceStateRef.current === 'waiting_response') {
        console.log("AI Response Received");
        if (data.response) {
          speakRef.current(
            data.response, 
            speechSettingsRef.current,
            () => setVoiceState('speaking'),
            () => setVoiceState('idle'),
            () => setVoiceState('idle')
          );
        } else {
          setVoiceState('idle');
        }
      } else if (speechSettingsRef.current.autoSpeak && data.response) {
        // If text-only input but Auto Speak is globally enabled
        speakRef.current(
          data.response,
          speechSettingsRef.current,
          () => setVoiceState('speaking'),
          () => setVoiceState('idle'),
          () => setVoiceState('idle')
        );
      }
    }
  }, []);

  const [wsUrl, setWsUrl] = useState("");
  const [backendUrl, setBackendUrl] = useState("");

  useEffect(() => {
    let api = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
    if (typeof window !== "undefined") {
      if (!api) {
        api = `http://${window.location.hostname}:8001`;
      } else if (api.includes("localhost") || api.includes("127.0.0.1")) {
        // If the env var says localhost but we are accessing via a network IP, rewrite it
        api = api.replace("localhost", window.location.hostname).replace("127.0.0.1", window.location.hostname);
      }
    }
    setBackendUrl(api);
    
    let ws = process.env.NEXT_PUBLIC_WS_URL || "";
    if (typeof window !== "undefined") {
      if (!ws && api) {
        ws = api.replace("http://", "ws://").replace("https://", "wss://") + "/ws/chat";
      } else if (ws && (ws.includes("localhost") || ws.includes("127.0.0.1"))) {
        ws = ws.replace("localhost", window.location.hostname).replace("127.0.0.1", window.location.hostname);
      }
    }
    setWsUrl(ws);
  }, []);

  const { sendMessage: sendWsMessage } = useWebSocket(
    wsUrl,
    handleWsMessage,
    setBackendStatus
  );

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
    return backendStatus === 'online';
  };

  const focusInput = useCallback(() => {
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, []);

  const handleClearChat = useCallback(async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
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

  const handleVoiceError = useCallback((error: string) => {
    showToast(error);
    setVoiceState('idle');
    setVoiceTranscript('');
  }, [showToast]);

  const { isListening, startListening, stopListening, cancelListening } = useSpeechRecognition(
    speechSettings.language,
    {
      onStateChange: (state) => setVoiceState(state),
      onTranscript: (transcript) => setVoiceTranscript(transcript),
      onEnd: (transcript) => {
        if (transcript && transcript.trim().length > 1) {
          console.log("Transcript Submitted");
          setVoiceState('sending');
          voiceStateRef.current = 'waiting_response'; // Update ref synchronously for fast WS responses
          sendMessageRef.current(transcript, {}, true); // true for isVoice
          setVoiceState('waiting_response');
          setVoiceTranscript('');
        } else {
          setVoiceState('idle');
          setVoiceTranscript('');
        }
      },
      onError: handleVoiceError
    }
  );

  const toggleVoice = useCallback(() => {
    // Unlock the speech synthesis engine on user gesture to prevent browser blocking
    voiceOutputService.unlock();
    
    if (voiceState === 'idle') {
      setVoiceState('listening');
      startListening();
    } else if (voiceState === 'listening' || voiceState === 'recognizing') {
      stopListening(); // This triggers final result, which sends the message
    } else if (voiceState === 'speaking') {
      stopSpeaking();
      setVoiceState('idle');
    }
  }, [voiceState, startListening, stopListening, stopSpeaking]);

  const cancelVoice = useCallback(() => {
    cancelListening();
    setVoiceState('idle');
    setVoiceTranscript('');
  }, [cancelListening]);

  const sendMessage = useCallback(async (textToSend: string, metadata: any = {}, isVoice: boolean = false) => {
    if (!textToSend) return;
    if (botState !== 'idle') return;

    const userMessage: MessageProps = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
      timestamp: Date.now(),
      status: "sent"
    };
    
    const botMsgId = Date.now().toString() + "-bot";
    const botMessage: MessageProps = {
      id: botMsgId,
      role: "bot",
      content: "",
      timestamp: Date.now(),
      format: "markdown",
      trace: isVoice ? {
        steps: [
          {
            step_name: 'SpeechRecognition',
            status: 'success',
            duration: 800, // mock duration
            metadata: {
              transcript: textToSend,
              language: speechSettings.language,
              confidence: '95%'
            }
          }
        ]
      } : undefined
    };

    setMessages((prev) => [...prev, userMessage, botMessage]);
    setInput("");
    setBotState('thinking');
    focusInput();

    try {
      setTimeout(() => {
        setMessages((prev) => 
          prev.map(m => m.id === userMessage.id ? { ...m, status: "delivered" } : m)
        );
      }, 0);

      const isConnected = await ensureBackend();
      if (!isConnected) {
        throw new Error("WebSocket disconnected.");
      }

      sendWsMessage({ 
        message: textToSend,
        session_id: sessionId,
        conversation_id: conversationId,
        metadata: { ...metadata, memory: MemoryService.loadMemory() }
      });

      setTimeout(() => {
        setMessages((prev) => 
          prev.map(m => m.id === userMessage.id ? { ...m, status: "read" } : m)
        );
      }, 200);

    } catch (error) {
      console.error(error);
      setTimeout(() => {
        const errorMessage: MessageProps = {
          id: Date.now().toString(),
          role: "bot",
          content: "Oops! Something went wrong connecting to the backend via WebSocket. Please check if your server is running.",
          intent: "fallback",
          timestamp: Date.now()
        };
        setMessages((prev) => [...prev.filter(m => m.id !== botMsgId), errorMessage]);
        setBotState('idle');
        setBackendStatus('offline');
        showToast("Unable to reach backend.");
        focusInput();
        
        if (voiceStateRef.current === 'waiting_response') {
          if (speechSettingsRef.current.autoSpeak) {
             speakRef.current(
               "Sorry, I couldn't process your request.", 
               speechSettingsRef.current,
               () => setVoiceState('speaking'),
               () => setVoiceState('idle'),
               () => setVoiceState('idle')
             );
          } else {
             setVoiceState('idle');
          }
        }
      }, 0);
    }
  }, [botState, focusInput, showToast, sessionId, conversationId]);

  // Use a ref to always access the latest sendMessage without triggering hook re-renders
  const sendMessageRef = useRef(sendMessage);
  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);

  const sendActionMessage = useCallback(async (actionType: string, payload: any) => {
    if (botState !== 'idle') return;
    
    if (actionType === 'send_message' && payload.text) {
      return sendMessage(payload.text);
    }

    const textToSend = payload.action || 'Action Executed';
    return sendMessage(textToSend, { action: payload.action, data: payload.data });
  }, [botState, sendMessage]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    sendMessage(suggestion);
  }, [sendMessage]);



  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ctrl+M to toggle mic
      if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        toggleVoice();
      }
      if (e.key === 'Escape' && (voiceState === 'listening' || voiceState === 'speaking')) {
        cancelVoice();
        stopSpeaking();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [toggleVoice, cancelVoice, stopSpeaking, voiceState]);

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
      <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 lg:bottom-10 lg:right-10 z-[100] group cursor-pointer" onClick={() => { console.log("Pill clicked. Current state:", isChatOpen); setIsChatOpen(!isChatOpen); }}>
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
              onSpeak={(text) => {
                speakRef.current(
                  text, 
                  speechSettingsRef.current, 
                  () => setVoiceState('speaking'), 
                  () => setVoiceState('idle'), 
                  () => setVoiceState('idle')
                );
              }}
            />
            
            <InputArea 
              ref={inputRef}
              input={input} 
              setInput={setInput} 
              handleSend={handleSend} 
              isLoading={botState !== 'idle'} 
              onSuggestionClick={handleSuggestionClick}
              voiceState={voiceState}
              onVoiceToggle={toggleVoice}
              onVoiceCancel={cancelVoice}
              voiceTranscript={voiceTranscript}
              speechSettings={speechSettings}
              setSpeechSettings={setSpeechSettings}
              voices={voices}
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

