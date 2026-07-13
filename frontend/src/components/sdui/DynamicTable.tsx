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
