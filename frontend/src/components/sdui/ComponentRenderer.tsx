import React from 'react';
import { QuickReplies } from './QuickReplies';
import { ActionButtons } from './ActionButtons';
import { DynamicCard } from './DynamicCard';
import { DynamicForm } from './DynamicForm';
import { DynamicTable } from './DynamicTable';
import { DynamicCarousel } from './DynamicCarousel';
import { FallbackCard } from './FallbackCard';

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
          case 'fallback':
            return <FallbackCard key={idx} fallback={comp} onAction={onAction} />;
          default:
            return <div key={idx} className="text-xs text-red-400">Unknown component type: {comp.type}</div>;
        }
      })}
    </div>
  );
};
