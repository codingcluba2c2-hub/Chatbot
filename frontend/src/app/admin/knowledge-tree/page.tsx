"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Trash2, Edit2, Loader2, Save, X, Network, ListPlus } from "lucide-react";

export default function KnowledgeTreePage() {
  const [search, setSearch] = useState("");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});
  
  const queryClient = useQueryClient();
  const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/+$/, "");
  const apiUrl = `${backendUrl}/api/admin/knowledge_nodes`;
  const buttonsApiUrl = `${backendUrl}/api/admin/knowledge_buttons`;

  const { data, isLoading } = useQuery({
    queryKey: ["knowledge_nodes", search],
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
      queryClient.invalidateQueries({ queryKey: ["knowledge_nodes"] });
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
      queryClient.invalidateQueries({ queryKey: ["knowledge_nodes"] });
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
        title: "",
        slug: "",
        description: "",
        response_markdown: "",
        node_type: "standard",
        icon: "",
        image: "",
        priority: 1,
        sort_order: 1,
        status: "active",
        aliasText: ""
      });
    }
    setIsDrawerOpen(true);
  };

  const handleSave = () => {
    if (!formData.title?.trim()) {
      alert("Title is required");
      return;
    }
    const aliases = (formData.aliasText || "").split("\n").map((s: string) => s.trim()).filter(Boolean);
    const payload = {
      title: formData.title,
      slug: formData.slug || null,
      description: formData.description,
      response_markdown: formData.response_markdown,
      parent_id: formData.parent_id || null,
      node_type: formData.node_type || "standard",
      icon: formData.icon || null,
      image: formData.image || null,
      priority: Number(formData.priority) || 1,
      sort_order: Number(formData.sort_order) || 1,
      status: formData.status || "active",
      aliases: aliases
    };
    saveMutation.mutate(payload);
  };

  const items = data?.data || [];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800">
      {/* Header */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-950 rounded-t-xl">
        <h2 className="text-xl font-bold tracking-tight flex items-center">
          <Network className="w-5 h-5 mr-2 text-indigo-600" />
          Knowledge Tree
        </h2>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              suppressHydrationWarning
              type="text"
              placeholder="Search nodes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 min-w-[250px]"
            />
          </div>
          <button 
            suppressHydrationWarning
            onClick={() => openDrawer()}
            className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Node
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto bg-slate-50 dark:bg-slate-900 p-6">
        <div className="bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Title</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Parent Node</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                    Loading tree...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    No nodes found. Start building your knowledge tree.
                  </td>
                </tr>
              ) : (
                items.map((item: any) => (
                  <tr key={item.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-slate-900 dark:text-slate-100">
                      {item.title}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400 truncate max-w-[300px]" title={item.description}>
                      {item.description || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                      {item.parent_id ? (items.find((n: any) => n.id === item.parent_id)?.title || item.parent_id) : "None"}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${item.node_type === 'root' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' : 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                        {item.node_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {item.status === 'active' ? (
                        <span className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-medium border border-green-200">Active</span>
                      ) : (
                        <span className="px-2 py-1 bg-slate-50 text-slate-600 rounded text-xs font-medium border border-slate-200">Inactive</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {/* TODO: Link to manage buttons for this node */}
                      <button onClick={() => alert("Button management coming soon! For now use API.")} className="p-2 text-indigo-400 hover:text-indigo-600 transition-colors cursor-pointer mr-2" title="Manage Buttons">
                        <ListPlus className="w-4 h-4" />
                      </button>
                      <button onClick={() => openDrawer(item)} className="p-2 text-slate-400 hover:text-blue-600 transition-colors cursor-pointer" title="Edit Node">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => { if(confirm("Are you sure?")) deleteMutation.mutate(item.id) }} className="p-2 text-slate-400 hover:text-red-600 transition-colors cursor-pointer" title="Delete Node">
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
              <span className="font-medium mr-4">Total: {items.length} nodes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Drawer */}
      {isDrawerOpen && (
        <>
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40" onClick={() => setIsDrawerOpen(false)} />
          <div className="fixed top-0 right-0 h-full w-[500px] bg-white dark:bg-slate-900 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right">
            <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-xl font-bold tracking-tight">{editingItem ? 'Edit Node' : 'Create Node'}</h3>
              <button onClick={() => setIsDrawerOpen(false)} className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Title <span className="text-red-500">*</span></label>
                <input 
                  type="text" 
                  value={formData.title || ''}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  placeholder="e.g., Our Services"
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Description</label>
                <input 
                  type="text" 
                  value={formData.description || ''}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="e.g., Choose a service below."
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 block">Markdown Response</label>
                <textarea 
                  value={formData.response_markdown || ''}
                  onChange={(e) => setFormData({...formData, response_markdown: e.target.value})}
                  rows={4}
                  placeholder="## AI Solutions&#10;We provide..."
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Parent Node</label>
                  <select 
                    value={formData.parent_id || ''}
                    onChange={(e) => setFormData({...formData, parent_id: e.target.value})}
                    className="w-full px-3 py-2.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">None (Root Node)</option>
                    {items
                      .filter((n: any) => !editingItem || n.id !== editingItem.id)
                      .map((node: any) => (
                      <option key={node.id} value={node.id}>
                        {node.title}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Status</label>
                  <select 
                    value={formData.status || "active"}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="w-full px-3 py-2.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 block">Aliases (One per line)</label>
                <p className="text-xs text-slate-500 mb-2">Used for finding this node when user types loosely matching text.</p>
                <textarea 
                  value={formData.aliasText || ''}
                  onChange={(e) => setFormData({...formData, aliasText: e.target.value})}
                  rows={3}
                  placeholder="what do you do&#10;your services"
                  className="w-full px-3 py-2 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-lg text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono"
                />
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
                className="flex items-center px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 shadow-sm cursor-pointer"
              >
                {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4 mr-2" /> {editingItem ? 'Save Changes' : 'Create Node'}</>}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
