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
            const isMatched = step.metadata && Object.keys(step.metadata).some(k => k.endsWith('_detected') && step.metadata[k] === true);
            let bgColor = 'bg-slate-800/80 border-slate-700'; // Default Gray (Skipped/Not Matched)
            
            if (isFailed) {
              bgColor = 'bg-red-900/20 border-red-700/50';
            } else if (step.decision === 'Stop') {
              bgColor = 'bg-orange-900/20 border-orange-700/50 shadow-[0_0_15px_rgba(249,115,22,0.15)]';
            } else if (isMatched || step.step_name === 'KnowledgeSearch' && step.metadata.knowledge_search_decision === 'EXECUTED') {
              bgColor = 'bg-emerald-900/20 border-emerald-700/50';
            } else if (step.duration > 0 && !isSkipped) {
              bgColor = 'bg-blue-900/20 border-blue-700/50'; // Executed but didn't match/stop
            }
            
            return (
              <React.Fragment key={index}>
                <motion.div 
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`w-full max-w-sm rounded-lg border p-3 cursor-pointer transition-all hover:bg-slate-700 ${bgColor}`}
                  onClick={() => toggleExpand(index)}
                >
                  <div className="flex justify-between items-center">
                    <span className={`font-semibold text-sm ${step.decision === 'Stop' ? 'text-orange-400' : (isMatched ? 'text-emerald-400' : 'text-slate-200')}`}>
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
