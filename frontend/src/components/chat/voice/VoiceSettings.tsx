import React from 'react';
import { Settings, Volume2, Mic } from 'lucide-react';
import { SpeechSettings, SUPPORTED_LANGUAGES } from '../../../types/speech';

interface VoiceSettingsProps {
  settings: SpeechSettings;
  setSettings: React.Dispatch<React.SetStateAction<SpeechSettings>>;
  voices: SpeechSynthesisVoice[];
}

export const VoiceSettings: React.FC<VoiceSettingsProps> = ({ settings, setSettings, voices }) => {
  return (
    <div className="flex flex-col gap-4 p-4 min-w-[280px]">
      <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-700 pb-2">
        <Settings size={16} />
        Voice Settings
      </div>

      <div className="space-y-3">
        {/* Language Selection */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Mic size={12} />
            Input Language
          </label>
          <select
            value={settings.language}
            onChange={(e) => setSettings({ ...settings, language: e.target.value })}
            className="w-full text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1.5 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Output Voice */}
        <div className="flex flex-col gap-1.5 pt-2">
          <label className="text-xs font-medium text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Volume2 size={12} />
            Output Voice
          </label>
          <select
            value={settings.voiceURI || ''}
            onChange={(e) => setSettings({ ...settings, voiceURI: e.target.value })}
            className="w-full text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1.5 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Default OS Voice</option>
            {voices.filter(v => v.lang.startsWith(settings.language.split('-')[0])).map((voice) => (
              <option key={voice.voiceURI} value={voice.voiceURI}>
                {voice.name}
              </option>
            ))}
          </select>
        </div>

        {/* Pitch and Rate */}
        <div className="flex flex-col gap-3 pt-2">
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Pitch</label>
              <span className="text-xs text-slate-400">{settings.pitch.toFixed(1)}</span>
            </div>
            <input 
              type="range" 
              min="0.1" max="2" step="0.1" 
              value={settings.pitch}
              onChange={(e) => setSettings({ ...settings, pitch: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Speed</label>
              <span className="text-xs text-slate-400">{settings.rate.toFixed(1)}x</span>
            </div>
            <input 
              type="range" 
              min="0.5" max="2" step="0.1" 
              value={settings.rate}
              onChange={(e) => setSettings({ ...settings, rate: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>

        {/* Auto Speak Toggle */}
        <div className="flex items-center justify-between pt-2">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Auto Speak Responses
          </label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              className="sr-only peer"
              checked={settings.autoSpeak}
              onChange={(e) => setSettings({ ...settings, autoSpeak: e.target.checked })}
            />
            <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-gray-600 peer-checked:bg-blue-500"></div>
          </label>
        </div>
      </div>
    </div>
  );
};
