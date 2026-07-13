import os

os.makedirs('frontend/src/app/admin/knowledge', exist_ok=True)
os.makedirs('frontend/src/components/admin/knowledge', exist_ok=True)

with open('frontend/src/app/admin/knowledge/page.tsx', 'w') as f:
    f.write('''\
"use client";
import React from 'react';
import { KnowledgeBaseModule } from '@/components/admin/knowledge/KnowledgeBaseModule';

export default function KnowledgeBasePage() {
  return (
    <div className="h-full w-full">
      <KnowledgeBaseModule />
    </div>
  );
}
''')

with open('frontend/src/components/admin/knowledge/KnowledgeBaseModule.tsx', 'w') as f:
    f.write('''\
import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Database, HardDrive, Trash2, CheckCircle, Clock, AlertTriangle, Search, Filter, RefreshCw, Layers } from 'lucide-react';
import { format } from 'date-fns';

// Minimal Custom UI for Knowledge Base
export const KnowledgeBaseModule = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/knowledge/documents`);
      if(res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll for status updates
    const interval = setInterval(fetchDocuments, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(10); // Fake initial progress
    
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", "general");
    formData.append("language", "en");
    
    try {
      setUploadProgress(40);
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/knowledge/upload`, {
        method: "POST",
        body: formData,
      });
      setUploadProgress(90);
      
      if (res.ok) {
        await fetchDocuments();
      }
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      setUploadProgress(100);
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        if(fileInputRef.current) fileInputRef.current.value = "";
      }, 500);
    }
  };

  const handleDelete = async (id: string) => {
    if(!confirm("Are you sure you want to delete this document and all its chunks?")) return;
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${backendUrl}/api/knowledge/documents/${id}`, { method: "DELETE" });
      fetchDocuments();
    } catch (e) {
      console.error(e);
    }
  };

  const stats = {
    total: documents.length,
    published: documents.filter(d => d.status === 'published').length,
    processing: documents.filter(d => d.status === 'processing').length,
    failed: documents.filter(d => d.status === 'failed').length,
    chunks: documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950">
      {/* Header & Upload */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Database className="text-blue-600" />
            Enterprise Knowledge Base
          </h1>
          <p className="text-sm text-slate-500 mt-1">Manage documents, chunks, and parsing pipelines for RAG.</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchDocuments} className="p-2 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 transition">
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
          
          <div className="relative">
             <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".pdf,.txt,.csv,.docx,.md" />
             <button 
               onClick={() => fileInputRef.current?.click()} 
               disabled={isUploading}
               className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50"
             >
               {isUploading ? (
                 <>
                   <RefreshCw size={18} className="animate-spin" /> Uploading {uploadProgress}%
                 </>
               ) : (
                 <>
                   <Upload size={18} /> Upload Document
                 </>
               )}
             </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Total Docs</h3>
            <FileText size={16} className="text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.total}</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Published</h3>
            <CheckCircle size={16} className="text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.published}</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Processing</h3>
            <Clock size={16} className="text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.processing}</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Failed</h3>
            <AlertTriangle size={16} className="text-rose-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.failed}</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Total Chunks</h3>
            <Layers size={16} className="text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stats.chunks}</p>
        </div>
      </div>

      {/* Main Table */}
      <div className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input type="text" placeholder="Search documents..." className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300">
            <Filter size={16} /> Filter
          </button>
        </div>
        
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 dark:bg-slate-950 sticky top-0 border-b border-slate-200 dark:border-slate-800 shadow-sm">
              <tr>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400">Name</th>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400">Category</th>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400">Status</th>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400">Chunks</th>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400">Size (KB)</th>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400">Uploaded</th>
                <th className="px-6 py-3 font-semibold text-slate-600 dark:text-slate-400 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {documents.map(doc => (
                <tr key={doc.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <FileText size={18} className="text-slate-400" />
                      <span className="font-medium text-blue-600 dark:text-blue-400 hover:underline cursor-pointer" onClick={() => setSelectedDoc(doc)}>
                        {doc.name}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs rounded-full capitalize">
                      {doc.category}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full capitalize ${
                      doc.status === 'published' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                      doc.status === 'processing' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                      doc.status === 'failed' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' :
                      'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                    }`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{doc.chunk_count}</td>
                  <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{doc.file_size ? Math.round(doc.file_size/1024) : 0}</td>
                  <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{format(new Date(doc.created_at * 1000), 'MMM d, yyyy')}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => handleDelete(doc.id)} className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 rounded transition">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              
              {documents.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    No documents uploaded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Detail Drawer (Simplified) */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex justify-end">
          <div className="w-[500px] h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
            <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-start">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 break-all">{selectedDoc.name}</h2>
                <p className="text-sm text-slate-500 mt-1">Uploaded {format(new Date(selectedDoc.created_at * 1000), 'MMM d, yyyy h:mm a')}</p>
              </div>
              <button onClick={() => setSelectedDoc(null)} className="text-slate-400 hover:text-slate-600">×</button>
            </div>
            <div className="p-6 flex-1 overflow-auto">
              <h3 className="font-semibold text-sm uppercase tracking-wider text-slate-500 mb-4">Metadata</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">ID</span><span className="font-mono text-xs">{selectedDoc.id}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Status</span><span className="capitalize font-medium">{selectedDoc.status}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Chunks</span><span>{selectedDoc.chunk_count}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Category</span><span className="capitalize">{selectedDoc.category}</span></div>
              </div>
              
              <hr className="my-6 border-slate-200 dark:border-slate-800" />
              
              {selectedDoc.error_message && (
                <div className="p-4 bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400 rounded-lg text-sm mb-6 border border-rose-200 dark:border-rose-800/50">
                  <span className="font-bold">Extraction Error:</span> {selectedDoc.error_message}
                </div>
              )}
              
              <h3 className="font-semibold text-sm uppercase tracking-wider text-slate-500 mb-4">Pipeline Trace</h3>
              <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                 {/* Visual trace of the pipeline processing */}
                 <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                   <div className="flex items-center justify-center w-5 h-5 rounded-full border border-white bg-slate-300 text-slate-500 shadow shrink-0 z-10" />
                   <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-2.5rem)] p-3 rounded-lg border border-slate-200 bg-white dark:bg-slate-900 shadow-sm">
                     <p className="text-sm font-semibold">File Validated</p>
                   </div>
                 </div>
                 <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                   <div className="flex items-center justify-center w-5 h-5 rounded-full border border-white bg-blue-500 text-white shadow shrink-0 z-10" />
                   <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-2.5rem)] p-3 rounded-lg border border-slate-200 bg-white dark:bg-slate-900 shadow-sm">
                     <p className="text-sm font-semibold">Text Extracted</p>
                   </div>
                 </div>
                 <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                   <div className="flex items-center justify-center w-5 h-5 rounded-full border border-white bg-purple-500 text-white shadow shrink-0 z-10" />
                   <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-2.5rem)] p-3 rounded-lg border border-slate-200 bg-white dark:bg-slate-900 shadow-sm">
                     <p className="text-sm font-semibold">Chunking Completed ({selectedDoc.chunk_count} chunks)</p>
                   </div>
                 </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
''')
