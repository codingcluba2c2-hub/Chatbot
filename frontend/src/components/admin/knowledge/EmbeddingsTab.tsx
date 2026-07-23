import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Copy, Download, Search, ChevronDown, ChevronUp, Play, Zap, RefreshCw } from 'lucide-react';

interface EmbeddingsTabProps {
  documentId: string;
}

export const EmbeddingsTab: React.FC<EmbeddingsTabProps> = ({ documentId }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  
  // Similarity Playground state
  const [playgroundQuery, setPlaygroundQuery] = useState('');
  const [playgroundResults, setPlaygroundResults] = useState<any[]>([]);
  const [playgroundLoading, setPlaygroundLoading] = useState(false);

  useEffect(() => {
    const fetchEmbeddings = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
        const res = await fetch(`${backendUrl}/api/knowledge/documents/${documentId}/embeddings`);
        if (!res.ok) {
          throw new Error('Failed to fetch embeddings');
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message || "No embedding vectors found.");
      } finally {
        setLoading(false);
      }
    };
    fetchEmbeddings();
  }, [documentId]);

  const testSimilarity = async () => {
    if (!playgroundQuery.trim()) return;
    setPlaygroundLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
      const res = await fetch(`${backendUrl}/api/knowledge/documents/${documentId}/retrieve?q=${encodeURIComponent(playgroundQuery)}&top_k=3`);
      if (res.ok) {
        const json = await res.json();
        setPlaygroundResults(json.results || []);
      }
    } catch (e) {
      console.error("Retrieval failed", e);
    } finally {
      setPlaygroundLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading embeddings...</div>;
  }

  if (error || !data || !data.embeddings || data.embeddings.length === 0) {
    return (
      <div className="p-8 text-center border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-800/30">
        <p className="text-slate-500">No embedding vectors found.</p>
        {error && <p className="text-rose-500 text-sm mt-2">{error}</p>}
      </div>
    );
  }

  const toggleRow = (chunkId: string) => {
    setExpandedRows(prev => ({
      ...prev,
      [chunkId]: !prev[chunkId]
    }));
  };

  const calculateStats = (vector: number[]) => {
    let min = Infinity;
    let max = -Infinity;
    let sum = 0;
    let sumSq = 0;
    let nonZero = 0;

    for (let i = 0; i < vector.length; i++) {
      const val = vector[i];
      if (val < min) min = val;
      if (val > max) max = val;
      sum += val;
      sumSq += val * val;
      if (Math.abs(val) > 0.000001) nonZero++;
    }

    const mean = sum / vector.length;
    let variance = 0;
    for (let i = 0; i < vector.length; i++) {
      variance += Math.pow(vector[i] - mean, 2);
    }
    const stdDev = Math.sqrt(variance / vector.length);
    const l2Norm = Math.sqrt(sumSq);

    // Top 20 absolute values
    const indexedValues = vector.map((v, i) => ({ index: i, value: v, abs: Math.abs(v) }));
    indexedValues.sort((a, b) => b.abs - a.abs);
    const top20Indices = new Set(indexedValues.slice(0, 20).map(v => v.index));

    return { min, max, mean, stdDev, l2Norm, nonZero, top20Indices };
  };

  const handleCopy = (vector: number[]) => {
    navigator.clipboard.writeText(JSON.stringify(vector));
  };

  const handleDownload = (format: 'json' | 'csv' | 'txt', chunk: any) => {
    let content = '';
    const mimeType = format === 'json' ? 'application/json' : 'text/plain';
    
    if (format === 'json') {
      content = JSON.stringify(chunk, null, 2);
    } else if (format === 'csv') {
      content = 'Index,Value\n' + chunk.vector.map((v: number, i: number) => `${i},${v}`).join('\n');
    } else {
      content = `Chunk #${chunk.chunk_number}\nChunk ID: ${chunk.chunk_id}\nVector Dimension: ${chunk.vector_dimension}\n\nVector Values:\n` + chunk.vector.join('\n');
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `embedding_chunk_${chunk.chunk_number}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredEmbeddings = data.embeddings.filter((chunk: any) => {
    const q = searchQuery.toLowerCase();
    if (!q) return true;
    return chunk.chunk_id.toLowerCase().includes(q) || 
           chunk.chunk_number.toString().includes(q) ||
           (q === 'embedding index');
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700/50 flex flex-col justify-center">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-0.5">Embedding Model</div>
          <div className="font-semibold text-sm truncate" title={data.embedding_model}>{data.embedding_model}</div>
        </div>
        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700/50 flex flex-col justify-center">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-0.5">Dimension</div>
          <div className="font-semibold text-sm">{data.dimension}</div>
        </div>
        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700/50 flex flex-col justify-center">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-0.5">Distance</div>
          <div className="font-semibold text-sm capitalize">{data.distance?.toLowerCase()}</div>
        </div>
        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700/50 flex flex-col justify-center">
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-0.5">Collection</div>
          <div className="font-semibold text-sm truncate" title={data.collection}>{data.collection}</div>
        </div>
      </div>

      {/* Similarity Playground */}
      <div className="border border-blue-200 dark:border-blue-900/50 rounded-xl overflow-hidden bg-blue-50/30 dark:bg-blue-900/10">
        <div className="p-4 border-b border-blue-100 dark:border-blue-900/30 bg-blue-50/50 dark:bg-blue-900/20">
          <p className="text-xs text-blue-700/70 dark:text-blue-300/70 mt-1">
            Test how queries match these vectors in real-time.
          </p>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex gap-2">
            <input 
              type="text" 
              value={playgroundQuery} 
              onChange={e => setPlaygroundQuery(e.target.value)} 
              onKeyDown={e => e.key === 'Enter' && testSimilarity()} 
              placeholder="e.g. 'How many earned leaves?'" 
              className="flex-1 px-3 py-2 text-sm border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
            <button 
              onClick={testSimilarity} 
              disabled={playgroundLoading || !playgroundQuery.trim()} 
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {playgroundLoading ? <RefreshCw size={16} className="animate-spin" /> : 'Generate & Test'}
            </button>
          </div>
          
          {playgroundResults.length > 0 && (
            <div className="space-y-3 mt-4 pt-4 border-t border-blue-100 dark:border-blue-900/30">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Top Matches</h4>
              {playgroundResults.map((res, i) => (
                <div key={i} className="flex flex-col p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Match for Chunk {res.payload.chunk_id ? `(ID: ${res.payload.chunk_id.substring(0, 8)}...)` : `#${i+1}`}
                    </span>
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-1 rounded">
                      Score: {res.score.toFixed(3)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                    {res.payload.content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 dark:text-slate-100">Vector Table ({data.total_chunks} Chunks)</h3>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <input 
          type="text" 
          placeholder="Search by Chunk Number or ID..." 
          className="w-full pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Table Wrapped in Overflow */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-x-auto bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left text-sm whitespace-nowrap min-w-[700px]">
          <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="px-4 py-3 font-semibold">Chunk</th>
              <th className="px-4 py-3 font-semibold">Min</th>
              <th className="px-4 py-3 font-semibold">Max</th>
              <th className="px-4 py-3 font-semibold">Mean</th>
              <th className="px-4 py-3 font-semibold">L2 Norm</th>
              <th className="px-4 py-3 font-semibold">Preview</th>
              <th className="px-4 py-3 font-semibold text-right sticky right-0 bg-slate-50 dark:bg-slate-800/80 z-10 shadow-[-10px_0_15px_-10px_rgba(0,0,0,0.1)]">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
            {filteredEmbeddings.map((chunk: any) => {
              const stats = calculateStats(chunk.vector);
              const isExpanded = expandedRows[chunk.chunk_id];
              
              // Generate histogram data
              const binCount = 20;
              const range = Math.max(Math.abs(stats.min), Math.abs(stats.max));
              const binSize = (range * 2) / binCount;
              const bins = Array.from({length: binCount}, (_, i) => ({
                name: (-range + (i * binSize) + (binSize/2)).toFixed(2),
                count: 0
              }));
              chunk.vector.forEach((v: number) => {
                let index = Math.floor((v + range) / binSize);
                if (index >= binCount) index = binCount - 1;
                if (index < 0) index = 0;
                bins[index].count++;
              });

              return (
                <React.Fragment key={chunk.chunk_id}>
                  <tr className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors group">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{chunk.chunk_number}</td>
                    <td className="px-4 py-3 text-slate-500 tabular-nums">{stats.min.toFixed(4)}</td>
                    <td className="px-4 py-3 text-slate-500 tabular-nums">{stats.max.toFixed(4)}</td>
                    <td className="px-4 py-3 text-slate-500 tabular-nums">{stats.mean.toFixed(4)}</td>
                    <td className="px-4 py-3 text-slate-500 tabular-nums font-semibold">{stats.l2Norm.toFixed(4)}</td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                      [{chunk.vector.slice(0, 3).map((v: number) => v.toFixed(3)).join(', ')}, ...]
                    </td>
                    <td className="px-4 py-3 text-right sticky right-0 bg-white dark:bg-slate-900 group-hover:bg-slate-50 dark:group-hover:bg-slate-800/80 z-10 shadow-[-10px_0_15px_-10px_rgba(0,0,0,0.05)] transition-colors">
                      <button 
                        onClick={() => toggleRow(chunk.chunk_id)}
                        className="inline-flex items-center justify-center px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 dark:text-blue-300 dark:bg-blue-900/40 dark:hover:bg-blue-900/60 rounded transition-colors"
                      >
                        View Vector {isExpanded ? <ChevronUp size={14} className="ml-1" /> : <ChevronDown size={14} className="ml-1" />}
                      </button>
                    </td>
                  </tr>
                  
                  {isExpanded && (
                    <tr>
                      <td colSpan={7} className="p-0 border-b-2 border-blue-500/20">
                        <div className="bg-slate-50/50 dark:bg-slate-900/50 p-4 md:p-6 border-b border-slate-200 dark:border-slate-800 shadow-inner">
                          
                          <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6">
                            <div>
                              <h4 className="font-bold text-slate-900 dark:text-slate-100 text-lg">Chunk {chunk.chunk_number}</h4>
                              <p className="text-xs text-slate-500 font-mono mt-1">ID: {chunk.chunk_id}</p>
                            </div>
                            
                            <div className="flex flex-wrap gap-2">
                              <button onClick={() => handleCopy(chunk.vector)} className="flex items-center px-3 py-1.5 text-xs font-medium border border-slate-300 dark:border-slate-600 rounded bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors shadow-sm">
                                <Copy size={14} className="mr-1.5" /> Copy Vector
                              </button>
                              <div className="flex bg-slate-200 dark:bg-slate-700 rounded p-0.5 shadow-sm">
                                <button onClick={() => handleDownload('json', chunk)} className="px-3 py-1 text-xs font-medium rounded hover:bg-white dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors">JSON</button>
                                <button onClick={() => handleDownload('csv', chunk)} className="px-3 py-1 text-xs font-medium rounded hover:bg-white dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors">CSV</button>
                                <button onClick={() => handleDownload('txt', chunk)} className="px-3 py-1 text-xs font-medium rounded hover:bg-white dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors">TXT</button>
                              </div>
                            </div>
                          </div>

                          {/* Chunk Content Preview */}
                          {chunk.content && (
                            <div className="mb-6 bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                              <h5 className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-2">Chunk Content</h5>
                              <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                                {chunk.content}
                              </p>
                            </div>
                          )}

                          {/* Stats Grid */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                            <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 block mb-1">Standard Deviation</span>
                              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{stats.stdDev.toFixed(6)}</span>
                            </div>
                            <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 block mb-1">L2 Norm</span>
                              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{stats.l2Norm.toFixed(6)}</span>
                            </div>
                            <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 block mb-1">Non-Zero Values</span>
                              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{stats.nonZero} / {chunk.vector_dimension}</span>
                            </div>
                            <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 block mb-1">Dimension</span>
                              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{chunk.vector_dimension}</span>
                            </div>
                          </div>

                          {/* Histogram */}
                          <div className="mb-6 h-56 border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 p-4 shadow-sm">
                            <h5 className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-4">Vector Distribution (Value Bins)</h5>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={bins} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                                <XAxis dataKey="name" tick={{fontSize: 10}} stroke="#94a3b8" axisLine={false} tickLine={false} />
                                <YAxis tick={{fontSize: 10}} stroke="#94a3b8" axisLine={false} tickLine={false} />
                                <Tooltip 
                                  cursor={{fill: 'rgba(0,0,0,0.05)'}}
                                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                />
                                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>

                          {/* Vector Values Table */}
                          <div>
                            <h5 className="text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-3 flex items-center justify-between">
                              <span>Complete 384-Dimension Vector</span>
                              <span className="text-blue-500 bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 rounded">Showing all values</span>
                            </h5>
                            <div className="h-80 overflow-y-auto border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 shadow-inner relative custom-scrollbar">
                              <table className="w-full text-left text-sm font-mono">
                                <thead className="bg-slate-100 dark:bg-slate-800/90 sticky top-0 z-10 border-b border-slate-200 dark:border-slate-700 shadow-sm backdrop-blur-sm">
                                  <tr>
                                    <th className="px-6 py-3 text-slate-500 font-semibold w-32 border-r border-slate-200 dark:border-slate-700">Index</th>
                                    <th className="px-6 py-3 text-slate-500 font-semibold">Value</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                                  {chunk.vector.map((val: number, idx: number) => {
                                    const isTop20 = stats.top20Indices.has(idx);
                                    return (
                                      <tr key={idx} className={`hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${isTop20 ? 'bg-blue-50/40 dark:bg-blue-900/10' : ''}`}>
                                        <td className="px-6 py-2.5 text-slate-400 border-r border-slate-100 dark:border-slate-700/50">{idx}</td>
                                        <td className={`px-6 py-2.5 flex items-center gap-3 ${isTop20 ? 'font-bold text-blue-700 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'}`}>
                                          <span className="w-24 inline-block">{val.toFixed(6)}</span>
                                          {isTop20 && (
                                            <span className="px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/60 text-[10px] uppercase tracking-wider font-semibold text-blue-700 dark:text-blue-300 shadow-sm">
                                              Top 20 Magnitude
                                            </span>
                                          )}
                                        </td>
                                      </tr>
                                    );
                                  })}
                                </tbody>
                              </table>
                            </div>
                          </div>

                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
            
            {filteredEmbeddings.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-slate-500 bg-white dark:bg-slate-900">
                  <Search className="mx-auto h-8 w-8 text-slate-300 mb-3" />
                  <p>No matching chunks found for your search.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
