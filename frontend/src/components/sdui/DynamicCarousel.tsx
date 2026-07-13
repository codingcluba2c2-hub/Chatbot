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
