import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, User, Check, CheckCheck, Copy, RefreshCw, ThumbsUp, ThumbsDown, Volume2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { Tooltip } from './Tooltip';
import { ComponentRenderer } from '../sdui/ComponentRenderer';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeSanitize from 'rehype-sanitize';
import rehypeHighlight from 'rehype-highlight';

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
  format?: 'markdown' | 'text';
  onReplay?: () => void;
  onAction?: (action: string, payload?: any) => void;
};

const getIntentColor = (intent?: string) => {
  if (!intent) return "";
  const lower = intent.toLowerCase();
  if (lower === "greeting") return "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800/50";
  if (lower === "fallback") return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50";
  if (lower === "gibberish") return "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50";
  if (lower === "goodbye") return "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50";
  if (lower === "fastpath") return "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800/50";
  return "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700";
};

// Markdown Renderer with Memoization
const MarkdownRenderer = React.memo(({ content }: { content: string }) => {
  // Extract breadcrumb if it exists at the start of the message
  let textToRender = content;
  let breadcrumb = null;

  const breadcrumbMatch = textToRender.match(/^📍 \*\*(.*?)\*\*\n\n/);
  if (breadcrumbMatch) {
    breadcrumb = breadcrumbMatch[1];
    textToRender = textToRender.substring(breadcrumbMatch[0].length);
  }

  // Clean up excessive newlines
  textToRender = textToRender.replace(/\n{3,}/g, '\n\n');

  return (
    <>
      {breadcrumb && (
        <div className="mb-3 text-[10.5px] font-semibold text-slate-500 uppercase tracking-widest bg-slate-50 dark:bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-200/60 dark:border-slate-700/60 shadow-sm leading-relaxed">
          <span className="text-blue-500 dark:text-blue-400 mr-1.5 text-[12px] align-baseline">📍</span>
          <span className="opacity-90">{breadcrumb.replace(/➔/g, '›')}</span>
        </div>
      )}
      <div className="markdown-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSanitize, rehypeHighlight]}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const language = match ? match[1] : '';
              
              if (!inline && match) {
                return (
                  <div className="relative my-3 rounded-xl overflow-hidden border border-slate-700/50 bg-[#0d1117] group">
                    <div className="flex items-center justify-between px-4 py-2 text-xs font-sans text-slate-400 bg-[#161b22] border-b border-slate-700/50">
                      <span>{language}</span>
                      <button 
                        onClick={() => navigator.clipboard.writeText(String(children).replace(/\n$/, ''))}
                        className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-white"
                        title="Copy code"
                      >
                        <Copy size={14} />
                      </button>
                    </div>
                    <div className="p-4 overflow-x-auto text-sm">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </div>
                  </div>
                );
              }
              return (
                <code className="px-1.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-pink-500 dark:text-pink-400 text-[0.9em]" {...props}>
                  {children}
                </code>
              );
            },
            table({ children }) {
              return (
                <div className="overflow-x-auto my-3 rounded-lg border border-slate-200 dark:border-slate-700">
                  <table className="min-w-full text-sm text-left">{children}</table>
                </div>
              );
            },
            th({ children }) {
              return <th className="px-4 py-2 bg-slate-50 dark:bg-slate-800/50 font-semibold text-slate-700 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700">{children}</th>;
            },
            td({ children }) {
              return <td className="px-4 py-2 border-b border-slate-200 dark:border-slate-700/50 text-slate-600 dark:text-slate-300">{children}</td>;
            },
            a({ children, href }) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline hover:text-blue-700 dark:hover:text-blue-300">
                  {children}
                </a>
              );
            },
            h1: ({children}) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
            h2: ({children}) => <h2 className="text-lg font-bold mt-4 mb-2">{children}</h2>,
            h3: ({children}) => <h3 className="text-base font-bold mt-3 mb-1">{children}</h3>,
            ul: ({children}) => <ul className="list-disc pl-5 my-2 space-y-0.5">{children}</ul>,
            ol: ({children}) => <ol className="list-decimal pl-5 my-2 space-y-0.5">{children}</ol>,
            li: ({children}) => <li className="text-slate-700 dark:text-slate-200">{children}</li>,
            p: ({children}) => <p className="my-1.5">{children}</p>,
          }}
        >
          {textToRender}
        </ReactMarkdown>
      </div>
    </>
  );
});

