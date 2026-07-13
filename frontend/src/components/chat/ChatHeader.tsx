import React, { useEffect, useState } from 'react';
import { Bot, RefreshCw, MoreVertical, Moon, Sun } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Tooltip } from './Tooltip';
import { useTheme } from 'next-themes';

interface ChatHeaderProps {
  status?: 'online' | 'offline';
  model?: string;
  latency?: number;
  onRefreshClick: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ 
  status = 'online', 
  model = 'Python API', 
  latency = 120,
  onRefreshClick
}) => {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  return (
    <div className="flex items-center justify-between p-3 sm:p-4 border-b border-[var(--color-border)] bg-[var(--color-cards)]/95 backdrop-blur-sm sm:rounded-t-2xl shadow-sm z-10 sticky top-0 transition-colors duration-300">
      {/* Left section */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border border-blue-200 dark:border-blue-800/50 rounded-full shadow-sm text-blue-600 dark:text-blue-400">
            <Bot size={24} className="scale-90 sm:scale-100" />
          </div>
          {status === 'online' ? (
            <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 border-2 border-white rounded-full">
              <div className="absolute inset-0 bg-green-500 rounded-full animate-ping opacity-75"></div>
            </div>
          ) : (
            <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-red-500 border-2 border-white rounded-full"></div>
          )}
        </div>
        <div>
          <h1 className="text-[var(--color-text-main)] font-semibold text-lg leading-tight">
            AI Assistant
          </h1>
          <p className="text-[var(--color-secondary)] text-sm flex items-center gap-1.5">
            Customer Support AI
            <span className="text-gray-300">•</span>
            {status === 'online' ? (
              <span className="text-green-600 dark:text-green-400 font-medium text-xs bg-green-50 dark:bg-green-900/30 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                Online
              </span>
            ) : (
              <span className="text-red-600 dark:text-red-400 font-medium text-xs bg-red-50 dark:bg-red-900/30 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                Offline
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center gap-4 text-sm text-[var(--color-secondary)]">
        <div className="hidden md:flex flex-col items-end mr-2">
          <div className="flex items-center gap-1.5">
            <span className={cn("w-2 h-2 rounded-full", status === 'online' ? "bg-green-500" : "bg-red-500")}></span>
            <span className="font-medium text-[var(--color-text-main)]">{status === 'online' ? 'Connected' : 'Disconnected'}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span>{model}</span>
            <span>•</span>
            <span>{latency} ms</span>
          </div>
        </div>
        
        <Tooltip content="Clear Chat (Ctrl+L)">
          <button 
            onClick={onRefreshClick}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 active:bg-gray-200 dark:active:bg-gray-700 cursor-pointer" 
            aria-label="Refresh"
          >
            <RefreshCw size={18} />
          </button>
        </Tooltip>

        {mounted && (
          <Tooltip content={theme === 'dark' ? "Light Mode" : "Dark Mode"}>
            <button 
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 active:bg-gray-200 dark:active:bg-gray-700 cursor-pointer" 
              aria-label="Toggle Theme"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </Tooltip>
        )}
      </div>
    </div>
  );
};
