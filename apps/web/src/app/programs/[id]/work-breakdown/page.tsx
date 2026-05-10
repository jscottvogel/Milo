"use client";

import { useState, use } from "react";
import { ChevronRight, ChevronDown, Circle, CheckCircle2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { fetchProgram } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

type Status = 'not_started' | 'in_progress' | 'complete' | 'pending' | 'todo' | 'done';

const StatusIcon = ({ status }: { status: Status }) => {
  if (status === 'complete' || status === 'done') return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === 'in_progress' || status === 'pending') return <Clock className="w-4 h-4 text-amber-500" />;
  return <Circle className="w-4 h-4 text-muted-foreground" />;
};

const WorkItemRow = ({ item, level = 0 }: { item: any; level?: number }) => {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;
  
  // Calculate synthetic progress based on children if not available
  const progress = item.metadata_json?.progress || 0;

  return (
    <>
      <div className="flex items-center gap-4 py-3 px-4 hover:bg-white/5 border-b border-white/5 transition-colors group">
        <div 
          className="flex items-center gap-2 flex-1 min-w-0"
          style={{ paddingLeft: `${level * 1.5}rem` }}
        >
          {hasChildren ? (
            <button onClick={() => setExpanded(!expanded)} className="p-0.5 hover:bg-white/10 rounded shrink-0">
              {expanded ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
            </button>
          ) : (
            <div className="w-5 shrink-0" />
          )}
          
          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-white/10 text-muted-foreground shrink-0 w-24 text-center truncate">
            {item.item_type.replace('_', ' ')}
          </span>
          <span className="truncate font-medium group-hover:text-primary transition-colors cursor-pointer">{item.name}</span>
        </div>

        <div className="w-32 flex items-center gap-2 shrink-0">
          <div className="w-full bg-black/40 rounded-full h-1.5 overflow-hidden">
            <div className="bg-primary h-full rounded-full" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-xs text-muted-foreground w-8 text-right">{progress}%</span>
        </div>

        <div className="w-32 text-sm text-muted-foreground truncate shrink-0">{item.owner_name || 'Unassigned'}</div>
        
        <div className="w-24 text-sm text-muted-foreground shrink-0">{item.due_date ? new Date(item.due_date).toLocaleDateString() : 'No date'}</div>

        <div className="w-32 flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-2 px-2 py-1 rounded bg-white/5 border border-transparent text-xs w-full text-left">
            <StatusIcon status={item.status as Status} />
            <span className="capitalize text-muted-foreground truncate">{item.status.replace('_', ' ')}</span>
          </div>
        </div>
      </div>
      
      <AnimatePresence initial={false}>
        {expanded && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden border-l-2 border-white/5 ml-4"
          >
            {item.children.map((child: any) => (
              <WorkItemRow key={child.id} item={child} level={level + 1} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default function WorkBreakdown({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['program', resolvedParams.id],
    queryFn: () => fetchProgram(resolvedParams.id),
    refetchInterval: 15000,
  });

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading work breakdown...</div>;
  }

  if (error || !data) {
    return <div className="p-8 text-center text-red-400">Failed to load work breakdown.</div>;
  }

  return (
    <div className="bg-[#111115] border border-white/10 rounded-xl overflow-hidden flex flex-col h-full">
      {/* Toolbar */}
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-black/20 shrink-0">
        <h2 className="text-lg font-semibold text-white">Hierarchy</h2>
        <div className="flex gap-2">
          <button className="text-xs font-medium bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded transition-colors">Expand All</button>
          <button className="text-xs font-medium bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded transition-colors">Collapse All</button>
        </div>
      </div>

      {/* Table Header */}
      <div className="flex items-center gap-4 py-3 px-4 border-b border-white/10 text-xs font-medium text-muted-foreground uppercase tracking-wider bg-[#0a0a0c] shrink-0">
        <div className="flex-1">Item</div>
        <div className="w-32 shrink-0">Progress</div>
        <div className="w-32 shrink-0">Owner</div>
        <div className="w-24 shrink-0">Due Date</div>
        <div className="w-32 shrink-0">Status</div>
      </div>

      {/* Table Body */}
      <div className="flex-1 overflow-auto custom-scrollbar">
        {data.children && data.children.length > 0 ? (
          data.children.map((item: any) => (
            <WorkItemRow key={item.id} item={item} />
          ))
        ) : (
          <div className="p-8 text-center text-muted-foreground">No child items found. Add initiatives or projects to get started.</div>
        )}
      </div>
    </div>
  );
}
