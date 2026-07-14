import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Database, HardDrive, Trash2, CheckCircle, Clock, AlertTriangle, Search, Filter, RefreshCw, Layers } from 'lucide-react';
import { format } from 'date-fns';

export const KnowledgeBaseModule = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<"metadata" | "chunks" | "retrieval">("metadata");
  const [documentChunks, setDocumentChunks] = useState<any[]>([]);
  const [retrievalQuery, setRetrievalQuery] = useState("");
  const [retrievalResults, setRetrievalResults] = useState<any[]>([]);
  const [retrievalLoading, setRetrievalLoading] = useState(false);

  useEffect(() => {
    if (selectedDoc && activeTab === "chunks") {
       const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
       fetch(`${backendUrl}/api/knowledge/documents/${selectedDoc.id}/chunks`)
         .then(res => res.json())
         .then(setDocumentChunks)
         .catch(console.error);
    }
  }, [selectedDoc, activeTab]);

  const testRetrieval = async () => {
    if (!retrievalQuery) return;
    setRetrievalLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/knowledge/documents/${selectedDoc?.id}/retrieve?q=${encodeURIComponent(retrievalQuery)}`);
      const data = await res.json();
      setRetrievalResults(data.results || []);
    } catch(e) {
      console.error(e);
    } finally {
      setRetrievalLoading(false);
    }
  };
  const [isReprocessing, setIsReprocessing] = useState(false);

  const getProcessingPercentage = (status: string) => {
    switch (status) {
      case 'validating': return 10;
      case 'extracting': return 30;
      case 'chunking': return 60;
      case 'embedding': return 80;
      case 'indexing': return 95;
      case 'published': return 100;
      case 'failed': return 0;
      case 'processing': return 5;
      default: return 0;
    }
  };

  const handleReprocess = async () => {
    if (!selectedDoc) return;
    setIsReprocessing(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      await fetch(`${backendUrl}/api/knowledge/documents/${selectedDoc.id}/reprocess`, { method: "POST" });
      
      const res = await fetch(`${backendUrl}/api/knowledge/documents`);
      if(res.ok) {
        const docs = await res.json();
        setDocuments(docs);
        const updated = docs.find((d: any) => d.id === selectedDoc.id);
        if (updated) setSelectedDoc(updated);
      }
    } catch(e) {
      console.error(e);
    } finally {
      setIsReprocessing(false);
    }
  };

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
    
    // Poll every 3 seconds if any document is still processing
    const hasProcessing = documents.some(d => d.status !== 'published' && d.status !== 'failed');
    if (!hasProcessing) return;
    
    const interval = setInterval(async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${backendUrl}/api/knowledge/documents`);
        if(res.ok) {
          const data = await res.json();
          setDocuments(data);
          // If a document is selected, update it too
          if (selectedDoc) {
            const updated = data.find((d: any) => d.id === selectedDoc.id);
            if (updated && updated.status !== selectedDoc.status) {
              setSelectedDoc(updated);
            }
          }
        }
      } catch (e) {
        console.error(e);
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [documents.some(d => d.status !== 'published' && d.status !== 'failed'), selectedDoc?.id]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    
    setIsUploading(true);
    setUploadProgress(10);
    
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
                    <div className="relative overflow-hidden inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold w-[120px]">
                      {doc.status !== 'published' && doc.status !== 'failed' && (
                        <div className="absolute inset-0 bg-blue-100 dark:bg-blue-900/40">
                           <div 
                             className="h-full bg-blue-300 dark:bg-blue-600/60 transition-all duration-500 ease-out" 
                             style={{ width: `${getProcessingPercentage(doc.status)}%` }}
                           />
                        </div>
                      )}
                      {doc.status === 'published' && <div className="absolute inset-0 bg-emerald-100 dark:bg-emerald-900/30" />}
                      {doc.status === 'failed' && <div className="absolute inset-0 bg-rose-100 dark:bg-rose-900/30" />}
                      
                      <span className={`relative z-10 w-full text-center capitalize ${
                        doc.status === 'published' ? 'text-emerald-700 dark:text-emerald-400' :
                        doc.status === 'failed' ? 'text-rose-700 dark:text-rose-400' :
                        'text-blue-800 dark:text-blue-200 drop-shadow-sm'
                      }`}>
                        {doc.status}
                        {doc.status !== 'published' && doc.status !== 'failed' && ` ${getProcessingPercentage(doc.status)}%`}
                      </span>
                    </div>
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
      
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex justify-end">
          <div className="w-[500px] h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
            <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-start">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 break-all">{selectedDoc.name}</h2>
                <p className="text-sm text-slate-500 mt-1">Uploaded {format(new Date(selectedDoc.created_at * 1000), 'MMM d, yyyy h:mm a')}</p>
              </div>
              <button onClick={() => setSelectedDoc(null)} className="text-slate-400 hover:text-slate-600">x</button>
            </div>
            <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 pt-2 gap-4">
              <button onClick={() => setActiveTab('metadata')} className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'metadata' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>Metadata</button>
              <button onClick={() => setActiveTab('chunks')} className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'chunks' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>Chunks</button>
              <button onClick={() => setActiveTab('raw')} className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'raw' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>Raw Extracted Text</button>
              <button onClick={() => setActiveTab('retrieval')} className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'retrieval' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>Retrieval Test</button>
            </div>

            <div className="p-6 flex-1 overflow-auto">
              {activeTab === 'metadata' && (
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <h3 className="font-semibold text-xs uppercase tracking-wider text-slate-500">Document Profile</h3>
                      <button 
                        onClick={handleReprocess} 
                        disabled={isReprocessing || (selectedDoc.status !== 'published' && selectedDoc.status !== 'failed')}
                        className="flex items-center gap-1.5 px-2 py-1 bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 rounded text-xs font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <RefreshCw size={14} className={isReprocessing || (selectedDoc.status !== 'published' && selectedDoc.status !== 'failed') ? "animate-spin" : ""} /> Reprocess
                      </button>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-slate-500">ID</span><span className="font-mono text-xs">{selectedDoc.id}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Status</span><span className="capitalize font-medium">{selectedDoc.status}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Category</span><span className="capitalize">{selectedDoc.category}</span></div>
                    </div>
                  </div>
                  
                  {selectedDoc.processing_stats && (
                    <>
                      <div>
                        <h3 className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-3">Text Statistics</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between"><span className="text-slate-500">Characters</span><span>{selectedDoc.processing_stats.characters || 0}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Words</span><span>{selectedDoc.processing_stats.words || 0}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Paragraphs</span><span>{selectedDoc.processing_stats.paragraphs || 0}</span></div>
                        </div>
                      </div>
                      <div>
                        <h3 className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-3">Vector Details</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between"><span className="text-slate-500">Total Chunks</span><span>{selectedDoc.processing_stats.chunks_created || selectedDoc.chunk_count}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Embeddings Generated</span><span>{selectedDoc.processing_stats.embeddings_generated || 0}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Vectors Stored</span><span>{selectedDoc.processing_stats.vectors_stored || 0}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Total Time</span><span>{selectedDoc.processing_stats.total_processing_time}s</span></div>
                        </div>
                      </div>
                    </>
                  )}
                  
                  {selectedDoc.error_message && (
                    <div className="p-4 bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400 rounded-lg text-sm border border-rose-200 dark:border-rose-800/50">
                      <span className="font-bold">Error:</span> {selectedDoc.error_message}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'chunks' && (
                <div className="space-y-4">
                  {documentChunks.length === 0 ? (
                     <p className="text-sm text-slate-500">No chunks found or loading...</p>
                  ) : (
                    documentChunks.map(chunk => (
                      <div key={chunk.id} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                        <div className="flex justify-between items-center mb-3">
                           <div className="flex items-center gap-2">
                             <span className="text-xs font-bold px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 rounded">Chunk #{chunk.metadata.chunk_number}</span>
                             {chunk.metadata.page_number && <span className="text-xs px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300">Page {chunk.metadata.page_number}</span>}
                             {chunk.metadata.section && <span className="text-xs px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300">{chunk.metadata.section}</span>}
                           </div>
                           <span className="text-xs font-medium text-slate-500">{chunk.metadata.character_count} chars • ~{chunk.metadata.estimated_tokens} tokens</span>
                        </div>
                        
                        {(chunk.metadata.first_sentence || chunk.metadata.last_sentence) && (
                          <div className="mb-3 p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-100 dark:border-slate-700/50 space-y-2">
                            {chunk.metadata.first_sentence && (
                              <div className="text-xs">
                                <span className="font-semibold text-emerald-600 dark:text-emerald-400 mr-2">START:</span>
                                <span className="text-slate-600 dark:text-slate-400 italic">"{chunk.metadata.first_sentence}"</span>
                              </div>
                            )}
                            {chunk.metadata.last_sentence && (
                              <div className="text-xs">
                                <span className="font-semibold text-rose-600 dark:text-rose-400 mr-2">END:</span>
                                <span className="text-slate-600 dark:text-slate-400 italic">"{chunk.metadata.last_sentence}"</span>
                              </div>
                            )}
                          </div>
                        )}
                        
                        <div className="text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Full Content</div>
                        <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">{chunk.content}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
              
              {activeTab === 'raw' && (
                <div className="flex flex-col h-full bg-slate-900 rounded-xl overflow-hidden border border-slate-800">
                  <div className="p-3 bg-slate-800 text-slate-300 text-xs font-mono border-b border-slate-700 flex justify-between">
                    <span>Raw Extracted Text</span>
                    <span>{selectedDoc.raw_text ? selectedDoc.raw_text.length : 0} bytes</span>
                  </div>
                  <div className="flex-1 overflow-auto p-4">
                    <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap">
                      {selectedDoc.raw_text || "No raw text available for this document."}
                    </pre>
                  </div>
                </div>
              )}

              {activeTab === 'retrieval' && (
                <div className="flex flex-col h-full">
                  <div className="flex gap-2 mb-4">
                    <input type="text" value={retrievalQuery} onChange={e => setRetrievalQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && testRetrieval()} placeholder="Test retrieval... e.g. 'Company name?'" className="flex-1 px-3 py-2 text-sm border border-slate-200 dark:border-slate-800 rounded-lg bg-transparent focus:outline-none focus:border-blue-500" />
                    <button onClick={testRetrieval} disabled={retrievalLoading} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition disabled:opacity-50">Test</button>
                  </div>
                  <div className="flex-1 overflow-auto space-y-4">
                    {retrievalResults.map((res, i) => (
                       <div key={i} className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                         <div className="flex justify-between items-center mb-2">
                           <span className="text-xs font-semibold px-2 py-1 bg-blue-100 text-blue-700 rounded">Match #{i+1}</span>
                           <span className="text-xs font-semibold text-emerald-600">Score: {res.score.toFixed(3)}</span>
                         </div>
                         <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">{res.payload.content}</p>
                       </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
