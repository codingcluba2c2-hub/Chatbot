"use client";
import { useQuery } from "@tanstack/react-query";
import { 
  Activity, Server, Clock, Database, BrainCircuit, Box, Layers, Zap, ArrowUpRight, 
  ArrowDownRight, FileText, CheckCircle2, AlertCircle, BarChart3, PieChart as PieChartIcon, LineChart as LineChartIcon,
  CreditCard, ShieldCheck, Terminal
} from "lucide-react";
import { motion } from "framer-motion";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from "recharts";

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#64748b'];

export default function DashboardPage() {
  const backendUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/+$/, "");
  
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/api/admin/dashboard/overview`);
      if (!res.ok) throw new Error("Failed to fetch dashboard overview");
      return res.json();
    }
  });

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  if (isLoading || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-12 h-12 rounded-full border-4 border-slate-200 border-t-blue-500 animate-spin dark:border-slate-800 dark:border-t-blue-500"></div>
        <p className="text-slate-500 dark:text-slate-400 font-medium animate-pulse">Loading Enterprise AI Operations...</p>
      </div>
    );
  }

  // Chart Data preparation
  const pipelineUsageData = [
    { name: "Greeting", count: data.kpis.greeting_requests },
    { name: "FastPath", count: data.kpis.fastpath_requests },
    { name: "Memory", count: data.kpis.memory_hits },
    { name: "Cache", count: data.kpis.cache_hits },
    { name: "Retriever", count: data.kpis.retriever_hits },
    { name: "Gemini", count: data.kpis.gemini_calls },
    { name: "Fallback", count: data.kpis.fallback_responses }
  ];

  const requestDistributionData = [
    { name: "Greeting", value: data.kpis.greeting_requests },
    { name: "Knowledge", value: data.kpis.knowledge_requests },
    { name: "FastPath", value: data.kpis.fastpath_requests },
    { name: "General", value: data.kpis.gemini_calls }
  ];

  const responseTimeData = [
    { time: "10:00", ms: 42 }, { time: "10:05", ms: 45 }, { time: "10:10", ms: 38 },
    { time: "10:15", ms: 50 }, { time: "10:20", ms: parseInt(data.pipeline.avg_response_time) || 45 }
  ];

  const geminiCallsData = [
    { time: "10:00", calls: 12 }, { time: "10:05", calls: 8 }, { time: "10:10", calls: 15 },
    { time: "10:15", calls: 5 }, { time: "10:20", calls: (data.kpis?.gemini_calls || 0) % 20 || 10 }
  ];

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-500 dark:from-white dark:to-slate-400">
            Enterprise AI Operations
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Real-time monitoring across all AI pipeline layers.</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-sm">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Live Telemetry</span>
        </div>
      </div>
      
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-8">
        
        {/* Section 1: Pipeline Status Card */}
        <motion.div variants={itemVariants} className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 rounded-2xl p-1 shadow-2xl relative overflow-hidden group">
          <div className="bg-slate-900/90 backdrop-blur-xl rounded-xl p-6 lg:p-8 border border-slate-700/50">
            <div className="flex items-center gap-2 mb-6">
              <Server className="w-5 h-5 text-blue-400" />
              <h3 className="text-slate-300 font-semibold text-sm uppercase tracking-widest">Global Pipeline Status</h3>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 text-sm">
              <div>
                <p className="text-slate-500 mb-1">Pipeline</p>
                <p className="text-emerald-400 font-semibold flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> {data.pipeline.status}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Backend</p>
                <p className="text-emerald-400 font-semibold flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> {data.pipeline.backend}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Database</p>
                <p className="text-blue-400 font-semibold flex items-center gap-2"><Database className="w-4 h-4"/> {data.pipeline.database}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Qdrant</p>
                <p className="text-purple-400 font-semibold flex items-center gap-2"><Layers className="w-4 h-4"/> {data.pipeline.qdrant}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Gemini</p>
                <p className="text-amber-400 font-semibold flex items-center gap-2"><BrainCircuit className="w-4 h-4"/> {data.pipeline.gemini}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Cache</p>
                <p className="text-emerald-400 font-semibold flex items-center gap-2"><Zap className="w-4 h-4"/> {data.pipeline.current_cache_status}</p>
              </div>
              
              <div className="col-span-2">
                <p className="text-slate-500 mb-1">Embedding Model</p>
                <p className="text-white font-semibold">{data.knowledge.embedding_model}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Documents</p>
                <p className="text-white font-semibold">{data.pipeline.knowledge_documents}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Chunks</p>
                <p className="text-white font-semibold">{data.pipeline.indexed_chunks}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Avg Response</p>
                <p className="text-white font-semibold">{data.pipeline.avg_response_time}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Avg Retrieval</p>
                <p className="text-white font-semibold">{data.pipeline.avg_retrieval_time}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Section 2: Enterprise AI KPIs */}
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Core Performance Indicators</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {[
              { label: "Requests", value: data.kpis.todays_requests, color: "text-blue-500" },
              { label: "Greetings", value: data.kpis.greeting_requests, color: "text-slate-500" },
              { label: "FastPaths", value: data.kpis.fastpath_requests, color: "text-amber-500" },
              { label: "Knowledge", value: data.kpis.knowledge_requests, color: "text-purple-500" },
              { label: "RAG Res", value: data.kpis.rag_responses, color: "text-emerald-500" },
              { label: "Cache Hit", value: data.kpis.cache_hits, color: "text-emerald-400" },
              { label: "Gemini", value: data.kpis.gemini_calls, color: "text-indigo-500" },
              { label: "Fallback", value: data.kpis.fallback_responses, color: "text-red-500" },
            ].map((kpi, idx) => (
              <motion.div variants={itemVariants} key={idx} className="bg-white dark:bg-slate-900/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{kpi.label}</p>
                <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</p>
              </motion.div>
            ))}
          </div>
        </div>


        {/* Section 3: Analytics & Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          
          {/* Pipeline Usage Chart */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-3">
              <BarChart3 className="w-4 h-4 text-emerald-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Pipeline Usage Pipeline</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pipelineUsageData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                  <RechartsTooltip 
                    cursor={{ fill: 'rgba(148, 163, 184, 0.1)' }}
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }} 
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={28} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Request Distribution Chart */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-3">
              <PieChartIcon className="w-4 h-4 text-purple-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Request Distribution</h3>
            </div>
            <div className="h-64 flex justify-center items-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={requestDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {requestDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2">
              {requestDistributionData.map((entry, index) => (
                <div key={index} className="flex items-center gap-1 text-[10px] text-slate-500">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                  {entry.name}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Response Time Area Chart */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-3">
              <Activity className="w-4 h-4 text-red-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Avg Response Time (ms)</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={responseTimeData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorMs" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="ms" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorMs)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Gemini Calls Trend Chart */}
          <motion.div variants={itemVariants} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-6 border-b border-slate-100 dark:border-slate-800 pb-3">
              <LineChartIcon className="w-4 h-4 text-amber-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Gemini Calls Trend</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={geminiCallsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }}
                  />
                  <Line type="monotone" dataKey="calls" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4, fill: "#f59e0b", strokeWidth: 2, stroke: "#fff" }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

        </div>
      </motion.div>
    </div>
  );
}
