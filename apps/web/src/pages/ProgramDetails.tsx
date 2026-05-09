import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { GanttChart } from '../components/GanttChart';
import { Activity, CheckCircle2, CircleDashed, Play, ArrowLeft, Loader2, AlertTriangle, LayoutList, CalendarRange, ChevronDown, ChevronRight, Hash, FileEdit, FolderOpen, Scale, LineChart, Users, Star, CheckSquare } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import clsx from 'clsx';

function getStatusIcon(status: string) {
  switch (status.toLowerCase()) {
    case 'active':
    case 'executing':
    case 'in_progress':
      return <Activity className="text-blue-400" size={16} />;
    case 'completed':
    case 'closed':
    case 'done':
      return <CheckCircle2 className="text-emerald-400" size={16} />;
    case 'initiating':
    case 'planning':
    case 'pending':
      return <Play className="text-amber-400" size={16} />;
    default:
      return <CircleDashed className="text-muted-foreground" size={16} />;
  }
}

function WorkItemNode({ item, depth = 0, showArchived = false }: { item: any, depth?: number, showArchived?: boolean }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const children = item.children || [];
  const visibleChildren = showArchived ? children : children.filter((c: any) => c.status !== 'archived');
  const hasChildren = visibleChildren.length > 0;

  if (!showArchived && item.status === 'archived') return null;

  return (
    <div className="flex flex-col">
      <div 
        className={clsx(
          "flex items-center justify-between p-3 border-b border-white/5 hover:bg-white/5 transition-colors group",
          depth === 0 ? "bg-black/20" : "",
          item.status === 'archived' && "opacity-60 grayscale"
        )}
        style={{ paddingLeft: `${depth * 1.5 + 1}rem` }}
      >
        <div className="flex items-center gap-3">
          {hasChildren ? (
            <button onClick={() => setIsExpanded(!isExpanded)} className="text-muted-foreground hover:text-white transition-colors">
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
          ) : (
            <div className="w-4" />
          )}
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-white/10 text-white border border-white/10 shrink-0">
             {item.item_type}
          </span>
          <div>
            <h4 className={clsx("font-medium transition-colors cursor-pointer", item.status === 'archived' ? 'text-gray-400 line-through' : 'text-white group-hover:text-primary')}>{item.name}</h4>
            {item.description && <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{item.description}</p>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {item.owner_name && (
            <span className="text-xs text-muted-foreground hidden sm:block">{item.owner_name}</span>
          )}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-black/30 text-xs shrink-0">
            {getStatusIcon(item.status)} <span className="capitalize">{item.status}</span>
          </div>
        </div>
      </div>
      
      {isExpanded && hasChildren && (
        <div className="flex flex-col">
          {visibleChildren.map((child: any) => (
            <WorkItemNode key={child.id} item={child} depth={depth + 1} showArchived={showArchived} />
          ))}
        </div>
      )}
    </div>
  );
}

export function ProgramDetails() {
  const { id } = useParams();
  const [program, setProgram] = useState<any>(null);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list');
  const [showArchived, setShowArchived] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        
        // Fetch Work Item Details
        const res = await fetch(`${API_URL}/v1/work_items/${id}`, {
          headers: {
            'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
          }
        });
        if (res.ok) {
          const data = await res.json();
          setProgram(data);
        }
        
        // Fetch Artifacts
        const artifactsRes = await fetch(`${API_URL}/v1/work_items/${id}/artifacts`, {
          headers: {
            'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
          }
        });
        if (artifactsRes.ok) {
          const artifactsData = await artifactsRes.json();
          setArtifacts(artifactsData);
        }
        
        // Fetch Validation Errors
        const valRes = await fetch(`${API_URL}/v1/work_items/validation-errors`, {
          headers: {
            'Authorization': 'Bearer dev_00000000-0000-0000-0000-000000000001'
          }
        });
        if (valRes.ok) {
          const valJson = await valRes.json();
          setValidationErrors(valJson.errors || []);
        }
        
      } catch (e) {
        console.error('Failed to fetch work item details or artifacts:', e);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchDetails();
    }
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-muted-foreground z-10 gap-4">
        <Loader2 size={32} className="animate-spin text-primary" />
        <span>Loading details...</span>
      </div>
    );
  }

  if (!program) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-muted-foreground z-10 gap-4">
        <span>Work Item not found.</span>
        <Link to="/programs" className="text-primary hover:underline flex items-center gap-2">
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full max-w-6xl mx-auto p-8 z-10 overflow-y-auto scrollbar-hide">
      <div className="flex items-center justify-between mb-6">
        <Link to="/programs" className="inline-flex items-center gap-2 text-muted-foreground hover:text-white transition-colors w-fit">
          <ArrowLeft size={20} /> Back to Dashboard
        </Link>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer text-sm text-muted-foreground hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={showArchived} 
              onChange={(e) => setShowArchived(e.target.checked)}
              className="rounded border-white/20 bg-black/50 text-primary focus:ring-primary focus:ring-offset-0"
            />
            Show Archived
          </label>
          <div className="flex items-center gap-1 bg-black/40 border border-white/10 rounded-lg p-1">
            <button 
              onClick={() => setViewMode('list')}
              className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors", viewMode === 'list' ? "bg-white/10 text-white" : "text-muted-foreground hover:text-white hover:bg-white/5")}
            >
              <LayoutList size={16} /> List
            </button>
            <button 
              onClick={() => setViewMode('timeline')}
              className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors", viewMode === 'timeline' ? "bg-white/10 text-white" : "text-muted-foreground hover:text-white hover:bg-white/5")}
            >
              <CalendarRange size={16} /> Timeline
            </button>
          </div>
        </div>
      </div>

      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-white/10 text-white border border-white/10">
              {program.item_type}
            </span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white mt-1">{program.name}</h2>
          {program.description && (
             <p className="text-muted-foreground mt-2 max-w-3xl">{program.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-black/40 border border-white/5 shadow-inner">
          {getStatusIcon(program.status)}
          <span className="text-sm font-medium text-gray-200 capitalize">{program.status}</span>
        </div>
      </div>

      {validationErrors.length > 0 && (
        <div className="mb-6 bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start gap-3 animate-fade-in">
          <AlertTriangle className="text-rose-400 shrink-0 mt-0.5" size={20} />
          <div>
            <h4 className="text-rose-400 font-semibold mb-1">⚠️ {validationErrors.length} hierarchy violations detected</h4>
            <ul className="list-disc list-inside text-sm text-rose-300/80 space-y-1">
              {validationErrors.slice(0, 3).map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
              {validationErrors.length > 3 && (
                <li className="italic text-rose-400/60 mt-1">...and {validationErrors.length - 3} more.</li>
              )}
            </ul>
          </div>
        </div>
      )}

      {viewMode === 'timeline' ? (
        <div className="animate-fade-in flex-1">
          <GanttChart program={program} />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-fade-in">
          {/* Left Column: Work Item Tree */}
          <div className="lg:col-span-2 space-y-8">
            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Hash className="text-primary" size={24} /> Hierarchy
              </h3>
              <div className="glass-card overflow-hidden">
                 <WorkItemNode item={program} depth={0} showArchived={showArchived} />
              </div>
            </section>
          </div>

          {/* Right Column: Risks & Details */}
          <div className="space-y-8">
            {program.metadata_json?.financials && Array.isArray(program.metadata_json.financials) && program.metadata_json.financials.length > 0 && (
              <section>
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <LineChart className="text-emerald-400" size={24} /> Financials
                </h3>
                <div className="glass-card p-5">
                  <div className="h-[250px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={program.metadata_json.financials} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                        <XAxis dataKey="period" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `$${value/1000}k`} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#111', borderColor: '#333', borderRadius: '8px', color: '#fff' }}
                          itemStyle={{ color: '#fff' }}
                          formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
                        />
                        <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
                        <Bar dataKey="budget" name="Budget" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={40} />
                        <Bar dataKey="actual" name="Actual" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={40} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  
                  {/* Summary */}
                  <div className="mt-6 pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider">Total Budget</span>
                      <p className="text-lg font-semibold text-emerald-400">
                        ${program.metadata_json.financials.reduce((acc: number, curr: any) => acc + (curr.budget || 0), 0).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider">Total Actuals</span>
                      <p className="text-lg font-semibold text-indigo-400">
                        ${program.metadata_json.financials.reduce((acc: number, curr: any) => acc + (curr.actual || 0), 0).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </section>
            )}

            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="text-rose-400" size={24} /> Risks
              </h3>
              {(!program.risks || program.risks.length === 0) ? (
                 <div className="glass-card border-dashed p-6 text-center text-muted-foreground">
                   No risks identified.
                 </div>
              ) : (
                <div className="space-y-4">
                  {program.risks.map((r: any) => (
                    <div key={r.id} className="glass-card p-5 border-l-2 border-l-rose-500/50 hover:border-rose-500/30 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                         <h4 className="font-medium text-white line-clamp-2">{r.title}</h4>
                      </div>
                      <div className="flex gap-4 text-xs text-muted-foreground mt-2">
                         <span>Likelihood: <strong className="text-gray-300">{r.likelihood}/5</strong></span>
                         <span>Impact: <strong className="text-gray-300">{r.impact}/5</strong></span>
                      </div>
                      <div className="mt-3 inline-block px-2 py-0.5 rounded bg-black/30 text-xs capitalize text-rose-300 border border-rose-500/20">
                        {r.status}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <FileEdit className="text-blue-400" size={24} /> Change Requests
              </h3>
              {(!program.change_requests || program.change_requests.length === 0) ? (
                 <div className="glass-card border-dashed p-6 text-center text-muted-foreground">
                   No change requests logged.
                 </div>
              ) : (
                <div className="space-y-4">
                  {program.change_requests.map((cr: any) => (
                    <div key={cr.id} className="glass-card p-5 border-l-2 border-l-blue-500/50 hover:border-blue-500/30 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                         <h4 className="font-medium text-white line-clamp-2">{cr.title}</h4>
                      </div>
                      <div className="text-sm text-muted-foreground mt-2 line-clamp-3">
                         {cr.description}
                      </div>
                      <div className="mt-3 inline-block px-2 py-0.5 rounded bg-black/30 text-xs capitalize text-blue-300 border border-blue-500/20">
                        {cr.status}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <CheckSquare className="text-cyan-400" size={24} /> Action Items
              </h3>
              {(!program.action_items || program.action_items.length === 0) ? (
                 <div className="glass-card border-dashed p-6 text-center text-muted-foreground">
                   No action items logged.
                 </div>
              ) : (
                <div className="space-y-3">
                  {program.action_items.map((ai: any) => (
                    <div key={ai.id} className={clsx(
                      "glass-card p-4 flex gap-3 transition-colors",
                      ai.status === 'met' ? "opacity-60" : "border-l-2 border-l-cyan-500/50 hover:border-cyan-500/30"
                    )}>
                      <div className="mt-0.5">
                        <CheckCircle2 className={ai.status === 'met' ? "text-emerald-500" : "text-muted-foreground"} size={18} />
                      </div>
                      <div className="flex-1">
                        <p className={clsx(
                          "text-sm",
                          ai.status === 'met' ? "text-muted-foreground line-through" : "text-white"
                        )}>
                          {ai.description}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs">
                          {ai.owner_name && (
                            <span className="text-cyan-300 font-medium">@{ai.owner_name}</span>
                          )}
                          {ai.due_date && (
                            <span className={clsx(
                              "flex items-center gap-1",
                              ai.status !== 'met' && new Date(ai.due_date) < new Date() ? "text-rose-400 border border-rose-500/30 rounded px-1" : "text-muted-foreground"
                            )}>
                              <CalendarRange size={12} />
                              {new Date(ai.due_date).toLocaleDateString()}
                            </span>
                          )}
                          <span className={clsx(
                            "px-1.5 py-0.5 rounded capitalize bg-black/30 border border-white/5",
                            ai.status === 'missed' ? "text-rose-400" : 
                            ai.status === 'met' ? "text-emerald-400" : "text-muted-foreground"
                          )}>
                            {ai.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Scale className="text-amber-400" size={24} /> Decisions
              </h3>
              {(!program.decisions || program.decisions.length === 0) ? (
                 <div className="glass-card border-dashed p-6 text-center text-muted-foreground">
                   No decisions logged.
                 </div>
              ) : (
                <div className="space-y-4">
                  {program.decisions.map((d: any) => (
                    <div key={d.id} className="glass-card p-5 border-l-2 border-l-amber-500/50 hover:border-amber-500/30 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                         <h4 className="font-medium text-white line-clamp-2">{d.title}</h4>
                      </div>
                      <div className="text-sm text-muted-foreground mt-2 line-clamp-3">
                         {d.decision_text}
                      </div>
                      {d.source_link && (
                        <div className="mt-3">
                          <a href={d.source_link} target="_blank" rel="noreferrer" className="text-xs text-amber-300 hover:text-amber-200 underline underline-offset-2 transition-colors">
                            View Source
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <Users className="text-pink-400" size={24} /> Stakeholders
              </h3>
              {(!program.stakeholders || program.stakeholders.length === 0) ? (
                 <div className="glass-card border-dashed p-6 text-center text-muted-foreground">
                   No stakeholders identified.
                 </div>
              ) : (
                <div className="space-y-4">
                  {program.stakeholders.map((sh: any) => (
                    <div key={sh.id} className="glass-card p-5 border-l-2 border-l-pink-500/50 hover:border-pink-500/30 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                         <div className="flex items-center gap-2">
                           <h4 className="font-medium text-white line-clamp-1">{sh.name}</h4>
                           {sh.role?.toLowerCase().includes('sponsor') && (
                             <span className="px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 text-[10px] uppercase font-bold flex items-center gap-1">
                               <Star size={10} /> Sponsor
                             </span>
                           )}
                         </div>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1 line-clamp-1">
                         {sh.role} {sh.email ? `• ${sh.email}` : ''}
                      </div>
                      {sh.notes && (
                        <div className="text-sm text-gray-400 mt-2 line-clamp-2 italic">
                          "{sh.notes}"
                        </div>
                      )}
                      <div className="mt-4 flex gap-2 flex-wrap">
                        {sh.satisfaction && (
                          <div className={clsx(
                            "px-2 py-1 rounded-md text-xs font-medium border flex items-center gap-1",
                            sh.satisfaction.toLowerCase().includes('satisf') || sh.satisfaction.toLowerCase() === 'high' ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" :
                            sh.satisfaction.toLowerCase().includes('dissatisf') || sh.satisfaction.toLowerCase() === 'low' ? "bg-rose-500/20 text-rose-300 border-rose-500/30" :
                            "bg-gray-500/20 text-gray-300 border-gray-500/30"
                          )}>
                             Satisfaction: <span className="capitalize">{sh.satisfaction}</span>
                          </div>
                        )}
                        <div className="px-2 py-1 rounded-md bg-black/30 text-xs text-gray-400 border border-white/5">
                           Influence: {sh.influence || 'Unknown'}
                        </div>
                        <div className="px-2 py-1 rounded-md bg-black/30 text-xs text-gray-400 border border-white/5">
                           Interest: {sh.interest || 'Unknown'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <FolderOpen className="text-purple-400" size={24} /> Artifacts
              </h3>
              {(!artifacts || artifacts.length === 0) ? (
                 <div className="glass-card border-dashed p-6 text-center text-muted-foreground flex flex-col items-center justify-center gap-2">
                   <span>No artifacts uploaded.</span>
                   <button className="px-3 py-1.5 mt-2 rounded bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors text-sm font-medium border border-purple-500/30">
                     Upload File
                   </button>
                 </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-end mb-2">
                    <button className="px-3 py-1.5 rounded bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors text-xs font-medium border border-purple-500/30">
                       Upload New File
                    </button>
                  </div>
                  {artifacts.map((a: any) => (
                    <div key={a.key} className="glass-card p-4 border-l-2 border-l-purple-500/50 hover:border-purple-500/30 transition-colors flex items-center justify-between">
                      <div className="flex flex-col">
                         <h4 className="font-medium text-white line-clamp-1">{a.filename}</h4>
                         <span className="text-xs text-muted-foreground mt-1">{(a.size / 1024).toFixed(1)} KB</span>
                      </div>
                      {a.url && (
                        <a href={a.url} target="_blank" rel="noreferrer" className="px-2 py-1 bg-white/5 hover:bg-white/10 rounded text-xs text-purple-300 transition-colors">
                          Download
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
