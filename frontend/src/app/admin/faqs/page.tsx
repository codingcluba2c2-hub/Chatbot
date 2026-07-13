"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Trash2, Edit2, Loader2, Save, X } from "lucide-react";

export default function FAQsPage() {
  const [search, setSearch] = useState("");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});
  
  const queryClient = useQueryClient();
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiUrl = `${backendUrl}/api/admin/faqs`;

  const { data, isLoading } = useQuery({
    queryKey: ["faqs", search],
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
      queryClient.invalidateQueries({ queryKey: ["faqs"] });
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
      queryClient.invalidateQueries({ queryKey: ["faqs"] });
    }
  });

  const openDrawer = (item: any = null) => {
    setEditingItem(item);
    if (item) {
      setFormData({
        ...item,
        aliasText: (item.aliases || []).join("\n")
      });
    } else {
      setFormData({
        question: "",
        answer: "",
        aliasText: "",
        enabled: true
      });
    }
    setIsDrawerOpen(true);
  };

  const handleSave = () => {
    const aliasList = (formData.aliasText || "").split("\n").map((s: string) => s.trim()).filter(Boolean);
    const payload = {
      question: formData.question,
      answer: formData.answer,
      aliases: aliasList,
      enabled: formData.enabled
    };
    saveMutation.mutate(payload);
  };

  const items = data?.data || [];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-950 rounded-t-xl">
        <h2 className="text-xl font-bold tracking-tight">FAQs</h2>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text"
              placeholder="Search FAQs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 min-w-[250px]"
            />
          </div>
          <button 
            onClick={() => openDrawer()}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add New
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto bg-slate-50 dark:bg-slate-900 p-6">
        <div className="bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Question</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Response</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Aliases</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Enabled</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                    Loading data...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    No records found.
                  </td>
                </tr>
              ) : (
                items.map((item: any) => (
                  <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-slate-900 dark:text-slate-100">
                      {item.question}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400 max-w-xs truncate">
                      {item.answer}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                      {item.aliases?.length || 0}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {item.enabled ? (
                        <span className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-medium border border-green-200">Enabled</span>
                      ) : (
                        <span className="px-2 py-1 bg-slate-50 text-slate-600 rounded text-xs font-medium border border-slate-200">Disabled</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => openDrawer(item)} className="p-2 text-slate-400 hover:text-blue-600 transition-colors cursor-pointer">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => { if(confirm("Are you sure?")) deleteMutation.mutate(item.id) }} className="p-2 text-slate-400 hover:text-red-600 transition-colors cursor-pointer">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex items-center justify-between text-sm text-slate-500">
            <div className="flex items-center">
              <span className="font-medium mr-4">Total: {items.length} records</span>
              <span>Rows per page: <select className="ml-2 bg-transparent outline-none cursor-pointer"><option>50</option></select></span>
            </div>
            <div className="flex items-center gap-2">
              <button className="px-3 py-1 border border-slate-200 dark:border-slate-700 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 cursor-pointer" disabled>Previous</button>
              <button className="px-3 py-1 border border-slate-200 dark:border-slate-700 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 cursor-pointer" disabled>Next</button>
            </div>
          </div>
        </div>
      </div>

      {/* Drawer */}
      {isDrawerOpen && (
        <>
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40" onClick={() => setIsDrawerOpen(false)} />
          <div className="fixed top-0 right-0 h-full w-[450px] bg-white dark:bg-slate-900 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right">
            <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-xl font-bold tracking-tight">{editingItem ? 'Edit FAQ' : 'Create FAQ'}</h3>
              <button onClick={() => setIsDrawerOpen(false)} className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Question <span className="text-red-500">*</span></label>
                <input 
                  type="text" 
                  value={formData.question || ''}
                  onChange={(e) => setFormData({...formData, question: e.target.value})}
                  placeholder="e.g., What are your opening hours?"
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 block">Answer <span className="text-red-500">*</span></label>
                <textarea 
                  value={formData.answer || ''}
                  onChange={(e) => setFormData({...formData, answer: e.target.value})}
                  rows={4}
                  placeholder="e.g., We are open from 9 AM to 5 PM."
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 block">Aliases (One per line)</label>
                <p className="text-xs text-slate-500 mb-2">Alternative ways users might ask this question.</p>
                <textarea 
                  value={formData.aliasText || ''}
                  onChange={(e) => setFormData({...formData, aliasText: e.target.value})}
                  rows={4}
                  placeholder="when do you open?&#10;business hours"
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Status</label>
                <select 
                  value={formData.enabled ? "enabled" : "disabled"}
                  onChange={(e) => setFormData({...formData, enabled: e.target.value === "enabled"})}
                  className="w-full px-3 py-2.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="enabled">Enabled</option>
                  <option value="disabled">Disabled</option>
                </select>
              </div>

            </div>
            
            <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 flex justify-end gap-3">
              <button 
                onClick={() => setIsDrawerOpen(false)}
                className="px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={handleSave}
                disabled={saveMutation.isPending}
                className="flex items-center px-6 py-2.5 bg-[#4F46E5] hover:bg-[#4338CA] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 shadow-sm shadow-indigo-200 cursor-pointer"
              >
                {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4 mr-2" /> Save FAQ</>}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
