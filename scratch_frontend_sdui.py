import os

components = {}

components['ComponentRenderer.tsx'] = '''\
import React from 'react';
import { QuickReplies } from './QuickReplies';
import { ActionButtons } from './ActionButtons';
import { DynamicCard } from './DynamicCard';
import { DynamicForm } from './DynamicForm';
import { DynamicTable } from './DynamicTable';
import { DynamicCarousel } from './DynamicCarousel';

export const ComponentRenderer = ({ 
  components, 
  onAction 
}: { 
  components: any[], 
  onAction: (action: string, payload?: any) => void 
}) => {
  if (!components || components.length === 0) return null;

  return (
    <div className="flex flex-col gap-3 mt-3 w-full">
      {components.map((comp, idx) => {
        switch (comp.type) {
          case 'quickReplies':
            return <QuickReplies key={idx} items={comp.items} onSelect={(text) => onAction('send_message', { text })} />;
          case 'buttons':
            return <ActionButtons key={idx} buttons={comp.buttons} onClick={(action) => onAction('button_click', { action })} />;
          case 'card':
            return <DynamicCard key={idx} card={comp} onAction={(action) => onAction('button_click', { action })} />;
          case 'form':
            return <DynamicForm key={idx} form={comp} onSubmit={(data) => onAction('form_submit', { action: comp.submit_action, data })} />;
          case 'table':
            return <DynamicTable key={idx} table={comp} />;
          case 'carousel':
            return <DynamicCarousel key={idx} carousel={comp} onAction={(action) => onAction('button_click', { action })} />;
          default:
            return <div key={idx} className="text-xs text-red-400">Unknown component type: {comp.type}</div>;
        }
      })}
    </div>
  );
};
'''

components['QuickReplies.tsx'] = '''\
import React from 'react';

export const QuickReplies = ({ items, onSelect }: { items: string[], onSelect: (text: string) => void }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(item)}
          className="px-4 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 border border-blue-200 rounded-full text-sm font-medium transition-colors dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50 dark:hover:bg-blue-900/50"
        >
          {item}
        </button>
      ))}
    </div>
  );
};
'''

components['ActionButtons.tsx'] = '''\
import React from 'react';

export const ActionButtons = ({ buttons, onClick }: { buttons: any[], onClick: (action: string) => void }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {buttons.map((btn, idx) => (
        <button
          key={idx}
          onClick={() => onClick(btn.action)}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white shadow-sm"
        >
          {btn.text}
        </button>
      ))}
    </div>
  );
};
'''

components['DynamicCard.tsx'] = '''\
import React from 'react';
import { ActionButtons } from './ActionButtons';

export const DynamicCard = ({ card, onAction }: { card: any, onAction: (action: string) => void }) => {
  return (
    <div className="w-full max-w-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
      {card.image_url && (
        <img src={card.image_url} alt={card.title} className="w-full h-32 object-cover" />
      )}
      <div className="p-4">
        <h3 className="font-bold text-slate-900 dark:text-slate-100">{card.title}</h3>
        {card.subtitle && <p className="text-xs text-blue-600 dark:text-blue-400 font-medium mt-1 uppercase tracking-wider">{card.subtitle}</p>}
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">{card.description}</p>
        
        {card.buttons && card.buttons.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <ActionButtons buttons={card.buttons} onClick={onAction} />
          </div>
        )}
      </div>
    </div>
  );
};
'''

components['DynamicForm.tsx'] = '''\
import React, { useState } from 'react';

export const DynamicForm = ({ form, onSubmit }: { form: any, onSubmit: (data: any) => void }) => {
  const [data, setData] = useState<any>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-4">
      {form.fields.map((field: any, idx: number) => (
        <div key={idx} className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {field.label} {field.required && <span className="text-red-500">*</span>}
          </label>
          
          {field.type === 'dropdown' ? (
            <select
              required={field.required}
              onChange={(e) => setData({ ...data, [field.name]: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            >
              <option value="">Select an option</option>
              {field.options?.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          ) : field.type === 'textarea' ? (
            <textarea
              required={field.required}
              onChange={(e) => setData({ ...data, [field.name]: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 min-h-[80px]"
            />
          ) : (
            <input
              type={field.type}
              required={field.required}
              onChange={(e) => setData({ ...data, [field.name]: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          )}
        </div>
      ))}
      <button type="submit" className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
        Submit
      </button>
    </form>
  );
};
'''

components['DynamicTable.tsx'] = '''\
import React from 'react';

export const DynamicTable = ({ table }: { table: any }) => {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
          <tr>
            {table.columns.map((col: string, idx: number) => (
              <th key={idx} className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-300">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-950">
          {table.rows.map((row: any[], rowIdx: number) => (
            <tr key={rowIdx}>
              {row.map((cell: any, cellIdx: number) => (
                <td key={cellIdx} className="px-4 py-3 text-slate-600 dark:text-slate-400">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
'''

components['DynamicCarousel.tsx'] = '''\
import React from 'react';
import { DynamicCard } from './DynamicCard';

export const DynamicCarousel = ({ carousel, onAction }: { carousel: any, onAction: (action: string) => void }) => {
  return (
    <div className="w-full flex overflow-x-auto gap-4 pb-4 snap-x custom-scrollbar">
      {carousel.items.map((item: any, idx: number) => (
        <div key={idx} className="min-w-[280px] snap-center">
          <DynamicCard card={item} onAction={onAction} />
        </div>
      ))}
    </div>
  );
};
'''

for filename, content in components.items():
    with open(f'frontend/src/components/sdui/{filename}', 'w') as f:
        f.write(content)
