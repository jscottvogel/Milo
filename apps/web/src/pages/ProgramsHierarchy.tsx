import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store/useAppStore';
import { ChevronRight, ChevronDown, Flag, Target, Crosshair, Package, Folder, LayoutGrid, MapPin, CheckSquare, Activity, AlertTriangle, FileText, GitPullRequest, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { apiFetch } from '../api/client';

// Types
type LayerLevel = 'Objective' | 'Outcome' | 'Key Result' | 'Initiative' | 'Project' | 'Workstream' | 'Milestone' | 'Task';

interface WorkItem {
  id: string;
  title: string;
  level: LayerLevel;
  status: 'On Track' | 'At Risk' | 'Off Track' | 'Done';
  owner: string;
  dueDate: string;
  progress: number;
  children?: WorkItem[];
  description?: string;
  _raw?: any;
}

const LAYER_ICONS: Record<LayerLevel, any> = {
  'Objective': Flag,
  'Outcome': Target,
  'Key Result': Crosshair,
  'Initiative': Package,
  'Project': Folder,
  'Workstream': LayoutGrid,
  'Milestone': MapPin,
  'Task': CheckSquare,
};

const STATUS_COLORS = {
  'On Track': 'bg-green-500/20 text-green-400 border-green-500/20',
  'At Risk': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/20',
  'Off Track': 'bg-red-500/20 text-red-400 border-red-500/20',
  'Done': 'bg-blue-500/20 text-blue-400 border-blue-500/20',
};

// Status mapping helper
const mapStatus = (status: string): WorkItem['status'] => {
  const s = status?.toLowerCase();
  if (s === 'on_track' || s === 'pending') return 'On Track';
  if (s === 'at_risk') return 'At Risk';
  if (s === 'off_track') return 'Off Track';
  if (s === 'done' || s === 'completed' || s === 'closed') return 'Done';
  return 'On Track'; // default
};

const mapLevel = (level: string): LayerLevel => {
  const l = level?.toLowerCase();
  if (l === 'objective') return 'Objective';
  if (l === 'outcome') return 'Outcome';
  if (l === 'key_result') return 'Key Result';
  if (l === 'initiative') return 'Initiative';
  if (l === 'project') return 'Project';
  if (l === 'workstream') return 'Workstream';
  if (l === 'milestone') return 'Milestone';
  if (l === 'task') return 'Task';
  return 'Task'; // default
};

// Map backend tree to frontend structure
const transformTree = (nodes: any[]): WorkItem[] => {
  return nodes.map(node => ({
    id: node.id,
    title: node.name || 'Unnamed',
    level: mapLevel(node.item_type),
    status: mapStatus(node.status),
    owner: node.owner_name || 'Unassigned',
    dueDate: node.due_date ? new Date(node.due_date).toLocaleDateString() : 'TBD',
    progress: node.metadata_json?.progress || 0,
    description: node.description,
    children: node.children && node.children.length > 0 ? transformTree(node.children) : undefined,
    // Store original data to access risks, decisions etc in the UI
    _raw: node
  }));
};

export const ProgramsHierarchy: React.FC = () => {
  const { setBreadcrumbContext } = useAppStore();
  const [hierarchy, setHierarchy] = useState<WorkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [selectedItem, setSelectedItem] = useState<WorkItem | null>(null);
  const [activeTab, setActiveTab] = useState<'activity' | 'risks' | 'decisions' | 'changes'>('activity');

  useEffect(() => {
    async function fetchTree() {
      try {
        const data = await apiFetch<any[]>('/v1/work_items/tree');
        const transformed = transformTree(data);
        setHierarchy(transformed);
        if (transformed.length > 0) {
          setExpandedIds(new Set([transformed[0].id]));
        }
      } catch (err) {
        console.error('Failed to load hierarchy tree', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTree();
  }, []);

  // Breadcrumb path builder
  useEffect(() => {
    if (!selectedItem) {
      setBreadcrumbContext([{ label: 'Programs', path: '/programs' }]);
      return;
    }

    const path: { label: string, path: string }[] = [{ label: 'Programs', path: '/programs' }];
    
    const findPath = (items: WorkItem[], targetId: string, currentPath: { label: string, path: string }[]): boolean => {
      for (const item of items) {
        const newPath = [...currentPath, { label: item.title, path: `/programs?id=${item.id}` }];
        if (item.id === targetId) {
          setBreadcrumbContext(newPath);
          return true;
        }
        if (item.children && findPath(item.children, targetId, newPath)) {
          return true;
        }
      }
      return false;
    };
    findPath(hierarchy, selectedItem.id, path);
  }, [selectedItem, hierarchy, setBreadcrumbContext]);

  // Handle ESC
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedItem(null);
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  const toggleExpand = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  const renderItem = (item: WorkItem, depth: number = 0) => {
    const isExpanded = expandedIds.has(item.id);
    const isSelected = selectedItem?.id === item.id;
    const Icon = LAYER_ICONS[item.level];
    
    return (
      <div key={item.id} className="flex flex-col w-full">
        <div 
          onClick={() => setSelectedItem(item)}
          className={clsx(
            "flex items-center p-3 cursor-pointer border-y border-transparent transition-colors w-full group",
            isSelected ? "bg-primary/10 border-y-primary/20" : "hover:bg-white/5 border-b-white/5"
          )}
          style={{ paddingLeft: `${depth * 24 + 12}px` }}
        >
          <div 
            onClick={(e) => item.children ? toggleExpand(e, item.id) : undefined}
            className="w-6 h-6 flex items-center justify-center mr-2 text-muted-foreground hover:text-white rounded hover:bg-white/10"
          >
            {item.children ? (
              isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />
            ) : <span className="w-4 h-4" />}
          </div>
          
          <Icon className={clsx("w-4 h-4 mr-3", isSelected ? "text-primary" : "text-muted-foreground group-hover:text-white")} />
          
          <div className="flex-1 min-w-0 flex items-center gap-4">
            <span className={clsx("font-medium truncate text-sm", isSelected ? "text-primary" : "text-white")}>
              {item.title}
            </span>
            <span className={clsx("text-[10px] px-2 py-0.5 rounded border uppercase tracking-wide", STATUS_COLORS[item.status])}>
              {item.status}
            </span>
          </div>
          
          <div className="flex items-center gap-6 hidden sm:flex">
            <div className="text-xs text-muted-foreground flex items-center gap-2 w-24">
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[9px] font-bold text-white">
                {item.owner.substring(0, 2).toUpperCase()}
              </div>
              <span className="truncate">{item.owner}</span>
            </div>
            
            <div className="text-xs text-muted-foreground w-20 truncate">
              {item.dueDate}
            </div>
            
            <div className="w-24 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary" 
                  style={{ width: `${item.progress}%` }} 
                />
              </div>
              <span className="text-[10px] text-muted-foreground w-6 text-right">{item.progress}%</span>
            </div>
          </div>
        </div>

        {/* Children (Inline Expansion) */}
        <AnimatePresence>
          {isExpanded && item.children && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              {item.children.map(child => renderItem(child, depth + 1))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  return (
    <div className="flex h-full max-h-[calc(100vh-64px)] w-full relative">
      
      {/* Left Pane: Hierarchy List */}
      <div className={clsx(
        "flex flex-col h-full overflow-y-auto transition-all duration-300 border-r border-border",
        selectedItem ? "w-full lg:w-1/2 hidden lg:flex" : "w-full"
      )}>
        <div className="sticky top-0 z-10 bg-[#0a0a0c]/90 backdrop-blur-md border-b border-border p-4 flex justify-between items-center">
          <h2 className="font-semibold">Programs Overview</h2>
          <div className="flex gap-2">
            <button className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded border border-white/5 transition-colors">
              Filter
            </button>
            <button className="text-xs px-3 py-1.5 bg-primary text-primary-foreground hover:bg-primary/90 rounded font-medium transition-colors">
              New Objective
            </button>
          </div>
        </div>
        
        <div className="pb-10">
          {loading ? (
            <div className="flex justify-center mt-20">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          ) : hierarchy.length === 0 ? (
            <div className="text-center mt-20 text-muted-foreground text-sm">No programs found.</div>
          ) : (
            hierarchy.map(item => renderItem(item, 0))
          )}
        </div>
      </div>

      {/* Right Pane: Detail Panel */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div 
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="flex-1 flex flex-col h-full bg-[#111115] overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-white/10 flex-shrink-0">
              <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                {React.createElement(LAYER_ICONS[selectedItem.level], { className: "w-4 h-4" })}
                {selectedItem.level}
              </div>
              <h1 className="text-2xl font-bold mb-4">{selectedItem.title}</h1>
              
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Status:</span>
                  <span className={clsx("text-xs px-2 py-0.5 rounded border uppercase tracking-wide font-bold", STATUS_COLORS[selectedItem.status])}>
                    {selectedItem.status}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Owner:</span>
                  <div className="flex items-center gap-1.5 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                    <div className="w-4 h-4 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[8px] font-bold">
                      {selectedItem.owner.substring(0, 2).toUpperCase()}
                    </div>
                    <span>{selectedItem.owner}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Due:</span>
                  <span>{selectedItem.dueDate}</span>
                </div>
                <div className="flex items-center gap-2 w-40">
                  <span className="text-muted-foreground">Progress:</span>
                  <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${selectedItem.progress}%` }} />
                  </div>
                  <span>{selectedItem.progress}%</span>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="p-6 border-b border-white/10 flex-shrink-0">
              <h3 className="font-semibold mb-2">Description</h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                {selectedItem.description || 'No description provided for this item.'}
              </p>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-white/10 px-4">
              {[
                { id: 'activity', label: 'Activity Log', icon: Activity },
                { id: 'risks', label: 'Risks', icon: AlertTriangle, count: selectedItem._raw?.risks?.length },
                { id: 'decisions', label: 'Decisions', icon: FileText, count: selectedItem._raw?.decisions?.length },
                { id: 'changes', label: 'Change Requests', icon: GitPullRequest, count: selectedItem._raw?.change_requests?.length },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={clsx(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                    activeTab === tab.id 
                      ? "border-primary text-primary" 
                      : "border-transparent text-muted-foreground hover:text-white hover:bg-white/5"
                  )}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {!!tab.count && (
                    <span className="ml-1 bg-white/10 text-white text-[10px] px-1.5 py-0.5 rounded-full">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6 bg-white/[0.02]">
              {activeTab === 'activity' && (
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <span className="text-primary text-xs font-bold">ML</span>
                    </div>
                    <div>
                      <p className="text-sm"><strong className="text-white">Milo</strong> flagged a schedule risk based on dependency delays.</p>
                      <span className="text-xs text-muted-foreground">2 hours ago</span>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-xs font-bold">JS</span>
                    </div>
                    <div>
                      <p className="text-sm"><strong className="text-white">Sarah</strong> updated progress from 35% to 45%.</p>
                      <span className="text-xs text-muted-foreground">Yesterday at 4:30 PM</span>
                    </div>
                  </div>
                </div>
              )}
              {activeTab === 'risks' && (
                <div className="space-y-4">
                  {selectedItem._raw?.risks?.length > 0 ? selectedItem._raw.risks.map((risk: any) => (
                    <div key={risk.id} className="p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-orange-400">{risk.title}</h4>
                        <span className="text-xs text-orange-400 border border-orange-500/30 px-2 py-0.5 rounded bg-orange-500/10 uppercase tracking-wide">
                          {risk.status}
                        </span>
                      </div>
                      <div className="flex gap-4 text-xs text-orange-400/80 mt-2">
                        <span>Impact: {risk.impact}/5</span>
                        <span>Likelihood: {risk.likelihood}/5</span>
                      </div>
                    </div>
                  )) : (
                    <div className="text-center text-muted-foreground py-10 text-sm">No risks logged.</div>
                  )}
                </div>
              )}
              {activeTab === 'decisions' && (
                <div className="space-y-4">
                  {selectedItem._raw?.decisions?.length > 0 ? selectedItem._raw.decisions.map((dec: any) => (
                    <div key={dec.id} className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <h4 className="font-semibold text-blue-400 mb-2">{dec.title}</h4>
                      <p className="text-sm text-gray-300">{dec.decision_text}</p>
                    </div>
                  )) : (
                    <div className="text-center text-muted-foreground py-10 text-sm">No decisions logged.</div>
                  )}
                </div>
              )}
              {activeTab === 'changes' && (
                <div className="space-y-4">
                  {selectedItem._raw?.change_requests?.length > 0 ? selectedItem._raw.change_requests.map((cr: any) => (
                    <div key={cr.id} className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-purple-400">{cr.title}</h4>
                        <span className="text-xs text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded bg-purple-500/10 uppercase tracking-wide">
                          {cr.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300">{cr.description}</p>
                    </div>
                  )) : (
                    <div className="text-center text-muted-foreground py-10 text-sm">No change requests logged.</div>
                  )}
                </div>
              )}
            </div>
            
            {/* Mobile close button overlay */}
            <button 
              className="lg:hidden absolute top-4 right-4 p-2 bg-black/50 hover:bg-black text-white rounded-full transition-colors"
              onClick={() => setSelectedItem(null)}
            >
              <span className="sr-only">Close details</span>
              &times;
            </button>
          </motion.div>
        )}
      </AnimatePresence>
      
    </div>
  );
};

export default ProgramsHierarchy;
