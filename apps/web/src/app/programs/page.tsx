"use client";

import Link from "next/link";
import { ArrowRight, PieChart, AlertTriangle, Calendar, DollarSign, Users } from "lucide-react";
import { cn } from "@/lib/utils";

import { useEffect, useState } from "react";
import { fetchDashboard } from "@/lib/api";

export default function PortfolioView() {
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboard().then(data => {
      setPortfolio(data.root_items || []);
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
                  <th className="px-6 py-4 font-medium text-center">Overall</th>
                  <th className="px-6 py-4 font-medium text-center">Schedule</th>
                  <th className="px-6 py-4 font-medium text-center">Budget</th>
                  <th className="px-6 py-4 font-medium text-center">Risk</th>
                  <th className="px-6 py-4 font-medium text-center">Progress</th>
                  <th className="px-6 py-4 font-medium text-center">CSAT</th>
                  <th className="px-6 py-4 font-medium text-center">Next MS</th>
                  <th className="px-6 py-4 font-medium text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="px-6 py-8 text-center text-muted-foreground">
                      Loading portfolio data...
                    </td>
                  </tr>
                ) : portfolio.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-6 py-8 text-center text-muted-foreground">
                      No programs found. Ask Milo to create one!
                    </td>
                  </tr>
                ) : portfolio.map(p => {
                  const meta = p.metadata_json || {};
                  const rag = meta.rag || 'green';
                  const schedule = meta.schedule || 'green';
                  const budget = meta.budget || 'green';
                  const risk = meta.risk || 'green';
                  const csat = meta.csat || 100;
                  const progress = meta.progress || 0;
                  
                  // Compute a dummy milestone days from due_date
                  let nextMilestone = 0;
                  if (p.due_date) {
                    const diffTime = new Date(p.due_date).getTime() - new Date().getTime();
                    nextMilestone = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                  } else {
                    nextMilestone = 14; // default dummy
                  }

                  return (
                  <tr key={p.id} className="hover:bg-white/5 transition-colors group cursor-pointer">
                    <td className="px-6 py-4 font-medium text-white group-hover:text-primary transition-colors">
                      <Link href={`/programs/${p.id}`}>{p.name}</Link>
                    </td>
                    
                    {[rag, schedule, budget, risk].map((val, idx) => {
                      return (
                        <td key={idx} className="px-6 py-4 text-center">
                          <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border", getRagColor(val))}>
                            <div className={cn("w-1.5 h-1.5 rounded-full", getRagDot(val))} />
                            <span className="capitalize">{val}</span>
                          </div>
                        </td>
                      );
                    })}

                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 bg-white/5 rounded-full h-1.5 overflow-hidden">
                          <div className="bg-blue-500 h-full rounded-full" style={{ width: `${progress}%` }} />
                        </div>
                        <span className="text-xs text-muted-foreground w-8 text-right">{progress}%</span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className={cn("font-medium", csat > 80 ? "text-green-400" : csat > 50 ? "text-amber-400" : "text-red-400")}>
                          {csat}%
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className={cn("font-medium", nextMilestone < 0 ? "text-red-400" : "text-white")}>
                          {nextMilestone < 0 ? `${Math.abs(nextMilestone)}d late` : `in ${nextMilestone}d`}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <Link href={`/programs/${p.id}`} className="inline-flex items-center justify-center p-2 rounded-lg hover:bg-white/10 text-muted-foreground hover:text-white transition-colors">
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

    </div>
  );
}
