import os

os.makedirs('frontend/src/app/admin/rag', exist_ok=True)

with open('frontend/src/app/admin/rag/page.tsx', 'w') as f:
    f.write('''\
"use client";
import React, { useState } from 'react';
import { Search, Sliders, CheckCircle, Database } from 'lucide-react';

export default function RAGSettingsPage() {
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.8);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // Save logic
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="h-full bg-slate-50 dark:bg-slate-950 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Search className="text-blue-600" />
            RAG Engine Configuration
          </h1>
          <p className="text-slate-500 mt-1">Configure vector retrieval thresholds and chunking strategies.</p>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Sliders size={18} /> Retrieval Settings
          </h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Top K Results ({topK})
              </label>
              <p className="text-xs text-slate-500 mb-2">Maximum number of document chunks to retrieve.</p>
              <input 
                type="range" min="1" max="20" value={topK} 
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Similarity Threshold ({threshold})
              </label>
              <p className="text-xs text-slate-500 mb-2">Minimum cosine similarity score required (0.0 to 1.0).</p>
              <input 
                type="range" min="0" max="1" step="0.01" value={threshold} 
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>
            
            <hr className="border-slate-200 dark:border-slate-800" />
            
            <div>
               <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Vector Database</h3>
               <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-800">
                  <Database className="text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Qdrant Engine</p>
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Connected (In-Memory / Local)</p>
                  </div>
               </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button 
                onClick={handleSave}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition"
              >
                {saved ? <><CheckCircle size={18} /> Saved!</> : "Save Configuration"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
''')
