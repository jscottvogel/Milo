"use client";

import { useState } from "react";
import { Users, Plus, Mail } from "lucide-react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from "recharts";
import { cn } from "@/lib/utils";

const DUMMY_STAKEHOLDERS = [
  { id: "s1", name: "Jane Executive", role: "Sponsor", email: "jane@example.com", influence: 9, interest: 8, satisfaction: 85, notes: "Needs weekly brief." },
  { id: "s2", name: "Bob Director", role: "VP Eng", email: "bob@example.com", influence: 8, interest: 4, satisfaction: 60, notes: "Concerned about architecture." },
  { id: "s3", name: "Alice Manager", role: "Project Lead", email: "alice@example.com", influence: 5, interest: 9, satisfaction: 95, notes: "Daily contact." },
  { id: "s4", name: "Tom Ops", role: "Support", email: "tom@example.com", influence: 2, interest: 7, satisfaction: 75, notes: "Needs training materials." },
];

export default function Stakeholders() {
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'Sponsor' });

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate API call to /stakeholders/invite
    console.log("Inviting:", inviteForm);
    setIsInviteModalOpen(false);
    setInviteForm({ email: '', role: 'Sponsor' });
  };

  const chartData = DUMMY_STAKEHOLDERS.map(s => ({
    x: s.interest, // 1-10 scale
    y: s.influence, // 1-10 scale
    name: s.name,
    satisfaction: s.satisfaction
  }));

  const getHML = (val: number) => val >= 7 ? 'High' : val >= 4 ? 'Med' : 'Low';

  return (
    <div className="flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Users className="w-5 h-5 text-indigo-500" />
          Stakeholders
        </h2>
        <button onClick={() => setIsInviteModalOpen(true)} className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
          <Plus className="w-4 h-4" />
          Invite Stakeholder
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Quadrant Matrix */}
        <div className="lg:col-span-1 bg-[#111115] border border-white/10 rounded-xl p-6 flex flex-col gap-4">
          <h3 className="font-semibold text-white">Influence / Interest Matrix</h3>
          <div className="flex-1 h-[300px] relative">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis type="number" dataKey="x" name="Interest" domain={[0, 10]} ticks={[0, 5, 10]} stroke="#888" tickLine={false} />
                <YAxis type="number" dataKey="y" name="Influence" domain={[0, 10]} ticks={[0, 5, 10]} stroke="#888" tickLine={false} />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }} 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-[#111115] border border-white/20 p-2 rounded-lg text-sm shadow-xl">
                          <p className="font-bold text-white">{data.name}</p>
                          <p className="text-muted-foreground">Influence: {data.y}</p>
                          <p className="text-muted-foreground">Interest: {data.x}</p>
                          <p className="text-muted-foreground">Satisfaction: {data.satisfaction}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <ReferenceLine x={5} stroke="#ffffff20" />
                <ReferenceLine y={5} stroke="#ffffff20" />
                
                {/* Quadrant Labels */}
                <text x="75%" y="10%" fill="#888888" textAnchor="middle" opacity={0.5} fontSize={12}>Manage Closely</text>
                <text x="25%" y="10%" fill="#888888" textAnchor="middle" opacity={0.5} fontSize={12}>Keep Satisfied</text>
                <text x="75%" y="90%" fill="#888888" textAnchor="middle" opacity={0.5} fontSize={12}>Keep Informed</text>
                <text x="25%" y="90%" fill="#888888" textAnchor="middle" opacity={0.5} fontSize={12}>Monitor</text>

                <Scatter data={chartData} name="Stakeholders">
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.satisfaction > 80 ? '#10b981' : entry.satisfaction > 60 ? '#f59e0b' : '#ef4444'} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Stakeholder Table */}
        <div className="lg:col-span-2 bg-[#111115] border border-white/10 rounded-xl overflow-hidden flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#0a0a0c] border-b border-white/10 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Contact</th>
                  <th className="px-4 py-3 font-medium text-center">Influence</th>
                  <th className="px-4 py-3 font-medium text-center">Interest</th>
                  <th className="px-4 py-3 font-medium text-center">CSAT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {DUMMY_STAKEHOLDERS.map(s => (
                  <tr key={s.id} className="hover:bg-white/5 transition-colors cursor-pointer">
                    <td className="px-4 py-4 font-medium text-white">{s.name}</td>
                    <td className="px-4 py-4 text-muted-foreground">{s.role}</td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2 text-muted-foreground hover:text-white transition-colors">
                        <Mail className="w-4 h-4" />
                        <span className="truncate max-w-[120px]">{s.email}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className={cn("px-2 py-1 rounded text-xs", 
                        s.influence >= 7 ? "bg-red-500/10 text-red-400" : s.influence >= 4 ? "bg-amber-500/10 text-amber-400" : "bg-green-500/10 text-green-400"
                      )}>{getHML(s.influence)}</span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className={cn("px-2 py-1 rounded text-xs", 
                        s.interest >= 7 ? "bg-blue-500/10 text-blue-400" : s.interest >= 4 ? "bg-teal-500/10 text-teal-400" : "bg-slate-500/10 text-slate-400"
                      )}>{getHML(s.interest)}</span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className={cn("w-2 h-2 rounded-full", s.satisfaction > 80 ? 'bg-green-500' : s.satisfaction > 60 ? 'bg-amber-500' : 'bg-red-500')} />
                        <span className="text-white font-medium">{s.satisfaction}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {isInviteModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-[#121218] border border-white/10 rounded-xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Invite Stakeholder</h3>
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white/80 mb-1">Email Address</label>
                <input 
                  type="email" 
                  required
                  className="w-full bg-[#0a0a0c] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
                  value={inviteForm.email}
                  onChange={e => setInviteForm({...inviteForm, email: e.target.value})}
                  placeholder="name@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/80 mb-1">Role</label>
                <input 
                  type="text" 
                  required
                  className="w-full bg-[#0a0a0c] border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-500"
                  value={inviteForm.role}
                  onChange={e => setInviteForm({...inviteForm, role: e.target.value})}
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setIsInviteModalOpen(false)} className="px-4 py-2 text-white/60 hover:text-white transition-colors">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium">Send Invite</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
