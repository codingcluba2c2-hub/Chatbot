"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Trash2, Edit2, Loader2, Save, X, Hand, MessageSquare } from "lucide-react";

export default function ConversationsPage() {
  const [activeTab, setActiveTab] = useState<"greetings" | "farewells">("greetings");
  const [search, setSearch] = useState("");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});
  
  const queryClient = useQueryClient();
  const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/+$/, "");
  const apiUrl = `${backendUrl}/api/admin/${activeTab}`;

  const { data, isLoading } = useQuery({
    queryKey: [activeTab, search],
    queryFn: async () => {
      const url = apiUrl.startsWith("http") ? new URL(apiUrl) : new URL(apiUrl, window.location.origin);
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
      queryClient.invalidateQueries({ queryKey: [activeTab] });
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
      queryClient.invalidateQueries({ queryKey: [activeTab] });
    }
  });

  const openDrawer = (item: any = null) => {
    setEditingItem(item);
    if (item) {
      setFormData({
        ...item,
        aliasText: (item.alias || []).join("\n")
      });
    } else {
      setFormData({
        name: "",
        intent: activeTab === "greetings" ? "Greeting" : "Farewell",
        priority: 50,
        aliasText: "",
        regex: "",
        response: "",
        enabled: true
      });
    }
    setIsDrawerOpen(true);
  };

  const handleSave = () => {
    const aliases = (formData.aliasText || "").split("\n").map((s: string) => s.trim()).filter(Boolean);
    const payload = {
      name: formData.name,
      intent: formData.intent,
      priority: Number(formData.priority),
      alias: aliases,
      regex: formData.regex,
      response: formData.response,
      enabled: formData.enabled
    };
    saveMutation.mutate(payload);
  };

  const items = data?.data || [];

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Conversations</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Manage standard bot greetings and farewells.</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-slate-200/50 dark:bg-slate-800/50 p-1 rounded-xl w-fit">
        <button
          onClick={() => { setActiveTab("greetings"); setSearch(""); }}
          className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "greetings" 
              ? "bg-white dark:bg-slate-900 text-blue-600 shadow-sm" 
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
          }`}
        >
          <Hand className="w-4 h-4 mr-2" />
          Greetings
        </button>
        <button
          onClick={() => { setActiveTab("farewells"); setSearch(""); }}
          className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "farewells" 
              ? "bg-white dark:bg-slate-900 text-blue-600 shadow-sm" 
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
          }`}
        >
          <MessageSquare className="w-4 h-4 mr-2" />
          Farewells
        </button>
      </div>

      <div className="flex flex-col h-full bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-950 rounded-t-xl">
          <h2 className="text-lg font-semibold capitalize">{activeTab}</h2>
          <div className="flex gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input 
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 min-w-[250px]"
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
        <div className="flex-1 overflow-auto bg-slate-50 dark:bg-slate-900 p-4">
          <div className="bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Title</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Intent</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Response</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                      Loading data...
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                      No records found.
                    </td>
                  </tr>
                ) : (
                  items.map((item: any) => (
                    <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-medium text-slate-900 dark:text-slate-100">
                        {item.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">
                        <span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded text-xs">
                          {item.intent}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">{item.priority}</td>
                      <td className="px-6 py-4 text-sm text-slate-500 truncate max-w-xs">{item.response}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          item.enabled 
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" 
                            : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                        }`}>
                          {item.enabled ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button 
                            onClick={() => openDrawer(item)}
                            className="p-1.5 text-slate-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => {
                              if(confirm("Are you sure?")) deleteMutation.mutate(item.id);
                            }}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Drawer */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={() => setIsDrawerOpen(false)} />
          <div className="relative w-[400px] bg-white dark:bg-slate-900 h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300 border-l border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
              <h3 className="font-semibold text-lg">{editingItem ? "Edit" : "New"} {activeTab === "greetings" ? "Greeting" : "Farewell"}</h3>
              <button onClick={() => setIsDrawerOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">Name / Title</label>
                <input 
                  type="text" 
                  value={formData.name || ""} 
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-transparent outline-none focus:border-blue-500"
                  placeholder="e.g. Standard Hello"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">Intent</label>
                <input 
                  type="text" 
                  value={formData.intent || ""} 
                  onChange={e => setFormData({...formData, intent: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-transparent outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">Priority (1-100)</label>
                <input 
                  type="number" 
                  value={formData.priority || 50} 
                  onChange={e => setFormData({...formData, priority: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-transparent outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">Aliases (One per line)</label>
                <textarea 
                  rows={4}
                  value={formData.aliasText || ""} 
                  onChange={e => setFormData({...formData, aliasText: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-transparent outline-none focus:border-blue-500 resize-none"
                  placeholder="hi&#10;hello&#10;hey"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">Advanced Regex (Optional)</label>
                <input 
                  type="text" 
                  value={formData.regex || ""} 
                  onChange={e => setFormData({...formData, regex: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-transparent outline-none focus:border-blue-500 font-mono"
                  placeholder="(?i)\b(hi|hello)\b"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-slate-700 dark:text-slate-300">Bot Response</label>
                <textarea 
                  rows={4}
                  value={formData.response || ""} 
                  onChange={e => setFormData({...formData, response: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-transparent outline-none focus:border-blue-500 resize-none"
                  placeholder="Hello! How can I help you today?"
                />
              </div>

              <div className="flex items-center gap-3">
                <input 
                  type="checkbox" 
                  id="enabled"
                  checked={formData.enabled ?? true}
                  onChange={e => setFormData({...formData, enabled: e.target.checked})}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                />
                <label htmlFor="enabled" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Active / Enabled
                </label>
              </div>
            </div>

            <div className="p-6 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-end gap-3">
              <button 
                onClick={() => setIsDrawerOpen(false)}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={handleSave}
                disabled={saveMutation.isPending}
                className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
