import React from 'react';
import { Network, ExternalLink, Download, FileText, ChevronRight, Mail, Calendar } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export const KnowledgeCard = ({ 
  node, 
  onAction 
}: { 
  node: any, 
  onAction: (action: string, payload?: any) => void 
}) => {
  if (!node) return null;

  const handleButtonClick = (btn: any) => {
    // Send hidden payload to backend so it loads the node by ID directly
    onAction('send_message', { 
      action: 'load_node', 
      text: btn.label, 
      metadata: { nodeId: btn.id }
    });
  };

  const getIcon = (iconName: string) => {
    // Basic emoji icons since they are sent from backend as emoji strings
    // If it's a known string name, fallback to Lucide, else return as text
    if (!iconName) return <ChevronRight className="w-4 h-4 mr-2 text-indigo-500" />;
    
    switch (iconName?.toLowerCase()) {
      case 'external-link': return <ExternalLink className="w-4 h-4 mr-2" />;
      case 'download': return <Download className="w-4 h-4 mr-2" />;
      case 'file-text': return <FileText className="w-4 h-4 mr-2" />;
      case 'mail': return <Mail className="w-4 h-4 mr-2" />;
      case 'calendar': return <Calendar className="w-4 h-4 mr-2" />;
      default: return <span className="mr-2">{iconName}</span>;
    }
  };

  return (
    <div className="flex flex-col w-full max-w-[450px]">
      
      {/* Breadcrumbs */}
      {node.breadcrumbs && node.breadcrumbs.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">
          {node.breadcrumbs.map((crumb: any, i: number) => (
            <React.Fragment key={crumb.id || i}>
              {i > 0 && <ChevronRight className="w-3 h-3 text-slate-300 dark:text-slate-600" />}
              <span 
                className={`truncate max-w-[120px] ${i === node.breadcrumbs.length - 1 ? 'text-indigo-600 dark:text-indigo-400 font-semibold' : 'hover:text-slate-700 dark:hover:text-slate-300 cursor-pointer'}`}
                onClick={() => {
                  if (i !== node.breadcrumbs.length - 1) {
                    onAction('send_message', { 
                      action: 'load_node', 
                      text: crumb.title, 
                      metadata: { nodeId: crumb.id }
                    });
                  }
                }}
              >
                {crumb.title}
              </span>
            </React.Fragment>
          ))}
        </div>
      )}

      {/* Markdown */}
      {(node.markdown || node.response_markdown) && (
        <div className="text-[15px] leading-relaxed text-slate-800 dark:text-slate-200 prose prose-sm dark:prose-invert bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm mb-3">
          <ReactMarkdown>{node.markdown || node.response_markdown}</ReactMarkdown>
        </div>
      )}

      {/* Buttons Grid */}
      {node.buttons && node.buttons.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {node.buttons.map((btn: any, idx: number) => (
            <button
              key={idx}
              onClick={() => handleButtonClick(btn)}
              className="flex items-center justify-between px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-md dark:hover:shadow-indigo-900/20 rounded-xl text-sm font-medium transition-all group"
            >
              <div className="flex items-center truncate text-slate-700 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                {getIcon(btn.icon)}
                <span className="truncate">{btn.label}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
