"use client";
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Edit2, Trash2, Search, Save, X, BookOpen,
  RefreshCw, Phone, Building2,
  Calendar, MapPin, BookOpenCheck, Laptop, Briefcase, Users,
  Shield, Bot, Filter, CheckCircle2, XCircle, Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// ─── Types ────────────────────────────────────────────────────────────────────
interface FAQ {
  id: string;
  title: string;
  answer: string;
  aliases: string[];
  regex_pattern: string | null;
  parent_id: string | null;
  display_type: string;
  show_children_buttons: boolean;
  icon: string | null;
  status: string;
  created_at: number;
  updated_at: number;
}

interface ParentOption { id: string; title: string; }

// ─── Icon Picker Data ─────────────────────────────────────────────────────────
const ENTERPRISE_ICONS = [
  { value: 'Phone', label: 'Phone', icon: Phone },
  { value: 'Building2', label: 'Building', icon: Building2 },
  { value: 'Calendar', label: 'Calendar', icon: Calendar },
  { value: 'MapPin', label: 'Location', icon: MapPin },
  { value: 'BookOpenCheck', label: 'Book', icon: BookOpenCheck },
  { value: 'Laptop', label: 'Laptop', icon: Laptop },
  { value: 'Briefcase', label: 'Briefcase', icon: Briefcase },
  { value: 'Users', label: 'Users', icon: Users },
  { value: 'Shield', label: 'Shield', icon: Shield },
  { value: 'Bot', label: 'Bot', icon: Bot },
];

const ICON_MAP: Record<string, React.ComponentType<any>> = {
  Phone, Building2, Calendar, MapPin, BookOpenCheck, Laptop, Briefcase, Users, Shield, Bot
};

const DISPLAY_TYPES = ['Standard', 'Button Group', 'Accordion', 'Quick Links'];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function generateRegexFromAliases(aliases: string[]): string {
  const cleaned = aliases.map(a => a.trim().toLowerCase()).filter(Boolean);
  if (!cleaned.length) return '';
  const escaped = cleaned.map(a => a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  return `(?i)\\b(${escaped.join('|')})\\b`;
}

function relativeTime(ts: number): string {
  const diff = Math.floor((Date.now() / 1000) - ts);
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 172800) return 'Yesterday';
  return `${Math.floor(diff / 86400)}d ago`;
}

// ─── IconRenderer ─────────────────────────────────────────────────────────────
function FaqIcon({ name, className = "w-4 h-4" }: { name: string | null; className?: string }) {
  if (!name) return null;
  const Comp = ICON_MAP[name];
  return Comp ? <Comp className={className} /> : null;
}

