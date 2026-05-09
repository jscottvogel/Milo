import { CriticalPathDAG } from "@/components/programs/CriticalPathDAG";
import { BrainCircuit, Target, AlertTriangle, TrendingUp } from "lucide-react";

export default function ProgramOverview() {
  return (
    <div className="flex flex-col gap-6">
      
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Target className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium">Progress</span>
          </div>
          <div className="text-2xl font-bold">75%</div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="text-sm font-medium">Budget Variance</span>
          </div>
          <div className="text-2xl font-bold text-green-400">+2.4%</div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-medium">Open Risks</span>
          </div>
          <div className="text-2xl font-bold text-amber-400">2 High</div>
        </div>
        
        <div className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl p-4 flex flex-col gap-2 relative overflow-hidden group cursor-pointer">
          <div className="flex items-center gap-2 text-indigo-300">
            <BrainCircuit className="w-4 h-4" />
            <span className="text-sm font-medium">Milo Summary</span>
          </div>
          <p className="text-sm text-indigo-100/80 italic leading-snug line-clamp-2 relative z-10">
            "Auth migration is on track. Waiting on vendor approval for Phase 2."
          </p>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-[100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
        </div>
      </div>

      {/* Critical Path */}
      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold text-white">Critical Path</h2>
        <CriticalPathDAG />
      </div>

    </div>
  );
}
