import os

components = {}

components['DeveloperSidebar.tsx'] = '''\
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
  const [activeTab, setActiveTab] = useState<'timeline' | 'network' | 'performance' | 'pipeline' | 'memory' | 'logs'>('pipeline');

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
    { id: 'pipeline', label: 'Pipeline', icon: GitBranch },
    { id: 'network', label: 'Network', icon: Network },
    { id: 'timeline', label: 'Timeline', icon: Activity },
    { id: 'memory', label: 'Memory', icon: Database },
    { id: 'logs', label: 'Logs', icon: Terminal },
    { id: 'performance', label: 'Performance', icon: Clock },
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
                {trace && <span>Latency: {trace.totalBackendTimeMs}ms</span>}
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
                {activeTab === 'timeline' && <PipelineTimeline trace={trace} mode="timeline" />}
                {activeTab === 'network' && (
                  <div className="space-y-4">
                    <div className="font-mono text-xs p-3 rounded-md bg-slate-900 border border-slate-800 overflow-x-auto">
                      <div className="flex justify-between items-center mb-2 pb-2 border-b border-slate-800">
                        <span className="text-blue-300 font-bold">POST /api/chat</span>
                        <span className="text-emerald-400">200 OK</span>
                      </div>
                      <div className="mt-2 text-slate-400 uppercase tracking-widest text-[10px]">Headers</div>
                      <pre className="text-slate-300 ml-2 mt-1">Content-Type: application/json</pre>
                      <div className="mt-4 text-slate-400 uppercase tracking-widest text-[10px]">Request Payload</div>
                      <pre className="text-amber-300 mt-1 bg-slate-950 p-2 rounded">
                        {JSON.stringify({ message: selectedMessage?.content || "" }, null, 2)}
                      </pre>
                      <div className="mt-4 text-slate-400 uppercase tracking-widest text-[10px]">Response Payload</div>
                      <pre className="text-emerald-300 mt-1 bg-slate-950 p-2 rounded">
                        {JSON.stringify({ intent: botMessage.intent, response: botMessage.content }, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                {activeTab === 'performance' && (
                  <div className="space-y-4">
                    <div className="p-4 rounded-md bg-slate-900 border border-slate-800">
                      <h4 className="text-xs font-semibold text-slate-400 mb-4 uppercase tracking-wider">Timing Breakdown</h4>
                      <div className="space-y-3 text-sm font-mono">
                        <div className="flex flex-col gap-1">
                          <div className="flex justify-between items-center text-slate-300">
                            <span>Backend Time</span>
                            <span className="text-blue-400">{trace.totalBackendTimeMs} ms</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-blue-500 h-full" style={{ width: '100%' }}></div>
                          </div>
                        </div>
                        <div className="flex flex-col gap-1 opacity-70">
                          <div className="flex justify-between items-center text-slate-300">
                            <span>Network Latency</span>
                            <span className="text-amber-400">~{Math.round(trace.totalBackendTimeMs * 1.5)} ms</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-amber-500 h-full" style={{ width: '60%' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                {activeTab === 'memory' && (
                  <div className="font-mono text-xs p-3 rounded-md bg-slate-900 border border-slate-800">
                    <div className="text-slate-400 uppercase tracking-widest text-[10px] mb-2">Session Facts & Entities</div>
                    <p className="text-slate-500 mb-4 italic">Memory state extracted during this turn:</p>
                    {trace.steps.filter((s:any) => s.step_name === 'Memory' || s.step_name === 'Regex').map((s:any, idx:number) => (
                      <div key={idx} className="mb-4">
                        <span className="text-emerald-400">[{s.step_name}]</span>
                        <pre className="text-amber-300 mt-1 bg-slate-950 p-2 rounded">
                          {JSON.stringify(s.output?.entities || {}, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
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
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
'''

