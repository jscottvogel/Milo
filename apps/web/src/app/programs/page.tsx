"use client";

import Link from "next/link";
import { ArrowRight, PieChart, AlertTriangle, Calendar, DollarSign, Users, Briefcase, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

import { useEffect, useState } from "react";
import { fetchPortfolio } from "@/lib/api";

export default function PortfolioView() {
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [resourceHeatmap, setResourceHeatmap] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPortfolio().then(data => {
      setPortfolio(data.portfolio || []);
      setResourceHeatmap(data.resource_heatmap || []);
      setIsLoading(false);
    }).catch(err => {
      console.error(err);
      setIsLoading(false);
    });
  }, []);

  const getRagColor = (rag: string) => {
    if (rag === 'green') return "bg-green-500/10 text-green-400 border-green-500/20";
    if (rag === 'amber') return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    return "bg-red-500/10 text-red-400 border-red-500/20";
  };

  const getRagDot = (rag: string) => {
    if (rag === 'green') return "bg-green-500";
    if (rag === 'amber') return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="p-6 h-full flex flex-col gap-8 overflow-y-auto custom-scrollbar">
      
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Portfolio Overview</h1>
          <p className="text-muted-foreground">High-level health metrics across all managed programs.</p>
        </div>
      </div>

      {/* Health Matrix */}
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <PieChart className="w-5 h-5 text-primary" />
          Health Matrix
        </h2>
        
        <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#0a0a0c] border-b border-white/10 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-6 py-4 font-medium">Program</th>
                  <th className="px-6 py-4 font-medium text-center">Health</th>
                  <th className="px-6 py-4 font-medium text-center">Milestones</th>
                  <th className="px-6 py-4 font-medium text-center">Overdue Tasks</th>
                  <th className="px-6 py-4 font-medium text-center">Open Risks</th>
                  <th className="px-6 py-4 font-medium text-center">Budget Variance</th>
                  <th className="px-6 py-4 font-medium text-center">Due Date</th>
                  <th className="px-6 py-4 font-medium text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-muted-foreground">
                      Loading portfolio data...
                    </td>
                  </tr>
                ) : portfolio.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-muted-foreground">
                      No programs found. Ask Milo to create one!
                    </td>
                  </tr>
                ) : portfolio.map(p => {
                  return (
                  <tr key={p.program_id} className="hover:bg-white/5 transition-colors group cursor-pointer">
                    <td className="px-6 py-4 font-medium text-white group-hover:text-primary transition-colors">
                      <Link href={`/programs/${p.program_id}`}>{p.name}</Link>
                    </td>
                    
                    <td className="px-6 py-4 text-center">
                      <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border", getRagColor(p.health))}>
                        <div className={cn("w-1.5 h-1.5 rounded-full", getRagDot(p.health))} />
                        <span className="capitalize">{p.health}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <span className="text-white">{p.milestone_count}</span>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <span className={cn("font-medium", p.overdue_task_count > 0 ? "text-red-400" : "text-green-400")}>
                        {p.overdue_task_count}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <AlertTriangle className={cn("w-4 h-4", p.open_risk_count > 0 ? "text-amber-400" : "text-green-400")} />
                        <span className="text-white">{p.open_risk_count}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <DollarSign className="w-4 h-4 text-muted-foreground" />
                        <span className={cn("font-medium", p.budget_variance_pct > 10 ? "text-red-400" : p.budget_variance_pct > 0 ? "text-amber-400" : "text-green-400")}>
                          {p.budget_variance_pct}%
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1.5 text-muted-foreground text-xs">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{p.due_date ? new Date(p.due_date).toLocaleDateString() : 'N/A'}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <Link href={`/programs/${p.program_id}`} className="inline-flex items-center justify-center p-2 rounded-lg hover:bg-white/10 text-muted-foreground hover:text-white transition-colors">
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </td>
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resource Heatmap */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            Resource Heatmap
          </h2>
          <div className="bg-[#111115] border border-white/10 rounded-xl p-6 flex flex-col gap-4 min-h-[250px]">
             {isLoading ? (
                <div className="text-center text-muted-foreground my-auto">Loading resources...</div>
             ) : resourceHeatmap.length === 0 ? (
                <div className="text-center text-muted-foreground my-auto">No resources assigned yet.</div>
             ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {resourceHeatmap.map(r => (
                    <div key={r.owner_name} className="flex flex-col p-4 bg-white/5 border border-white/5 rounded-lg">
                       <span className="text-sm text-muted-foreground mb-1">{r.owner_name}</span>
                       <div className="flex items-end justify-between">
                         <span className="text-2xl font-semibold text-white">{r.task_count}</span>
                         <span className="text-xs text-muted-foreground mb-1">active tasks</span>
                       </div>
                       {/* Basic bar visualization */}
                       <div className="w-full h-1.5 bg-white/5 rounded-full mt-3 overflow-hidden">
                         <div 
                           className={cn("h-full rounded-full", r.task_count > 10 ? "bg-red-500" : r.task_count > 5 ? "bg-amber-500" : "bg-primary")} 
                           style={{ width: `${Math.min((r.task_count / 15) * 100, 100)}%` }} 
                         />
                       </div>
                    </div>
                  ))}
                </div>
             )}
          </div>
        </div>

        {/* Financials Chart */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            Financials Overview
          </h2>
          <div className="bg-[#111115] border border-white/10 rounded-xl p-6 flex flex-col gap-4 min-h-[250px]">
             {isLoading ? (
                <div className="text-center text-muted-foreground my-auto">Loading financials...</div>
             ) : portfolio.filter(p => p.budget_variance_pct !== undefined && p.budget_variance_pct !== 0).length === 0 ? (
                <div className="text-center text-muted-foreground my-auto">No financial variance recorded.</div>
             ) : (
                <div className="flex flex-col gap-4">
                  {portfolio.filter(p => p.budget_variance_pct !== undefined && p.budget_variance_pct !== 0).map(p => (
                    <div key={`fin-${p.program_id}`} className="flex flex-col gap-2">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-white">{p.name}</span>
                        <span className={cn("font-medium", p.budget_variance_pct > 10 ? "text-red-400" : "text-amber-400")}>
                          +{p.budget_variance_pct}% Variance
                        </span>
                      </div>
                      <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden flex">
                        <div className="bg-primary h-full" style={{ width: '80%' }} />
                        <div className="bg-red-500 h-full" style={{ width: `${Math.min(p.budget_variance_pct, 20)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
             )}
          </div>
        </div>
      </div>

    </div>
  );
}
