"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Trash2, Edit2, Loader2, Save, X } from "lucide-react";

export function GenericModule({ 
  title, 
  endpoint, 
  columns, 
  defaultValues 
}: { 
  title: string, 
  endpoint: string, 
  columns: { key: string, label: string, type: "text" | "number" | "boolean" | "list" }[],
  defaultValues: any 
}) {
  const [search, setSearch] = useState("");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});
  
  const queryClient = useQueryClient();
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiUrl = `${backendUrl}/api/admin/${endpoint}`;

  const { data, isLoading } = useQuery({
    queryKey: [endpoint, search],
    queryFn: async () => {
      const url = new URL(apiUrl);
      if (search) url.searchParams.append("query", search);
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error("Failed to fetch");
      return res.json();
    }
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: any) => {
      const method = editingItem ? "PUT" : "POST";
      const url = editingItem ? `${apiUrl}/${editingItem.id}` : apiUrl;
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to save");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint] });
      setIsDrawerOpen(false);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${apiUrl}/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [endpoint] });
    }
  });

  const openDrawer = (item: any = null) => {
    setEditingItem(item);
    setFormData(item || defaultValues);
    setIsDrawerOpen(true);
  };

  const items = data?.data || [];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
        <h2 className="text-xl font-bold tracking-tight">{title}</h2>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <button 
            onClick={() => openDrawer()}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add New
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-slate-50 dark:bg-slate-950 shadow-sm z-10">
            <tr>
              {columns.map(col => (
                <th key={col.key} className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {col.label}
                </th>
              ))}
              <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length + 1} className="px-6 py-12 text-center text-slate-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading data...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={columns.length + 1} className="px-6 py-12 text-center text-slate-500">
                  No records found.
                </td>
              </tr>
            ) : (
              items.map((item: any) => (
                <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  {columns.map(col => (
                    <td key={col.key} className="px-6 py-4 text-sm text-slate-700 dark:text-slate-300">
                      {col.type === 'boolean' 
                        ? (item[col.key] ? <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">Yes</span> : <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs font-medium">No</span>)
                        : col.type === 'list' 
                          ? (item[col.key] || []).join(", ")
                          : item[col.key]}
                    </td>
                  ))}
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => openDrawer(item)} className="p-2 text-slate-400 hover:text-blue-600 transition-colors">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => { if(confirm("Are you sure?")) deleteMutation.mutate(item.id) }} className="p-2 text-slate-400 hover:text-red-600 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Drawer */}
      {isDrawerOpen && (
        <>
          <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40" onClick={() => setIsDrawerOpen(false)} />
          <div className="fixed top-0 right-0 h-full w-[400px] bg-white dark:bg-slate-900 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right">
            <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold">{editingItem ? 'Edit' : 'Create'} {title}</h3>
              <button onClick={() => setIsDrawerOpen(false)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {columns.map(col => (
                <div key={col.key} className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">{col.label}</label>
                  {col.type === 'boolean' ? (
                    <div className="flex items-center mt-2">
                      <input 
                        type="checkbox" 
                        checked={!!formData[col.key]}
                        onChange={(e) => setFormData({...formData, [col.key]: e.target.checked})}
                        className="w-4 h-4 text-blue-600 rounded border-slate-300"
                      />
                      <span className="ml-2 text-sm text-slate-600 dark:text-slate-400">Enabled</span>
                    </div>
                  ) : col.type === 'list' ? (
                    <input 
                      type="text" 
                      value={(formData[col.key] || []).join(", ")}
                      onChange={(e) => setFormData({...formData, [col.key]: e.target.value.split(",").map((s:string) => s.trim()).filter(Boolean)})}
                      placeholder="Comma separated values"
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-md text-sm outline-none focus:border-blue-500"
                    />
                  ) : (
                    <input 
                      type={col.type === 'number' ? 'number' : 'text'} 
                      value={formData[col.key] || ''}
                      onChange={(e) => setFormData({...formData, [col.key]: col.type === 'number' ? Number(e.target.value) : e.target.value})}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-md text-sm outline-none focus:border-blue-500"
                    />
                  )}
                </div>
              ))}
            </div>
            
            <div className="p-6 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
              <button 
                onClick={() => saveMutation.mutate(formData)}
                disabled={saveMutation.isPending}
                className="w-full flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {saveMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Save className="w-4 h-4 mr-2" /> Save</>}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