components['PipelineTimeline.tsx'] = '''\
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight, CheckCircle2, AlertTriangle, ArrowDown } from 'lucide-react';

interface TraceStep {
  step_name: string;
  duration: number;
  status: string;
  decision: string;
  input: any;
  output: any;
  metadata: Record<string, any>;
}

interface Trace {
  steps: TraceStep[];
  totalBackendTimeMs: number;
}

export const PipelineTimeline: React.FC<{ trace: Trace, mode: 'timeline' | 'graph' }> = ({ trace, mode }) => {
  const [expandedIndices, setExpandedIndices] = React.useState<number[]>([]);

  const toggleExpand = (index: number) => {
    setExpandedIndices(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };
  
  if (!trace || !trace.steps) return <div>No trace data.</div>;

  return (
    <div className="flex flex-col space-y-4">
      {mode === 'graph' && (
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-slate-300">Execution Graph</h3>
        </div>
      )}
      
      <div className={`relative ${mode === 'timeline' ? 'pl-4 border-l-2 border-slate-700/50 space-y-6' : 'flex flex-col items-center space-y-2'}`}>
        {trace.steps.map((step, index) => {
          const isExpanded = expandedIndices.includes(index);
          const isFailed = step.status === 'failed';
          const isSkipped = step.status === 'skipped' || (!step.duration && step.decision === 'Continue' && !Object.keys(step.metadata || {}).length);
          
          if (mode === 'graph') {
            return (
              <React.Fragment key={index}>
                <motion.div 
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`w-full max-w-sm rounded-lg border p-3 cursor-pointer transition-all ${
                    isFailed ? 'bg-red-900/20 border-red-700/50' : 
                    step.decision === 'Stop' ? 'bg-emerald-900/20 border-emerald-700/50 shadow-[0_0_15px_rgba(16,185,129,0.15)]' :
                    'bg-slate-800/80 border-slate-700 hover:bg-slate-800'
                  }`}
                  onClick={() => toggleExpand(index)}
                >
                  <div className="flex justify-between items-center">
                    <span className={`font-semibold text-sm ${step.decision === 'Stop' ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {step.step_name}
                    </span>
                    <span className="text-xs font-mono text-slate-400">{step.duration}ms</span>
                  </div>
                  
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                        <div className="mt-3 pt-3 border-t border-slate-700/50 flex flex-col gap-2">
                          <div className="flex justify-between text-[11px] font-mono">
                            <span className="text-slate-500">Decision</span>
                            <span className={step.decision === 'Stop' ? 'text-emerald-400' : 'text-amber-400'}>{step.decision}</span>
                          </div>
                          {Object.entries(step.metadata || {}).map(([key, value]) => (
                            <div key={key} className="flex flex-col">
                              <span className="text-[10px] uppercase tracking-wider text-slate-500">{key}</span>
                              <span className="text-xs font-mono text-blue-300 break-all">
                                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
                {index < trace.steps.length - 1 && (
                  <ArrowDown size={16} className="text-slate-600" />
                )}
              </React.Fragment>
            );
          }

          // Timeline Mode
          return (
            <motion.div 
              key={index} 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="relative"
            >
              <div className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full ring-4 ring-slate-950 ${
                isFailed ? 'bg-red-500' : step.decision === 'Stop' ? 'bg-emerald-500' : 'bg-blue-500'
              }`} />
              
              <div 
                className="bg-slate-900 border border-slate-800 rounded-lg p-3 cursor-pointer hover:border-slate-700 transition-colors"
                onClick={() => toggleExpand(index)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {isExpanded ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
                    <span className="font-semibold text-sm text-slate-200">{step.step_name}</span>
                    {step.decision === 'Stop' && <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-wider ml-2">Terminal</span>}
                  </div>
                  <span className="text-xs font-mono text-slate-400">{step.duration} ms</span>
                </div>
                
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 pt-3 border-t border-slate-800 flex flex-col gap-3">
                        <div className="flex gap-4">
                          <div className="flex-1 bg-slate-950 p-2 rounded border border-slate-800">
                            <div className="text-[10px] uppercase text-slate-500 mb-1">Input Message</div>
                            <div className="text-xs font-mono text-slate-300">{step.input?.message || 'N/A'}</div>
                          </div>
                          <div className="flex-1 bg-slate-950 p-2 rounded border border-slate-800">
                            <div className="text-[10px] uppercase text-slate-500 mb-1">Output Message</div>
                            <div className="text-xs font-mono text-slate-300">{step.output?.message || 'N/A'}</div>
                          </div>
                        </div>
                        {step.metadata && Object.keys(step.metadata).length > 0 && (
                          <div className="bg-slate-950 p-2 rounded border border-slate-800">
                            <div className="text-[10px] uppercase text-slate-500 mb-1">Metadata</div>
                            <pre className="text-xs font-mono text-amber-300 overflow-x-auto">
                              {JSON.stringify(step.metadata, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          );
        })}
        
        {mode === 'timeline' && (
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: trace.steps.length * 0.05 }}
            className="relative"
          >
            <div className="absolute -left-[25px] top-0 bg-slate-950">
              <CheckCircle2 size={18} className="text-emerald-500" />
            </div>
            <div className="pl-2">
              <span className="font-semibold text-sm text-slate-300">Response Generated</span>
              <div className="text-xs font-mono text-slate-500 mt-1">
                Total Backend Time: <span className="text-emerald-400">{trace.totalBackendTimeMs} ms</span>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};
'''

for filename, content in components.items():
    with open(f'frontend/src/components/dev/{filename}', 'w') as f:
        f.write(content)
