"use client";

import { AlertTriangle, FileText, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

const DUMMY_RISKS = [
  { id: "r1", title: "Key dependency delayed by 2 weeks", likelihood: 4, impact: 5, status: "open", mitigation: "Negotiate expedited delivery", owner: "Jane Doe" },
  { id: "r2", title: "API rate limits blocking stress test", likelihood: 5, impact: 3, status: "open", mitigation: "Request quota increase", owner: "John Smith" },
  { id: "r3", title: "Vendor SLA breach", likelihood: 2, impact: 4, status: "closed", mitigation: "Switched to secondary provider", owner: "Alice Johnson" },
];

const DUMMY_DECISIONS = [
  { id: "d1", title: "Select PostgreSQL over MongoDB", text: "Relational integrity required for financial transactions.", alternatives: "MongoDB, DynamoDB", date: "2026-05-01" },
  { id: "d2", title: "Use Tailwind CSS for v2 UI", text: "Team velocity and design system constraints favor utility classes.", alternatives: "Styled Components, CSS Modules", date: "2026-04-15" },
];

export default function RisksDecisions() {
  return (
    <div className="flex flex-col gap-8 h-full overflow-y-auto pr-2 custom-scrollbar">
      
      {/* Risks Section */}
      <div className="flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Risk Register
          </h2>
          <button className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
            <Plus className="w-4 h-4" />
            Add Risk
          </button>
        </div>

        <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#0a0a0c] border-b border-white/10 text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-medium">Risk</th>
                <th className="px-4 py-3 font-medium w-32">Severity</th>
                <th className="px-4 py-3 font-medium w-48">Status</th>
                <th className="px-4 py-3 font-medium">Mitigation</th>
                <th className="px-4 py-3 font-medium w-32">Owner</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {DUMMY_RISKS.map(risk => {
                const score = risk.likelihood * risk.impact;
                const severityColor = score >= 15 ? 'text-red-400 bg-red-500/10 border-red-500/20' : score >= 8 ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' : 'text-green-400 bg-green-500/10 border-green-500/20';
                
                return (
                  <tr key={risk.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-4 py-3 font-medium text-white">{risk.title}</td>
                    <td className="px-4 py-3">
                      <div className={cn("inline-flex items-center justify-center w-8 h-8 rounded-full border font-bold text-xs", severityColor)}>
                        {score}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn(
                        "px-2 py-1 rounded text-xs capitalize",
                        risk.status === 'open' ? "bg-amber-500/10 text-amber-500" : "bg-white/5 text-muted-foreground"
                      )}>
                        {risk.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground truncate max-w-[200px] hover:text-white transition-colors cursor-pointer" title={risk.mitigation}>
                      {risk.mitigation}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{risk.owner}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decisions Section */}
      <div className="flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-500" />
            Decision Log
          </h2>
          <button className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
            <Plus className="w-4 h-4" />
            Log Decision
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {DUMMY_DECISIONS.map(decision => (
            <div key={decision.id} className="bg-[#111115] border border-white/10 rounded-xl p-5 hover:border-white/20 transition-colors">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-white text-lg">{decision.title}</h3>
                <span className="text-xs text-muted-foreground bg-white/5 px-2 py-1 rounded">{decision.date}</span>
              </div>
              <p className="text-sm text-muted-foreground mb-4">{decision.text}</p>
              <div className="text-xs bg-black/20 p-2 rounded border border-white/5">
                <span className="font-medium text-white/70">Alternatives considered:</span> {decision.alternatives}
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
