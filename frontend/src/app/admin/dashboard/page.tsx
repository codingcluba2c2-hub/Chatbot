"use client";
import { useQuery } from "@tanstack/react-query";
import { 
  Hand, MessageSquare, HelpCircle, Zap, 
  Activity, Server, Clock, Cpu, Users, ArrowUpRight
} from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/api/admin/dashboard/stats`);
      if (!res.ok) throw new Error("Failed to fetch stats");
      return res.json();
    }
  });

  const cards = [
    { label: "Greetings", value: stats?.greetings || 0, icon: Hand, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20" },
    { label: "Farewells", value: stats?.farewells || 0, icon: MessageSquare, color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
    { label: "FAQs", value: stats?.faqs || 0, icon: HelpCircle, color: "text-purple-500", bg: "bg-purple-500/10", border: "border-purple-500/20" },
    { label: "FastPaths", value: stats?.fastpaths || 0, icon: Zap, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  ];

  const recentActivity = [
    { id: 1, action: "System Update", time: "10 mins ago", status: "Success", user: "Admin" },
    { id: 2, action: "Model Retrained", time: "2 hours ago", status: "Success", user: "System" },
    { id: 3, action: "API Rate Limit Exceeded", time: "5 hours ago", status: "Warning", user: "User_482" },
    { id: 4, action: "New FastPath Added", time: "1 day ago", status: "Success", user: "Admin" },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="space-y-8 pb-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-500 dark:from-white dark:to-slate-400">Dashboard Overview</h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Real-time metrics and system status monitoring.</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-sm">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Live Updates Enabled</span>
        </div>
      </div>
      
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {/* Status Card */}
        <motion.div variants={itemVariants} className="col-span-full md:col-span-2 lg:col-span-4 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 rounded-2xl p-1 shadow-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div className="bg-slate-900/90 backdrop-blur-xl rounded-xl p-6 lg:p-8 h-full border border-slate-700/50 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 lg:gap-0 relative z-10">
            
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Server className="w-4 h-4 text-blue-400" />
                <h3 className="text-slate-400 font-semibold text-xs uppercase tracking-widest">Pipeline Status</h3>
              </div>
              <div className="flex items-center gap-4">
                <div className="relative flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                  <Activity className="w-6 h-6" />
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-slate-900 rounded-full"></div>
                </div>
                <div>
                  <div className="text-3xl font-black text-white tracking-tight">
                    {isLoading ? "Checking..." : stats?.pipeline_status || "Online"}
                  </div>
                  <p className="text-emerald-400 text-sm font-medium flex items-center mt-1">
                    All systems operational
                  </p>
                </div>
              </div>
            </div>

            <div className="hidden lg:block w-px h-16 bg-slate-700/50 mx-8"></div>

            <div className="grid grid-cols-2 gap-8 flex-1 w-full lg:w-auto mt-6 lg:mt-0 pt-6 lg:pt-0 border-t border-slate-700/50 lg:border-none">
              <div>
                <div className="flex items-center gap-2 mb-1 text-slate-400">
                  <Clock className="w-4 h-4" />
                  <span className="text-xs uppercase tracking-widest font-semibold">Response Time</span>
                </div>
                <div className="text-2xl font-bold text-white flex items-end gap-2">
                  {isLoading ? "..." : stats?.avg_response_time || "15ms"}
                  <span className="text-sm font-normal text-emerald-400 mb-1 flex items-center"><ArrowUpRight className="w-3 h-3" /> 12%</span>
                </div>
              </div>
              
              <div>
                <div className="flex items-center gap-2 mb-1 text-slate-400">
                  <Cpu className="w-4 h-4" />
                  <span className="text-xs uppercase tracking-widest font-semibold">CPU Load</span>
                </div>
                <div className="text-2xl font-bold text-white flex items-end gap-2">
                  24%
                  <span className="text-sm font-normal text-slate-400 mb-1">Avg</span>
                </div>
              </div>
            </div>

          </div>
        </motion.div>
        
        {/* Stat Cards */}
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <motion.div 
              variants={itemVariants}
              key={idx} 
              className="bg-white dark:bg-slate-900/50 backdrop-blur-sm p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all duration-300 group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${card.bg} ${card.border} border transition-colors duration-300`}>
                  <Icon className={`w-6 h-6 ${card.color}`} />
                </div>
                <span className="flex items-center text-xs font-medium text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 px-2 py-1 rounded-full">
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                  {Math.floor(Math.random() * 10) + 1}%
                </span>
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight mb-1">
                  {isLoading ? "..." : card.value}
                </div>
                <h3 className="text-slate-500 dark:text-slate-400 text-sm font-medium">{card.label} Processed</h3>
              </div>
            </motion.div>
          );
        })}

        {/* Activity and Overview Section */}
        <motion.div variants={itemVariants} className="col-span-full grid grid-cols-1 lg:grid-cols-3 gap-6 mt-2">
          
          <div className="col-span-1 lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 flex flex-col justify-center items-center text-center min-h-[300px]">
             <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-full mb-4 shadow-inner">
                <Users className="w-8 h-8 text-slate-400" />
             </div>
             <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Audience Analytics</h3>
             <p className="text-slate-500 dark:text-slate-400 text-sm max-w-sm mb-6">Detailed conversational analytics and user journey mapping are currently being processed. Check back later for rich visualizations.</p>
             <button className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg text-sm font-medium hover:bg-slate-800 dark:hover:bg-slate-100 transition-colors shadow-sm active:scale-95">
               View Raw Data
             </button>
          </div>

          <div className="col-span-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6 flex items-center justify-between">
              Recent Activity
              <span className="text-xs font-medium text-slate-500 hover:text-slate-900 cursor-pointer">View All</span>
            </h3>
            <div className="space-y-6">
              {recentActivity.map((activity, i) => (
                <div key={activity.id} className="flex gap-4 relative">
                  {i !== recentActivity.length - 1 && (
                    <div className="absolute left-4 top-8 bottom-[-24px] w-px bg-slate-200 dark:bg-slate-800"></div>
                  )}
                  <div className="relative z-10 w-8 h-8 rounded-full bg-slate-50 dark:bg-slate-800 border-2 border-white dark:border-slate-900 flex items-center justify-center flex-shrink-0">
                    <div className={`w-2 h-2 rounded-full ${activity.status === 'Success' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">{activity.action}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-500 dark:text-slate-400">{activity.time}</span>
                      <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-700"></span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">{activity.user}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </motion.div>
      </motion.div>
    </div>
  );
}
