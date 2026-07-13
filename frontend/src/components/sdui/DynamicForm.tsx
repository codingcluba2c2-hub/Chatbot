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
