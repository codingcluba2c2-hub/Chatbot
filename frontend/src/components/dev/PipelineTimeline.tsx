import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ArrowDown } from 'lucide-react';

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

  // Compile the 7 logical stages from the raw trace
  const displayStages = React.useMemo(() => {
    if (!trace?.steps) return [];
    
    // Helper to find a specific step in trace
    const getStep = (name: string) => trace.steps.find((s: any) => s.step_name === name || s.step_name === `${name}Step`);
    
    const normalizeStep = getStep('Normalize');
    const spellStep = getStep('SpellCorrection');
    const aliasStep = getStep('AliasExpansion');
    const intentRouterStep = getStep('IntentRouter');
    const followupStep = getStep('FollowUpResolver');
    const knowledgeStep = getStep('KnowledgeSearch');
    const responseGenStep = getStep('ResponseGenerator');
    const cacheStep = getStep('ResponseCache');

    let stages: any[] = [];

    // Stage 1: Normalize
    if (normalizeStep) {
      stages.push({
        id: 'normalize',
        title: 'Normalize',
        icon: '📝',
        status: 'Completed',
        color: 'blue',
        duration: normalizeStep.duration,
        details: [
          { label: 'Original Query', value: normalizeStep.metadata?.original_query || 'N/A' },
          { label: 'Normalized Query', value: normalizeStep.metadata?.normalized_query || 'N/A' }
        ]
      });
    }

    // Stage 2: Rewrite Query
    const rewriteStep = getStep('QueryRewrite');
    if (rewriteStep) {
      stages.push({
        id: 'rewrite',
        title: 'Rewrite Query',
        icon: '🔄',
        status: 'Completed',
        color: 'blue',
        duration: rewriteStep.duration,
        details: [
          { label: 'Rewritten Query', value: rewriteStep.metadata?.rewritten_query || 'N/A' }
        ]
      });
    }

    // Stage 3: Intent
    const actualIntent = intentRouterStep?.metadata?.route || trace.steps[trace.steps.length - 1]?.intent || 'Unknown';
    stages.push({
      id: 'intent',
      title: 'Intent Detection',
      icon: '🧠',
      status: 'Completed',
      color: 'blue',
      duration: intentRouterStep?.duration || 0,
      details: [
        { label: 'Detected Intent', value: actualIntent }
      ]
    });

    // Stage 4: Entities
    const entities = responseGenStep?.metadata?.current_entity || followupStep?.metadata?.resolved_entity || 'None';
    stages.push({
      id: 'entities',
      title: 'Entity Detection',
      icon: '🔎',
      status: 'Completed',
      color: 'blue',
      duration: spellStep?.duration || 0,
      details: [
        { label: 'Detected Entities', value: entities }
      ]
    });

    // Stage 5: Metadata Match
    stages.push({
      id: 'metadata_match',
      title: 'Metadata Match',
      icon: '🏷️',
      status: 'Completed',
      color: 'blue',
      duration: 1, // instantaneous
      details: [
        { label: 'Heading Filter', value: responseGenStep?.metadata?.current_heading || 'None' }
      ]
    });

    // Stage 6: Hybrid Retrieval
    if (knowledgeStep) {
      stages.push({
        id: 'hybrid_retrieval',
        title: 'Hybrid Retrieval',
        icon: '📚',
        status: 'Completed',
        color: 'blue',
        duration: knowledgeStep.metadata?.retrieval_latency_ms || knowledgeStep.duration,
        details: [
          { label: 'Chunks Retrieved', value: knowledgeStep.metadata?.retrieved_chunks_count || 0 },
          { label: 'Search Type', value: 'Vector + BM25' }
        ]
      });

      // Stage 7: Reranking
      stages.push({
        id: 'reranking',
        title: 'Cross-Encoder Reranking',
        icon: '⚖️',
        status: 'Completed',
        color: 'blue',
        duration: 5,
        details: [
          { label: 'Algorithm', value: 'Weighted Fusion + Mock CrossEncoder' },
          { label: 'Chunks Selected', value: knowledgeStep.metadata?.selected_chunks_count || 0 },
          { label: 'Highest Score', value: knowledgeStep.metadata?.top_score?.toFixed(2) || 0 }
        ]
      });

      // Stage 8: Context Merge
      stages.push({
        id: 'context_merge',
        title: 'Context Merge',
        icon: '🧩',
        status: 'Completed',
        color: 'blue',
        duration: 2,
        details: [
          { label: 'Sections Generated', value: knowledgeStep.metadata?.merged_chunks_count || 0 },
          { label: 'Context Tokens', value: knowledgeStep.metadata?.context_tokens || 0 }
        ]
      });
    }

    // Stage 9: LLM Formatting
    if (responseGenStep) {
      stages.push({
        id: 'llm_formatting',
        title: 'LLM Formatting',
        icon: '✨',
        status: 'Completed',
        color: 'blue',
        duration: responseGenStep.metadata?.formatting_time_ms || responseGenStep.duration,
        details: [
          { label: 'LLM Provider', value: responseGenStep.metadata?.["Chosen Provider"] || 'Local Formatter' },
          { label: 'Response Source', value: responseGenStep.metadata?.response_source || 'LLM' },
          { label: 'Response Length', value: responseGenStep.metadata?.response_length || 0 }
        ]
      });
    }

    // Stage 10: Final Response
    stages.push({
      id: 'final',
      title: 'Final Response',
      icon: '✅',
      status: 'Completed',
      color: 'green',
      duration: 1,
      details: [
        { label: 'Total Latency', value: `${trace.totalBackendTimeMs?.toFixed(0)} ms` }
      ]
    });

    return stages;
  }, [trace]);

  if (mode !== 'graph') {
    return <div>Only Execution Graph mode is supported in Enterprise Debugger.</div>;
  }

  return (
    <div className="flex flex-col space-y-4 font-sans">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-300 tracking-wide uppercase">Enterprise AI Debugger</h3>
      </div>
      
      <div className="flex flex-col items-center space-y-2">
        {displayStages.map((stage: any, index: number) => {
          const isExpanded = expandedIndices.includes(index);
          
          let bgColor = 'bg-slate-800/80 border-slate-700/50';
          let textColor = 'text-slate-300';
          
          if (stage.color === 'blue') {
            bgColor = 'bg-blue-900/20 border-blue-700/50';
            textColor = 'text-blue-400';
          } else if (stage.color === 'green') {
            bgColor = 'bg-emerald-900/20 border-emerald-700/50 shadow-[0_0_15px_rgba(16,185,129,0.15)]';
            textColor = 'text-emerald-400';
          } else if (stage.color === 'yellow') {
            bgColor = 'bg-amber-900/20 border-amber-700/50';
            textColor = 'text-amber-400';
          } else if (stage.color === 'red') {
            bgColor = 'bg-red-900/20 border-red-700/50';
            textColor = 'text-red-400';
          } else if (stage.color === 'grey') {
            bgColor = 'bg-slate-900/50 border-slate-800 border-dashed';
            textColor = 'text-slate-500';
          }
          
          return (
            <React.Fragment key={stage.id}>
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`w-full max-w-sm rounded-lg border p-3 cursor-pointer transition-all hover:bg-slate-800/80 ${bgColor}`}
                onClick={() => toggleExpand(index)}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{stage.icon}</span>
                    <span className={`font-semibold text-sm ${textColor}`}>
                      {stage.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${textColor}`}>
                      {stage.status}
                    </span>
                    {stage.duration > 0 && stage.status !== 'Skipped' && (
                      <span className="text-xs font-mono text-slate-500">{stage.duration}ms</span>
                    )}
                  </div>
                </div>
                
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                      <div className="mt-3 pt-3 border-t border-slate-700/50 flex flex-col gap-2">
                        {stage.details.map((detail: any, dIndex: number) => (
                          <div key={dIndex} className="flex flex-col mb-1">
                            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">{detail.label}</span>
                            <span className={`text-xs font-mono break-words ${detail.label === 'Final Answer' ? 'text-slate-300 mt-1 bg-slate-950/50 p-2 rounded' : 'text-slate-200'}`}>
                              {String(detail.value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
              {index < displayStages.length - 1 && (
                <ArrowDown size={16} className="text-slate-600" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
