"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  MessageSquare, 
  Hand, 
  HelpCircle, 
  Zap, 
  Link as LinkIcon, 
  Regex, 
  BrainCircuit,
  Wrench,
  Database,
  Search,
  Cpu,
  PanelRightClose,
  PanelRightOpen
} from "lucide-react";
import { useState } from "react";
import { DeveloperPreview } from "@/components/admin/DeveloperPreview";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { name: "Greetings", href: "/admin/greetings", icon: Hand },
  { name: "Farewells", href: "/admin/farewells", icon: MessageSquare },
  { name: "FAQs", href: "/admin/faqs", icon: HelpCircle },
  { name: "FastPaths", href: "/admin/fastpaths", icon: Zap },
  { name: "Knowledge Base", href: "/admin/knowledge", icon: Database },
  { name: "Knowledge Settings", href: "/admin/settings", icon: Wrench },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-200 dark:border-slate-800">
          <BrainCircuit className="w-6 h-6 text-blue-600 mr-2" />
          <h1 className="font-bold text-lg tracking-tight">AI Studio</h1>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={`flex items-center px-3 py-2.5 rounded-lg transition-colors ${
                  isActive 
                    ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-medium" 
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <Icon className={`w-5 h-5 mr-3 ${isActive ? "text-blue-600 dark:text-blue-400" : ""}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden transition-all duration-300">
        <header className="h-16 flex items-center justify-end px-6 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur">
          <button 
            onClick={() => setIsPreviewOpen(!isPreviewOpen)}
            className="flex items-center text-sm font-medium px-4 py-2 bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 rounded-lg shadow-sm hover:opacity-90 transition-opacity"
          >
            {isPreviewOpen ? <PanelRightClose className="w-4 h-4 mr-2" /> : <PanelRightOpen className="w-4 h-4 mr-2" />}
            Developer Preview
          </button>
        </header>
        
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>
      
      {/* Developer Preview Panel */}
      <div className={`w-80 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all duration-300 ${isPreviewOpen ? 'translate-x-0' : 'translate-x-full absolute right-0 h-full hidden'}`}>
        {isPreviewOpen && <DeveloperPreview onClose={() => setIsPreviewOpen(false)} />}
      </div>
    </div>
  );
}
