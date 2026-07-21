import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Activity, Server, Clock, Database, Braces, PlayCircle, Network, Layers, GitBranch, Terminal } from 'lucide-react';
import { MessageProps } from '../chat/ChatMessage';
import { PipelineTimeline } from './PipelineTimeline';

interface DeveloperSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  messages: MessageProps[];
  selectedMessageId: string | null;
}

export const DeveloperSidebar: React.FC<DeveloperSidebarProps> = ({ isOpen, onClose, messages, selectedMessageId }) => {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'routing' | 'logs'>('pipeline');

  // Find the selected message trace, or default to the latest bot message
  let selectedMessage = messages.find(m => m.id === selectedMessageId);
  let botMessage = null;
  
  if (selectedMessage) {
    botMessage = selectedMessage.role === 'user' 
      ? messages[messages.indexOf(selectedMessage) + 1] 
      : (selectedMessage.role === 'bot' ? selectedMessage : null);
  } else {
    // If no message is explicitly selected, default to the last bot message
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'bot' && messages[i].trace) {
        botMessage = messages[i];
        selectedMessage = messages[i - 1] || messages[i];
        break;
      }
    }
  }
    
  const trace = botMessage?.trace;

  const tabs = [
    { id: 'pipeline', label: 'Pipeline Graph', icon: GitBranch },
    { id: 'routing', label: 'Agent Routing', icon: Layers },
    { id: 'logs', label: 'System Logs', icon: Terminal }
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="absolute right-0 top-0 bottom-0 w-full sm:w-[520px] bg-slate-900/95 backdrop-blur-xl border-l border-slate-700/50 shadow-2xl z-50 flex flex-col text-slate-200 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-4 border-b border-slate-700/50 bg-slate-900/50">
            <div className="flex flex-col gap-1">
              <h2 className="text-sm font-semibold tracking-wide flex items-center gap-2">
                <Database size={16} className="text-blue-400" />
                Developer Mode
              </h2>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Backend Online</span>
                {trace && <span>Total Latency: {trace.totalBackendTimeMs}ms</span>}
                {trace?.metadata?.gemini_used && trace?.metadata?.llm_latency_ms && (
                  <span className="text-purple-400 font-semibold border-l border-slate-700 pl-3">
                    LLM Time: {trace.metadata.llm_latency_ms}ms
                  </span>
                )}
              </div>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-md transition-colors text-slate-400 hover:text-white">
              <X size={20} />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex px-2 pt-2 border-b border-slate-800 overflow-x-auto custom-scrollbar gap-1 bg-slate-900/40">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id 
                      ? 'border-blue-500 text-blue-400 bg-slate-800/50' 
                      : 'border-transparent text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'
                  }`}
                >
                  <Icon size={14} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-slate-950">
            {!trace ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
                <PlayCircle size={48} className="opacity-20" />
                <p className="text-sm text-center">Select a message or click Replay<br/>to view the execution trace.</p>
              </div>
            ) : (
              <div className="h-full">
                {activeTab === 'pipeline' && <PipelineTimeline trace={trace} mode="graph" />}
                {activeTab === 'logs' && (
                  <div className="font-mono text-[11px] p-3 rounded-md bg-slate-900 border border-slate-800 space-y-1">
                    {trace.steps.map((s:any, idx:number) => (
                      <div key={idx} className="flex gap-2">
                        <span className="text-slate-500">[{new Date(s.start_time * 1000).toISOString().split('T')[1].slice(0,-1)}]</span>
                        <span className={s.status === 'failed' ? 'text-red-400' : 'text-blue-400'}>INFO</span>
                        <span className="text-slate-300">Executing pipeline step: {s.step_name}</span>
                        <span className="text-slate-500">({s.duration}ms)</span>
                      </div>
                    ))}
                  </div>
                )}
                {activeTab === 'routing' && (
                  <div className="font-mono text-xs p-3 rounded-md bg-slate-900 border border-slate-800 space-y-4">
                    <div className="text-slate-400 uppercase tracking-widest text-[10px] mb-2 border-b border-slate-800 pb-2">Enterprise Routing Decision</div>
                    
                    <div className="flex flex-col gap-3">
                      <div>
                        <span className="text-slate-500 block mb-1">User Query:</span>
                        <span className="text-blue-300 font-bold bg-slate-950 p-2 rounded block">{selectedMessage?.content || "N/A"}</span>
                      </div>
                      
                      <div className="text-center text-slate-600">↓</div>
                      
                      <div className="flex justify-between items-center bg-slate-800/50 p-2 rounded border border-slate-700/50">
                        <span className="text-slate-300">Normalize</span>
                        <span className="text-emerald-400 font-bold">✅</span>
                      </div>
                      
                      {trace.metadata?.greeting_detected !== undefined && (
                        <>
                          <div className="text-center text-slate-600">↓</div>
                          <div className="flex flex-col gap-2 bg-slate-800/50 p-3 rounded border border-slate-700/50">
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300 font-semibold text-xs">Greeting Detected:</span>
                              <span className={trace.metadata?.greeting_detected ? "text-emerald-400 font-bold" : "text-slate-500 font-bold"}>
                                {trace.metadata?.greeting_detected ? "true" : "false"}
                              </span>
                            </div>
                            
                            {trace.metadata?.greeting_detected && (
                              <>
                                <div className="flex justify-between items-center mt-1">
                                  <span className="text-slate-400 text-[11px]">Greeting Type:</span>
                                  <span className="text-amber-300 bg-slate-900 px-1.5 py-0.5 rounded text-[11px]">{trace.metadata.greeting_type}</span>
                                </div>
                                <div className="flex justify-between items-center mt-1">
                                  <span className="text-slate-400 text-[11px]">Corrected:</span>
                                  <span className="text-blue-300 bg-slate-900 px-1.5 py-0.5 rounded text-[11px]">{trace.metadata.corrected_greeting}</span>
                                </div>
                                <div className="flex justify-between items-center mt-1">
                                  <span className="text-slate-400 text-[11px]">Server Time:</span>
                                  <span className="text-slate-300 font-mono text-[11px]">{trace.metadata.detected_time} ({trace.metadata.time_bucket})</span>
                                </div>
                                <div className="flex justify-between items-center mt-1">
                                  <span className="text-slate-400 text-[11px]">Greeting Count:</span>
                                  <span className="text-purple-400 font-bold text-[11px]">{trace.metadata.greeting_count}</span>
                                </div>
                                <div className="flex justify-between items-center mt-1">
                                  <span className="text-slate-400 text-[11px]">Remaining Query:</span>
                                  <span className="text-blue-300 bg-slate-900 px-1.5 py-0.5 rounded text-[11px] truncate max-w-[150px]">"{trace.metadata.remaining_query}"</span>
                                </div>
                                <div className="flex flex-col mt-2 pt-2 border-t border-slate-700/50">
                                  <span className="text-slate-500 text-[10px] uppercase mb-1">Selected Template:</span>
                                  <span className="text-emerald-300 text-[11px] italic">"{trace.metadata.selected_template}"</span>
                                </div>
                                <div className="flex justify-between items-center mt-2">
                                  <span className="text-slate-400 text-[11px]">Execution Time:</span>
                                  <span className="text-slate-300 font-mono text-[11px]">{trace.metadata.execution_time_ms}ms</span>
                                </div>
                                <div className="flex justify-between items-center mt-1 pt-1 border-t border-slate-700/50">
                                  <span className="text-slate-400 text-[11px]">Routing:</span>
                                  <span className="text-purple-400 text-[11px] font-semibold">{trace.metadata.routing}</span>
                                </div>
                              </>
                            )}
                          </div>
                        </>
                      )}
                      
                      {trace.metadata?.memory_intent && (
                        <>
                          <div className="text-center text-slate-600">↓</div>
                          <div className="flex flex-col gap-2 bg-slate-800/50 p-3 rounded border border-slate-700/50">
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300 font-semibold text-xs">Memory Engine:</span>
                              <span className="text-emerald-400 font-bold">{trace.metadata.memory_intent}</span>
                            </div>
                            
                            <div className="flex justify-between items-center mt-1">
                              <span className="text-slate-400 text-[11px]">Detected Field:</span>
                              <span className="text-amber-300 bg-slate-900 px-1.5 py-0.5 rounded text-[11px]">{trace.metadata.detected_field}</span>
                            </div>
                            
                            <div className="flex justify-between items-center mt-1">
                              <span className="text-slate-400 text-[11px]">Previous Value:</span>
                              <span className="text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded text-[11px] truncate max-w-[120px]">
                                {trace.metadata.previous_value || 'null'}
                              </span>
                            </div>
                            
                            {trace.metadata.memory_intent === "UPDATE" && (
                              <div className="flex justify-between items-center mt-1">
                                <span className="text-slate-400 text-[11px]">Updated Value:</span>
                                <span className="text-blue-300 bg-slate-900 px-1.5 py-0.5 rounded text-[11px] truncate max-w-[120px]">
                                  {trace.metadata.updated_value || 'null'}
                                </span>
                              </div>
                            )}
                            
                            {trace.metadata.memory_intent === "LOOKUP" && (
                              <div className="flex justify-between items-center mt-1">
                                <span className="text-slate-400 text-[11px]">Lookup Value:</span>
                                <span className="text-blue-300 bg-slate-900 px-1.5 py-0.5 rounded text-[11px] truncate max-w-[120px]">
                                  {trace.metadata.lookup_value || 'null'}
                                </span>
                              </div>
                            )}

                            <div className="flex justify-between items-center mt-1">
                              <span className="text-slate-400 text-[11px]">Storage:</span>
                              <span className="text-slate-300 font-mono text-[11px]">{trace.metadata.storage}</span>
                            </div>
                            
                            <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-700/50">
                              <span className="text-slate-400 text-[11px]">Execution Time:</span>
                              <span className="text-slate-300 font-mono text-[11px]">{trace.metadata.execution_time_ms}ms</span>
                            </div>
                          </div>
                        </>
                      )}

                      <div className="text-center text-slate-600">↓</div>
                      
                      <div className="flex justify-between items-center bg-slate-800/50 p-2 rounded border border-slate-700/50">
                        <span className="text-slate-300">Spell Corrections:</span>
                        <span className={trace.metadata?.spell_correction?.corrections_count > 0 ? "text-amber-400 font-bold" : "text-emerald-400 font-bold"}>
                          {trace.metadata?.spell_correction?.corrections_count || 0}
                        </span>
                      </div>
                      
                      <div className="text-center text-slate-600">↓</div>
                      
                      <div className="flex justify-between items-center bg-slate-800/50 p-2 rounded border border-slate-700/50">
                        <span className="text-slate-300">Knowledge Search:</span>
                        <span className={trace.metadata?.knowledge_search_decision?.startsWith("REJECTED") ? "text-amber-400 font-bold" : (trace.metadata?.knowledge_search_decision === "EXECUTED" ? "text-emerald-400 font-bold" : "text-slate-500 font-bold")}>
                          {trace.metadata?.knowledge_search_decision || "SKIPPED"}
                        </span>
                      </div>
                      
                      {trace.metadata?.knowledge_search_decision === "EXECUTED" && (
                        <>
                          <div className="text-center text-slate-600">↓</div>
                          <div className="flex flex-col gap-2 bg-slate-800/50 p-3 rounded border border-slate-700/50">
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300 font-semibold text-xs">Top RAG Score:</span>
                              <span className="text-blue-400 font-bold">{trace.metadata.top_score?.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-slate-400 text-[11px]">Retrieval Latency:</span>
                              <span className="text-slate-300 text-[11px] font-mono">{trace.metadata.retrieval_latency_ms}ms</span>
                            </div>
                          </div>
                        </>
                      )}
                      
                      {(trace.metadata?.gemini_used || trace.metadata?.fallback_used) && (
                        <>
                          <div className="text-center text-slate-600">↓</div>
                          <div className="flex flex-col gap-2 bg-slate-800/50 p-3 rounded border border-slate-700/50">
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300 font-semibold text-xs">LLM Engine:</span>
                              <span className={trace.metadata?.gemini_used ? "text-purple-400 font-bold" : "text-amber-400 font-bold"}>
                                {trace.metadata?.gemini_used ? "Groq Llama 3.1" : "Deterministic Fallback"}
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-slate-400 text-[11px]">Generation Latency:</span>
                              <span className="text-slate-300 text-[11px] font-mono">{trace.metadata.llm_latency_ms}ms</span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-slate-400 text-[11px]">Final Output Length:</span>
                              <span className="text-slate-300 text-[11px] font-mono">{botMessage?.content?.length || 0} chars</span>
                            </div>
                          </div>
                        </>
                      )}
                      
                      <div className="text-center text-slate-600">↓</div>
                      
                      <div className="bg-slate-950 p-3 rounded border border-slate-700/50">
                        <span className="text-slate-500 block text-[10px] uppercase mb-1">Final Intent:</span>
                        <span className="text-white font-bold text-sm tracking-wide">{botMessage?.intent || "UNKNOWN"}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
