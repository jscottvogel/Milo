"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown, Circle, CheckCircle2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

type Status = 'not_started' | 'in_progress' | 'complete';
type ItemType = 'Objective' | 'Outcome' | 'KR' | 'Initiative' | 'Project' | 'Workstream' | 'Milestone' | 'Task';

interface WorkItem {
  id: string;
  name: string;
  type: ItemType;
  owner: string;
  status: Status;
  progress: number;
  dueDate: string;
  children?: WorkItem[];
}

const DUMMY_DATA: WorkItem[] = [
  {
    id: "obj-1",
    name: "Migrate Platform to Cloud",
    type: "Objective",
    owner: "Jane Doe",
    status: "in_progress",
    progress: 45,
    dueDate: "2026-12-31",
    children: [
      {
        id: "kr-1",
        name: "100% of user traffic served from AWS",
        type: "KR",
        owner: "John Smith",
        status: "in_progress",
        progress: 60,
        dueDate: "2026-10-15",
        children: [
          {
            id: "proj-1",
            name: "Database Migration",
            type: "Project",
            owner: "Alice Johnson",
            status: "in_progress",
            progress: 80,
            dueDate: "2026-08-01",
            children: [
              { id: "task-1", name: "Export on-prem data", type: "Task", owner: "Alice Johnson", status: "complete", progress: 100, dueDate: "2026-06-15" },
              { id: "task-2", name: "Import to RDS", type: "Task", owner: "Bob Wilson", status: "in_progress", progress: 50, dueDate: "2026-07-20" },
            ]
          }
        ]
      }
    ]
  }
];

const StatusIcon = ({ status }: { status: Status }) => {
  if (status === 'complete') return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === 'in_progress') return <Clock className="w-4 h-4 text-amber-500" />;
  return <Circle className="w-4 h-4 text-muted-foreground" />;
};

const WorkItemRow = ({ item, level = 0 }: { item: WorkItem; level?: number }) => {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = item.children && item.children.length > 0;

  return (
    <>
      <div className="flex items-center gap-4 py-3 px-4 hover:bg-white/5 border-b border-white/5 transition-colors group">
        <div 
          className="flex items-center gap-2 flex-1 min-w-0"
          style={{ paddingLeft: `${level * 1.5}rem` }}
        >
          {hasChildren ? (
            <button onClick={() => setExpanded(!expanded)} className="p-0.5 hover:bg-white/10 rounded">
              {expanded ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
            </button>
          ) : (
            <div className="w-5" />
          )}
          
          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-white/10 text-muted-foreground shrink-0 w-20 text-center">
            {item.type}
          </span>
          <span className="truncate font-medium group-hover:text-primary transition-colors cursor-pointer">{item.name}</span>
        </div>

        <div className="w-32 flex items-center gap-2">
          <div className="w-full bg-black/40 rounded-full h-1.5 overflow-hidden">
            <div className="bg-primary h-full rounded-full" style={{ width: `${item.progress}%` }} />
          </div>
          <span className="text-xs text-muted-foreground w-8 text-right">{item.progress}%</span>
        </div>

        <div className="w-32 text-sm text-muted-foreground truncate">{item.owner}</div>
        
        <div className="w-24 text-sm text-muted-foreground">{item.dueDate}</div>

        <div className="w-32 flex items-center gap-2">
          <button className="flex items-center gap-2 px-2 py-1 rounded bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 transition-all text-xs w-full text-left">
            <StatusIcon status={item.status} />
            <span className="capitalize text-muted-foreground">{item.status.replace('_', ' ')}</span>
          </button>
        </div>
      </div>
      
      {expanded && hasChildren && item.children!.map(child => (
        <WorkItemRow key={child.id} item={child} level={level + 1} />
      ))}
    </>
  );
};

export default function WorkBreakdown() {
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
        <div className="w-32">Progress</div>
        <div className="w-32">Owner</div>
        <div className="w-24">Due Date</div>
        <div className="w-32">Status</div>
      </div>

      {/* Table Body */}
      <div className="flex-1 overflow-auto custom-scrollbar">
        {DUMMY_DATA.map(item => (
          <WorkItemRow key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