export const ChatMessage: React.FC<MessageProps> = ({ role, content, intent, timestamp, status, trace, components, actions, format: msgFormat, onReplay, onAction }) => {
  const isBot = role === 'bot';
  const [isCopied, setIsCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={cn("flex w-full mt-5 space-x-4 group", isBot ? "justify-start" : "justify-end")}
      role="article"
      aria-label={isBot ? "Bot message" : "Your message"}
    >
      {/* Bot Avatar */}
      {isBot && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 shadow-md flex items-center justify-center text-white mt-1 z-10 border border-blue-500/30">
          <span className="font-bold text-lg italic tracking-tighter" style={{ fontFamily: 'Georgia, serif' }}>M</span>
        </div>
      )}

      {/* Message Bubble Container */}
      <div className={cn("flex flex-col max-w-[80%]", isBot ? "items-start" : "items-end")}>

        {/* Bubble */}
        <div className={cn(
          "relative px-5 py-4 text-[14px] md:text-[15px] xl:text-[16px] leading-relaxed break-words whitespace-pre-wrap transition-all duration-300",
          isBot 
            ? "bg-white border border-gray-200/60 text-gray-800 rounded-2xl rounded-tl-sm dark:bg-[#1E293B] dark:border-slate-700/50 dark:text-gray-100 shadow-sm hover:shadow-md"
            : "bg-gradient-to-br from-[#0f172a] to-[#1e293b] dark:from-blue-600 dark:to-blue-800 border border-slate-700/50 dark:border-blue-500/30 text-white rounded-2xl rounded-tr-sm shadow-md"
        )}>
          {msgFormat === 'markdown' ? (
            <MarkdownRenderer content={content} />
          ) : (() => {
            let textToRender = content;
            let breadcrumb = null;

            // Extract breadcrumb if it exists at the start of the message
            const breadcrumbMatch = textToRender.match(/^📍 \*\*(.*?)\*\*\n\n/);
            if (breadcrumbMatch) {
              breadcrumb = breadcrumbMatch[1];
              textToRender = textToRender.substring(breadcrumbMatch[0].length);
            }

            // Move pointing hand icon inside the link so it renders inside the button
            textToRender = textToRender.replace(/👉\s*\[/g, '[👉 ');

            const parts = textToRender.split(/(\*\*.*?\*\*|\[.*?\]\(.*?\))/g).map((part, i) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i} className="font-semibold text-blue-700 dark:text-blue-400">{part.slice(2, -2)}</strong>;
              }
              if (part.startsWith('[') && part.endsWith(')') && part.includes('](')) {
                const match = part.match(/\[(.*?)\]\((.*?)\)/);
                if (match) {
                  return (
                    <a 
                      key={i} 
                      href={match[2]} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-block mt-3 mb-1 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-sm hover:shadow transition-all no-underline w-auto border border-blue-500"
                    >
                      {match[1]}
                    </a>
                  );
                }
              }
              return <React.Fragment key={i}>{part}</React.Fragment>;
            });

            return (
              <>
                {breadcrumb && (
                  <div className="mb-3 text-[10.5px] font-semibold text-slate-500 uppercase tracking-widest bg-slate-50 dark:bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-200/60 dark:border-slate-700/60 shadow-sm leading-relaxed">
                    <span className="text-blue-500 dark:text-blue-400 mr-1.5 text-[12px] align-baseline">📍</span>
                    <span className="opacity-90">{breadcrumb.replace(/➔/g, '›')}</span>
                  </div>
                )}
                {parts}
              </>
            );
          })()}
          
          {/* SDUI Components rendering inside the bubble if bot */}
          {isBot && components && components.length > 0 && onAction && (
            <div className="mt-4 border-t border-gray-100 dark:border-slate-700/50 pt-4">
              <ComponentRenderer components={components} onAction={onAction} />
            </div>
          )}

          {/* Timestamp and Status inside or below */}
          <div className={cn(
            "flex items-center gap-1.5 text-[0.7rem] mt-2 justify-end opacity-70 font-medium tracking-wide",
            isBot ? "text-gray-400 dark:text-gray-500" : "text-gray-300 dark:text-blue-200"
          )}>
            <span>{format(new Date(timestamp), 'h:mm a')}</span>
            
            {!isBot && status && (
              <span className="ml-0.5">
                {status === 'sent' && <Check size={14} />}
                {(status === 'delivered' || status === 'read') && <CheckCheck size={14} className={status === 'read' ? 'text-blue-400' : ''} />}
              </span>
            )}
          </div>
        </div>
        
        {/* Actions Toolbar */}
        <div className={cn(
          "flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200",
          isBot ? "ml-1" : "mr-1 justify-end"
        )}>
          {isBot && (
            <>
              <Tooltip content="Helpful">
                <button className="p-1.5 rounded-md bg-white border border-gray-100 shadow-sm text-gray-400 hover:text-blue-600 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all">
                  <ThumbsUp size={14} />
                </button>
              </Tooltip>
              <Tooltip content="Not Helpful">
                <button className="p-1.5 rounded-md bg-white border border-gray-100 shadow-sm text-gray-400 hover:text-red-600 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all">
                  <ThumbsDown size={14} />
                </button>
              </Tooltip>
            </>
          )}
          
          <Tooltip content={isCopied ? "Copied!" : "Copy"}>
            <button onClick={handleCopy} className="p-1.5 rounded-md bg-white border border-gray-100 shadow-sm text-gray-400 hover:text-gray-700 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all">
              {isCopied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
            </button>
          </Tooltip>
          
          {isBot && onReplay && trace && (
            <Tooltip content="Replay Pipeline">
              <button onClick={onReplay} className="p-1.5 rounded-md bg-white border border-emerald-100 shadow-sm text-emerald-500 hover:text-emerald-700 hover:bg-emerald-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 transition-all ml-1">
                <RefreshCw size={14} />
              </button>
            </Tooltip>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {!isBot && (
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 shadow-sm flex items-center justify-center text-gray-500 dark:text-gray-400 mt-1 z-10">
          <User size={18} />
        </div>
      )}
    </motion.div>
  );
};

