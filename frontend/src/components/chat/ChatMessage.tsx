import React from 'react';
import { motion } from 'framer-motion';
import { Bot, User, Check, CheckCheck, Copy, ThumbsUp, ThumbsDown, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { Tooltip } from './Tooltip';
import { ComponentRenderer } from '../sdui/ComponentRenderer';

export type MessageProps = {
  id: string;
  role: 'user' | 'bot';
  content: string;
  intent?: string;
  timestamp: number;
  status?: 'sent' | 'delivered' | 'read';
  trace?: any; 
  components?: any[];
  actions?: any[];
  onReplay?: () => void;
  onAction?: (action: string, payload?: any) => void;
};

const getIntentColor = (intent?: string) => {
  if (!intent) return "";
  const lower = intent.toLowerCase();
  if (lower === "greeting") return "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800/50";
  if (lower === "fallback") return "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50";
  if (lower === "gibberish") return "bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50";
  if (lower === "goodbye") return "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50";
  if (lower === "fastpath") return "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800/50";
  return "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700";
};

export const ChatMessage: React.FC<MessageProps> = ({ role, content, intent, timestamp, status, trace, components, actions, onReplay, onAction }) => {
  const isBot = role === 'bot';
  
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn("flex w-full mt-4 space-x-3 group", isBot ? "justify-start" : "justify-end")}
    >
      {/* Bot Avatar */}
      {isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border border-blue-200 dark:border-blue-800/50 shadow-sm flex items-center justify-center text-blue-600 dark:text-blue-400 mt-auto">
          <Bot size={16} />
        </div>
      )}

      {/* Message Bubble Container */}
      <div className={cn("flex flex-col max-w-[80%]", isBot ? "items-start" : "items-end")}>
        
        {/* Name / Badge Row */}
        {isBot && intent && (
          <div className="mb-1.5 ml-1">
            <span className={cn(
              "text-[0.65rem] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border shadow-sm",
              getIntentColor(intent)
            )}>
              {intent.toLowerCase() === 'knowledge' ? 'RAG' : intent}
            </span>
          </div>
        )}

        {/* Bubble */}
        <div className={cn(
          "relative px-4 py-3 rounded-2xl shadow-sm text-[0.95rem] leading-relaxed break-words whitespace-pre-wrap transition-shadow duration-200 hover:shadow-md",
          isBot 
            ? "bg-[var(--color-cards)] border border-[var(--color-border)] text-[var(--color-text-main)] rounded-bl-sm"
            : "bg-gradient-to-br from-blue-600 to-blue-700 dark:from-blue-700 dark:to-blue-800 text-white rounded-br-sm shadow-md shadow-blue-500/20"
        )}>
          {content}
          
          {/* SDUI Components rendering inside the bubble if bot */}
          {isBot && components && components.length > 0 && onAction && (
            <ComponentRenderer components={components} onAction={onAction} />
          )}

          {/* Timestamp and Status inside or below */}
          <div className={cn(
            "flex items-center gap-1 text-[0.65rem] mt-1.5 justify-end opacity-70 font-medium",
            isBot ? "text-[var(--color-secondary)]" : "text-blue-100"
          )}>
            <span>{format(new Date(timestamp), 'h:mm a')}</span>
            
            {!isBot && status && (
              <span className="ml-0.5">
                {status === 'sent' && <Check size={12} />}
                {(status === 'delivered' || status === 'read') && <CheckCheck size={12} className={status === 'read' ? 'text-blue-300' : ''} />}
              </span>
            )}
          </div>
        </div>
        
        {/* Hover Actions Toolbar */}
        <div className={cn(
          "flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200",
          isBot ? "ml-1" : "mr-1 self-end"
        )}>
          {onReplay && trace && (
            <Tooltip content="Replay Pipeline">
              <button onClick={onReplay} className="p-1 text-emerald-500 hover:text-emerald-700 hover:bg-emerald-50 rounded transition-colors flex items-center gap-1 text-[0.65rem] font-medium mr-2">
                <RefreshCw size={12} />
                <span>Replay</span>
              </button>
            </Tooltip>
          )}
          <Tooltip content="Copy">
            <button onClick={handleCopy} className="p-1 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors">
              <Copy size={14} />
            </button>
          </Tooltip>
        </div>
      </div>

      {/* User Avatar */}
      {!isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-700 border border-slate-300 dark:border-slate-600 shadow-sm flex items-center justify-center text-slate-600 dark:text-slate-300 mt-auto">
          <User size={16} />
        </div>
      )}
    </motion.div>
  );
};