// ─── Alias Tooltip ────────────────────────────────────────────────────────────
function AliasBadges({ aliases }: { aliases: string[] }) {
  const [show, setShow] = useState(false);
  if (!aliases?.length) return <span className="text-slate-400 text-xs italic">—</span>;
  const visible = aliases.slice(0, 2);
  const rest = aliases.slice(2);
  return (
    <div className="flex flex-wrap gap-1 items-center">
      {visible.map(a => (
        <span key={a} className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-[11px] rounded font-mono">{a}</span>
      ))}
      {rest.length > 0 && (
        <div className="relative">
          <button onClick={() => setShow(s => !s)} className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 text-[11px] rounded hover:bg-slate-200 transition-colors">
            +{rest.length} more
          </button>
          <AnimatePresence>
            {show && (
              <motion.div
                initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="absolute top-full left-0 mt-1 z-20 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl p-2 min-w-[160px] flex flex-wrap gap-1"
                onMouseLeave={() => setShow(false)}
              >
                {rest.map(a => (
                  <span key={a} className="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-[11px] rounded font-mono">{a}</span>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function FAQsPage() {
  const backendUrl = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_URL).replace(/\/+$/, "");
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterParent, setFilterParent] = useState<string>("all"); // "all" | "top" | "children"
  const [currentFaq, setCurrentFaq] = useState<FAQ | null>(null);

  // Modal form state
  const [aliasText, setAliasText] = useState("");
  const [generatedRegex, setGeneratedRegex] = useState("");
  const [selectedIcon, setSelectedIcon] = useState<string | null>(null);
  const [selectedParentId, setSelectedParentId] = useState<string | null>(null);
  const [displayType, setDisplayType] = useState("Standard");
  const [showChildButtons, setShowChildButtons] = useState(false);

  // ─── Queries ───────────────────────────────────────────────────────────────
  const { data: faqsData, isLoading } = useQuery({
    queryKey: ['admin-faqs'],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/api/admin/faqs?limit=2000`);
      if (!res.ok) throw new Error("Failed to fetch FAQs");
      return res.json();
    },
    staleTime: 30000,
  });

  const { data: parentOptionsData } = useQuery({
    queryKey: ['faq-parent-options'],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/api/admin/faqs/parent-options`);
      if (!res.ok) throw new Error("Failed to fetch parent options");
      return res.json();
    },
    staleTime: 30000,
  });

  const allFaqs: FAQ[] = faqsData?.data ?? [];
  const parentOptions: ParentOption[] = parentOptionsData?.data ?? [];

  // ─── Mutations ─────────────────────────────────────────────────────────────
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-faqs'] });

  const createMutation = useMutation({
    mutationFn: async (faq: any) => {
      const res = await fetch(`${backendUrl}/api/admin/faqs`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(faq) });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => { invalidate(); setIsEditing(false); },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const res = await fetch(`${backendUrl}/api/admin/faqs/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => { invalidate(); setIsEditing(false); },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${backendUrl}/api/admin/faqs/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: invalidate,
  });

  // ─── Modal helpers ─────────────────────────────────────────────────────────
  const openCreate = () => {
    setCurrentFaq(null);
    setAliasText('');
    setGeneratedRegex('');
    setSelectedIcon(null);
    setSelectedParentId(null);
    setDisplayType('Standard');
    setShowChildButtons(false);
    setIsEditing(true);
  };

  const openEdit = (faq: FAQ) => {
    setCurrentFaq(faq);
    const aliases = faq.aliases ?? [];
    setAliasText(aliases.join('\n'));
    setGeneratedRegex(faq.regex_pattern ?? generateRegexFromAliases(aliases));
    setSelectedIcon(faq.icon ?? null);
    setSelectedParentId(faq.parent_id ?? null);
    setDisplayType(faq.display_type ?? 'Standard');
    setShowChildButtons(faq.show_children_buttons ?? false);
    setIsEditing(true);
  };

  const refreshRegex = useCallback(() => {
    const aliases = aliasText.split('\n').map(a => a.trim().toLowerCase()).filter(Boolean);
    setGeneratedRegex(generateRegexFromAliases(aliases));
  }, [aliasText]);

  useEffect(() => { refreshRegex(); }, [aliasText, refreshRegex]);

  // ─── Save ──────────────────────────────────────────────────────────────────
  const handleSave = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const aliases = aliasText
      .split('\n')
      .map(a => a.trim().toLowerCase())
      .filter(Boolean)
      .filter((a, i, arr) => arr.indexOf(a) === i);

    const data = {
      title: String(fd.get('title') ?? '').trim(),
      answer: String(fd.get('answer') ?? '').trim(),
      aliases,
      regex_pattern: generatedRegex || null,
      parent_id: selectedParentId || null,
      display_type: displayType,
      show_children_buttons: showChildButtons,
      icon: selectedIcon,
      status: String(fd.get('status') ?? 'active'),
    };

    if (currentFaq?.id) {
      updateMutation.mutate({ id: currentFaq.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  // ─── Filtering & Search ────────────────────────────────────────────────────
  const parentIdToTitle = useMemo(() => {
    const m: Record<string, string> = {};
    allFaqs.forEach(f => { m[f.id] = f.title; });
    return m;
  }, [allFaqs]);

  const childrenCountMap = useMemo(() => {
    const m: Record<string, number> = {};
    allFaqs.forEach(f => {
      if (f.parent_id) m[f.parent_id] = (m[f.parent_id] ?? 0) + 1;
    });
    return m;
  }, [allFaqs]);

  const filtered = useMemo((): { faq: FAQ; depth: number }[] => {
    let items = allFaqs.filter(Boolean);

    // Search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter(f =>
        f.title?.toLowerCase().includes(q) ||
        f.answer?.toLowerCase().includes(q) ||
        f.aliases?.some(a => a.toLowerCase().includes(q)) ||
        (f.parent_id && parentIdToTitle[f.parent_id]?.toLowerCase().includes(q))
      );
    }

    // Status filter
    if (filterStatus !== 'all') items = items.filter(f => f.status === filterStatus);

    // Level filter
    if (filterParent === 'top') items = items.filter(f => !f.parent_id);
    else if (filterParent === 'children') items = items.filter(f => !!f.parent_id);

    // Build id→children lookup from ALL faqs (use full set for structure)
    const allByParent: Record<string, FAQ[]> = {};
    allFaqs.filter(Boolean).forEach(f => {
      const pid = f.parent_id ?? '__root__';
      if (!allByParent[pid]) allByParent[pid] = [];
      allByParent[pid].push(f);
    });

    // IDs that passed the filter
    const itemSet = new Set(items.map(f => f.id));

    // Recursively flatten tree: parent → children → grandchildren
    const result: { faq: FAQ; depth: number }[] = [];
    const visited = new Set<string>();

    function flattenNode(parentId: string | null, depth: number) {
      const key = parentId ?? '__root__';
      const kids = allByParent[key] ?? [];
      kids.forEach(f => {
        if (!f?.id || visited.has(f.id)) return;
        visited.add(f.id);
        if (itemSet.has(f.id)) {
          result.push({ faq: f, depth });
        }
        flattenNode(f.id, depth + 1);
      });
    }

    flattenNode(null, 0);
    return result;
  }, [allFaqs, searchQuery, filterStatus, filterParent, parentIdToTitle]);

  const isSaving = createMutation.isPending || updateMutation.isPending;

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 pb-16">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-500" />
            FAQ Manager
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">
            {allFaqs.length} total · {allFaqs.filter(f => !f.parent_id).length} top-level · {allFaqs.filter(f => !!f.parent_id).length} children
          </p>
        </div>
        <button
          id="new-faq-btn"
          onClick={openCreate}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-semibold text-sm transition-all shadow-md hover:shadow-lg"
        >
          <Plus size={18} /> New FAQ
        </button>
      </div>

      {/* ── Search + Filters ── */}
      <div className="space-y-3">
        <div className="flex gap-3">
          <div className="flex-1 flex items-center gap-2 bg-white dark:bg-slate-900 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <Search className="text-slate-400 shrink-0" size={17} />
            <input
              type="text"
              placeholder="Search by title, alias, answer, or parent…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="flex-1 bg-transparent outline-none text-slate-700 dark:text-slate-200 text-sm"
            />
            {searchQuery && <button onClick={() => setSearchQuery('')} className="text-slate-400 hover:text-slate-600"><X size={15} /></button>}
          </div>
          <button
            onClick={() => setShowFilters(s => !s)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${showFilters ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300' : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'} shadow-sm`}
          >
            <Filter size={16} /> Filters
          </button>
        </div>

        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              className="flex flex-wrap gap-3 overflow-hidden"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium">Status</span>
                {['all', 'active', 'inactive'].map(s => (
                  <button key={s} onClick={() => setFilterStatus(s)}
                    className={`px-3 py-1 text-xs rounded-full border font-medium transition-all ${filterStatus === s ? 'bg-blue-600 text-white border-blue-600' : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'}`}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium">Level</span>
                {[['all', 'All'], ['top', 'Top Level Only'], ['children', 'Children Only']].map(([val, label]) => (
                  <button key={val} onClick={() => setFilterParent(val)}
                    className={`px-3 py-1 text-xs rounded-full border font-medium transition-all ${filterParent === val ? 'bg-blue-600 text-white border-blue-600' : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'}`}>
                    {label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Table ── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider font-semibold">
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800">Title</th>
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 hidden lg:table-cell">Aliases</th>
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 hidden md:table-cell">Response</th>
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 hidden xl:table-cell">Parent</th>
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 hidden sm:table-cell">Status</th>
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 hidden xl:table-cell">Updated</th>
                <th className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr><td colSpan={7} className="text-center py-16">
                  <div className="flex flex-col items-center gap-3 text-slate-400">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm">Loading FAQs…</span>
                  </div>
                </td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-16">
                  <div className="flex flex-col items-center gap-3 text-slate-400">
                    <BookOpen className="w-10 h-10 opacity-40" />
                    <span className="text-sm">{searchQuery ? 'No results found' : 'No FAQs yet. Create your first one!'}</span>
                  </div>
                </td></tr>
              ) : (
                filtered.map(({ faq, depth }) => {
                  const childCount = childrenCountMap[faq.id] ?? 0;
                  const isTop = depth === 0;
                  const parentTitle = faq.parent_id ? (parentIdToTitle[faq.parent_id] ?? '—') : null;
                  const badgeLabel = isTop ? 'Top Level' : depth === 1 ? 'Child FAQ' : 'Sub-Child';
                  const badgeClass = isTop
                    ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400'
                    : depth === 1
                    ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400'
                    : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400';
                  return (
                    <tr key={faq.id} className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/30 transition-colors ${depth > 0 ? 'bg-slate-50/40 dark:bg-slate-800/10' : ''}`}>
                      {/* Title */}
                      <td className="px-6 py-4 max-w-[260px]">
                        <div className="flex items-center gap-2" style={{ paddingLeft: `${depth * 20}px` }}>
                          {depth > 0 && <div className="w-0.5 h-8 bg-slate-200 dark:bg-slate-700 shrink-0 rounded-full" />}
                          {faq.icon && (
                            <span className="text-blue-500 shrink-0"><FaqIcon name={faq.icon} /></span>
                          )}
                          <div>
                            <div className="font-semibold text-slate-900 dark:text-slate-100 text-sm">{faq.title}</div>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded uppercase tracking-wide ${badgeClass}`}>{badgeLabel}</span>
                              {childCount > 0 && (
                                <span className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 text-[10px] rounded">
                                  {childCount} {childCount === 1 ? 'child' : 'children'}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                      {/* Aliases */}
                      <td className="px-6 py-4 hidden lg:table-cell max-w-[200px]">
                        <AliasBadges aliases={faq.aliases} />
                      </td>
                      {/* Response */}
                      <td className="px-6 py-4 hidden md:table-cell max-w-[280px]">
                        {faq.answer ? (
                          <span className="text-sm text-slate-600 dark:text-slate-300 line-clamp-2">
                            {faq.answer.length > 100 ? faq.answer.slice(0, 100) + '…' : faq.answer}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400 italic">No answer</span>
                        )}
                      </td>
                      {/* Parent */}
                      <td className="px-6 py-4 hidden xl:table-cell">
                        {parentTitle ? (
                          <span className="text-sm text-slate-700 dark:text-slate-300 font-medium">{parentTitle}</span>
                        ) : (
                          <span className="text-slate-400 italic text-xs">—</span>
                        )}
                      </td>
                      {/* Status */}
                      <td className="px-6 py-4 hidden sm:table-cell">
                        {faq.status === 'active' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 text-xs font-semibold rounded-full">
                            <CheckCircle2 size={11} />Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-500 text-xs font-semibold rounded-full">
                            <XCircle size={11} />Inactive
                          </span>
                        )}
                      </td>
                      {/* Updated */}
                      <td className="px-6 py-4 hidden xl:table-cell">
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock size={11} />{relativeTime(faq.updated_at || faq.created_at)}
                        </span>
                      </td>
                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-1">
                          <button onClick={() => openEdit(faq)}
                            className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                            title="Edit">
                            <Edit2 size={15} />
                          </button>
                          <button onClick={() => { if (confirm(`Delete "${faq.title}"?`)) deleteMutation.mutate(faq.id); }}
                            className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="Delete">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────────── */}
      {/* ── CREATE / EDIT MODAL ── */}
      {/* ─────────────────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {isEditing && (
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-start justify-center p-4 pt-12 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.97, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: -8 }}
              transition={{ type: 'spring', stiffness: 320, damping: 28 }}
              className="bg-white dark:bg-slate-950 rounded-2xl shadow-2xl w-full max-w-2xl border border-slate-200 dark:border-slate-800 overflow-hidden mb-8"
            >
              {/* Modal Header */}
              <div className="flex justify-between items-center px-7 py-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-500" />
                  {currentFaq ? 'Edit FAQ' : 'New FAQ'}
                </h3>
                <button onClick={() => setIsEditing(false)} className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSave} className="px-7 py-6 space-y-6">

                {/* 1. Title */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1.5">
                    FAQ Title <span className="text-red-500">*</span>
                  </label>
                  <input
                    required name="title" defaultValue={currentFaq?.title}
                    placeholder="e.g. What services does Mobiloitte provide?"
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white text-[15px] outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all placeholder:text-slate-400"
                  />
                </div>

                {/* 2. Answer */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1.5">
                    Answer <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    name="answer" defaultValue={currentFaq?.answer} rows={5}
                    placeholder="Provide a clear, concise answer. Markdown formatting is supported."
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-y placeholder:text-slate-400"
                  />
                </div>

                {/* 3. Aliases */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">Aliases <span className="text-slate-400 font-normal">(Optional)</span></label>
                  <p className="text-xs text-slate-500 mb-2">One alias per line. Auto-trimmed, lowercased, and deduplicated.</p>
                  <textarea
                    value={aliasText}
                    onChange={e => setAliasText(e.target.value)}
                    rows={4}
                    placeholder={"what services\nservices\nour services\nmobiloitte services"}
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white text-sm font-mono outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none placeholder:text-slate-400"
                    style={{ height: '120px' }}
                  />
                </div>

                {/* 4. Auto Regex */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                      Auto-Generated Regex <span className="text-slate-400 font-normal">(Read Only)</span>
                    </label>
                    <button type="button" onClick={refreshRegex}
                      className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 transition-colors">
                      <RefreshCw size={12} /> Regenerate
                    </button>
                  </div>
                  <div className="w-full px-4 py-2.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-500 dark:text-slate-400 text-xs font-mono break-all min-h-[40px] select-all">
                    {generatedRegex || <span className="italic text-slate-400">No aliases — regex will be empty</span>}
                  </div>
                </div>

                {/* 5. Parent FAQ */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1.5">Parent FAQ <span className="text-slate-400 font-normal">(Optional)</span></label>
                  <select
                    value={selectedParentId ?? ''}
                    onChange={e => setSelectedParentId(e.target.value || null)}
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  >
                    <option value="">None (Top Level FAQ)</option>
                    {parentOptions
                      .filter(p => p.id !== currentFaq?.id)
                      .map(p => <option key={p.id} value={p.id}>{p.title}</option>)
                    }
                  </select>
                </div>

                {/* 6 + 7. Display Type + Show Child Buttons */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1.5">Display Type</label>
                    <select
                      value={displayType} onChange={e => setDisplayType(e.target.value)}
                      className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    >
                      {DISPLAY_TYPES.map(t => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1.5">Status</label>
                    <select
                      name="status" defaultValue={currentFaq?.status ?? 'active'}
                      className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>

                {/* Show children as buttons toggle */}
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox" checked={showChildButtons} onChange={e => setShowChildButtons(e.target.checked)}
                    className="mt-0.5 w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 shrink-0"
                  />
                  <div>
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 group-hover:text-blue-600 transition-colors">
                      Show Child FAQs as Buttons
                    </span>
                    <p className="text-xs text-slate-500 mt-0.5">
                      If enabled, all child FAQs will automatically appear as clickable buttons below this answer.
                    </p>
                  </div>
                </label>

                {/* 8. Icon Picker */}
                <div>
                  <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2">Icon <span className="text-slate-400 font-normal">(Optional)</span></label>
                  <div className="flex flex-wrap gap-2">
                    <button type="button" onClick={() => setSelectedIcon(null)}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${!selectedIcon ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'}`}>
                      None
                    </button>
                    {ENTERPRISE_ICONS.map(({ value, label, icon: Ico }) => (
                      <button type="button" key={value} onClick={() => setSelectedIcon(value)}
                        title={label}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${selectedIcon === value ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'}`}>
                        <Ico size={14} /> {label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                  <button type="button" onClick={() => setIsEditing(false)}
                    className="px-5 py-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors text-sm font-medium">
                    Cancel
                  </button>
                  <button type="submit" disabled={isSaving}
                    className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-xl flex items-center gap-2 font-semibold text-sm transition-all shadow-md hover:shadow-lg">
                    {isSaving ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Saving…</> : <><Save size={16} />Save FAQ</>}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
