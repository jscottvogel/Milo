import { Link as LinkIcon, Flag, ListTodo } from 'lucide-react';
import clsx from 'clsx';

interface TimelineItem {
  id: string;
  type: 'milestone' | 'task';
  name: string;
  startDate: Date;
  endDate: Date;
  status: string;
  ownerName?: string;
  dependencies: string[];
  depth: number;
}

export function GanttChart({ program }: { program: any }) {
  const items: TimelineItem[] = [];
  
  function flattenTree(node: any, depth: number) {
    if (!node) return;
    const start = new Date(node.start_date || node.due_date || node.actual_date || Date.now());
    const end = new Date(node.due_date || node.start_date || node.actual_date || start);
    if (end.getTime() === start.getTime()) {
        end.setDate(end.getDate() + 1);
    }
    
    // Push the current node
    items.push({
      id: node.id,
      type: node.item_type,
      name: node.name,
      startDate: start,
      endDate: end,
      status: node.status,
      ownerName: node.owner_name,
      dependencies: node.dependencies || [],
      depth: depth
    });

    if (node.children && Array.isArray(node.children)) {
        node.children.forEach((child: any) => {
            flattenTree(child, depth + 1);
        });
    }
  }

  // Start with the root program's children, or the program itself
  if (program) {
      flattenTree(program, 0);
  }

  if (items.length === 0) {
    return (
      <div className="glass-card border-dashed p-12 text-center text-muted-foreground">
        No schedule data available to build a timeline.
      </div>
    );
  }

  // 2. Find overall min and max dates
  let minDate = new Date(Math.min(...items.map(i => i.startDate.getTime())));
  let maxDate = new Date(Math.max(...items.map(i => i.endDate.getTime())));
  
  // Add 10% padding to dates
  const totalDuration = maxDate.getTime() - minDate.getTime();
  const padding = Math.max(totalDuration * 0.1, 7 * 24 * 60 * 60 * 1000); // at least 7 days padding
  
  minDate = new Date(minDate.getTime() - padding);
  maxDate = new Date(maxDate.getTime() + padding);
  const chartDuration = maxDate.getTime() - minDate.getTime();

  // 3. Render
  return (
    <div className="glass-card overflow-hidden flex flex-col">
      {/* Header */}
      <div className="flex border-b border-border bg-black/20 text-xs font-medium text-muted-foreground p-3">
        <div className="w-1/3 min-w-[250px] shrink-0 pl-2">Name & Owner</div>
        <div className="flex-1 relative">
           <div className="absolute left-0 top-0">Start</div>
           <div className="absolute right-0 top-0">Target</div>
        </div>
      </div>

      {/* Rows */}
      <div className="relative flex flex-col divide-y divide-white/5 pb-4">
        {items.map((item) => {
          const leftPercent = ((item.startDate.getTime() - minDate.getTime()) / chartDuration) * 100;
          const widthPercent = ((item.endDate.getTime() - item.startDate.getTime()) / chartDuration) * 100;

          const isMilestone = item.type === 'milestone';
          
          return (
            <div key={item.id} className="flex group hover:bg-white/5 transition-colors relative h-14 items-center">
              {/* Left Column: Label */}
              <div 
                className="w-1/3 min-w-[250px] shrink-0 flex items-center pr-4 border-r border-border/50 bg-black/10"
                style={{ paddingLeft: `${item.depth * 1.5 + 1}rem` }}
              >
                {isMilestone ? (
                  <Flag className="text-indigo-400 mr-2 shrink-0" size={16} />
                ) : (
                  <ListTodo className="text-emerald-400 mr-2 shrink-0" size={16} />
                )}
                <div className="truncate flex-1">
                  <p className={clsx("truncate", isMilestone ? "text-white font-medium text-sm" : "text-gray-300 text-sm")}>
                    {item.name}
                  </p>
                  {item.ownerName && (
                    <div className="flex items-center gap-1 mt-0.5">
                      <div className="w-4 h-4 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[9px] font-bold text-white shadow-lg shrink-0">
                        {item.ownerName.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-[10px] text-muted-foreground truncate">{item.ownerName}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Timeline Track */}
              <div className="flex-1 relative h-full">
                {/* Background Grid Lines */}
                <div className="absolute inset-0 flex">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="flex-1 border-r border-white/5 h-full"></div>
                  ))}
                </div>

                {/* The Bar */}
                <div 
                  className={clsx(
                    "absolute top-1/2 -translate-y-1/2 h-6 rounded shadow-lg transition-all group-hover:brightness-110 flex items-center px-2 min-w-[4px]",
                    isMilestone ? "bg-indigo-500/80 border border-indigo-400" : "bg-emerald-500/80 border border-emerald-400"
                  )}
                  style={{
                    left: `${Math.max(0, leftPercent)}%`,
                    width: `${Math.max(0.5, widthPercent)}%`
                  }}
                >
                  {item.dependencies.length > 0 && (
                     <div className="absolute -left-5 bg-background border border-border rounded-full p-0.5">
                       <LinkIcon size={10} className="text-muted-foreground" />
                     </div>
                  )}
                  {widthPercent > 10 && (
                     <span className="text-[10px] font-medium text-white truncate drop-shadow-md">
                       {item.startDate.toLocaleDateString(undefined, {month:'short', day:'numeric'})}
                     </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
