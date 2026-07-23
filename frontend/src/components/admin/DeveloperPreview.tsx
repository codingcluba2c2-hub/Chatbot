"use client";
import { useState } from "react";
import { X, Send, PlayCircle, Loader2 } from "lucide-react";

export function DeveloperPreview({ onClose }: { onClose: () => void }) {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const testPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    setLoading(true);
    setError("");
    setResult(null);
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_URL;
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: input,
          session_id: "preview_session",
          conversation_id: "preview_conv"
        }),
      });
      
      if (!response.ok) throw new Error("Failed to test pipeline");
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
        <h2 className="font-semibold flex items-center">
          <PlayCircle className="w-4 h-4 mr-2 text-indigo-500" />
          Preview & Trace
        </h2>
        <button onClick={onClose} className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {error && (
          <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100">
            {error}
          </div>
        )}
        
        {result && (
          <div className="space-y-4">
            <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-900/50">
              <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-1 uppercase tracking-wider">Intent Match</div>
              <div className="font-medium">{result.intent}</div>
            </div>
            
            <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-wider">Response</div>
              <div className="text-sm whitespace-pre-wrap">{result.response}</div>
            </div>
            
            <div>
              <div className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Execution Trace ({result.trace?.totalBackendTimeMs}ms)</div>
              <div className="space-y-2">
                {result.trace?.steps?.filter((s: any) => s.durationMs > 0 || Object.keys(s.details).length > 0).map((step: any, i: number) => (
                  <div key={i} className="text-xs p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                    <div className="flex justify-between font-medium text-slate-700 dark:text-slate-300 mb-1">
                      <span>{step.step}</span>
                      <span className="text-slate-400">{step.durationMs}ms</span>
                    </div>
                    {Object.keys(step.details).length > 0 && (
                      <pre className="text-[10px] text-slate-500 overflow-x-auto p-1 bg-slate-50 dark:bg-slate-950 rounded">
                        {JSON.stringify(step.details, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {!result && !loading && !error && (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-500 p-4">
            <PlayCircle className="w-12 h-12 mb-3 text-slate-300 dark:text-slate-700" />
            <p className="text-sm">Type a message below to test the pipeline live without restarting the server.</p>
          </div>
        )}
      </div>
      
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <form onSubmit={testPipeline} className="relative">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a test message..."
            className="w-full pl-3 pr-10 py-2 bg-slate-100 dark:bg-slate-800 border-transparent focus:border-blue-500 focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-blue-500/20 rounded-lg text-sm outline-none transition-all"
            disabled={loading}
          />
          <button 
            type="submit" 
            disabled={!input.trim() || loading}
            className="absolute right-1.5 top-1.5 p-1 text-blue-500 hover:text-blue-600 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
      </div>
    </div>
  );
}
