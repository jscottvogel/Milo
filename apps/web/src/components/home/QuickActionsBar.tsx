"use client";

import { PlusCircle, FileText, AlertTriangle, Sparkles } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";

export function QuickActionsBar() {
  const { toggleRightRail, isRightRailOpen } = useAppStore();

  const handleAskMilo = () => {
    if (!isRightRailOpen) {
      toggleRightRail();
    }
    // In a real app we'd also focus the chat input or send a quick prefix
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-2 flex flex-wrap gap-2">
      <button className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <PlusCircle className="w-4 h-4 text-emerald-400" />
        New Task
      </button>
      <button className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <FileText className="w-4 h-4 text-blue-400" />
        Log Decision
      </button>
      <button className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <AlertTriangle className="w-4 h-4 text-red-400" />
        Flag Risk
      </button>
      <button 
        onClick={handleAskMilo}
        className="flex-1 min-w-[120px] bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        <Sparkles className="w-4 h-4" />
        Ask Milo
      </button>
    </div>
  );
}
