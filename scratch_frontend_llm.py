import os

os.makedirs('frontend/src/app/admin/llm', exist_ok=True)

with open('frontend/src/app/admin/llm/page.tsx', 'w') as f:
    f.write('''\
"use client";
import React, { useState } from 'react';
import { Cpu, ShieldCheck, Activity, Save, AlertTriangle } from 'lucide-react';

export default function LLMGatewayPage() {
  const [provider, setProvider] = useState("gemini");
  const [temperature, setTemperature] = useState(0.2);
  const [guardrailsEnabled, setGuardrailsEnabled] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="h-full bg-slate-50 dark:bg-slate-950 p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6 pb-20">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Cpu className="text-blue-600" />
            Enterprise LLM Gateway
          </h1>
          <p className="text-slate-500 mt-1">Configure foundational models, prompt templates, and security guardrails.</p>
        </div>

        {/* Global Settings */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-6 text-slate-900 dark:text-slate-100">
            <Activity size={18} className="text-blue-500" /> Provider Configuration
          </h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Active Provider
              </label>
              <select 
                value={provider}
                onChange={e => setProvider(e.target.value)}
                className="w-full max-w-sm px-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-sm"
              >
                <option value="gemini">Google Gemini (Gemini 1.5 Pro)</option>
                <option value="openai" disabled>OpenAI (Coming Soon)</option>
                <option value="claude" disabled>Anthropic Claude (Coming Soon)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Model Temperature ({temperature})
              </label>
              <p className="text-xs text-slate-500 mb-2">Higher values produce more creative but less deterministic responses.</p>
              <input 
                type="range" min="0" max="1" step="0.1" value={temperature} 
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full max-w-sm accent-blue-600"
              />
            </div>
          </div>
        </div>

        {/* Security & Guardrails */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-6 text-slate-900 dark:text-slate-100">
            <ShieldCheck size={18} className="text-emerald-500" /> Security Guardrails
          </h2>
          
          <div className="space-y-4">
            <label className="flex items-center gap-3 p-4 border border-slate-200 dark:border-slate-800 rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
              <input 
                type="checkbox" 
                checked={guardrailsEnabled} 
                onChange={(e) => setGuardrailsEnabled(e.target.checked)}
                className="w-5 h-5 accent-blue-600 rounded"
              />
              <div>
                <p className="font-medium text-slate-900 dark:text-slate-100">Enable Input/Output Validation</p>
                <p className="text-sm text-slate-500 mt-0.5">Automatically blocks prompt injections, jailbreaks, and hallucinatory formats before execution.</p>
              </div>
            </label>
          </div>
        </div>

        {/* Output Schema */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 text-slate-900 dark:text-slate-100">
            <AlertTriangle size={18} className="text-amber-500" /> System Fallback
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            If all modules and the LLM fail to generate a safe response, this message will be shown.
          </p>
          <input 
            type="text" 
            defaultValue="I'm sorry, I cannot process that request at this time."
            className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-sm"
          />
        </div>

        <div className="flex justify-end pt-4">
          <button 
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition"
          >
            {saved ? <><ShieldCheck size={18} /> Settings Saved</> : <><Save size={18} /> Save Configuration</>}
          </button>
        </div>
      </div>
    </div>
  );
}
''')
