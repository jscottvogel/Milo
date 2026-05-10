"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useEffect, useState, use } from "react";
import { fetchProgram } from "@/lib/api";
import { useAppStore } from "@/store/useAppStore";

const TABS = [
  { name: "Overview", path: "" },
  { name: "Work Breakdown", path: "/work-breakdown" },
  { name: "Risks & Decisions", path: "/risks-decisions" },
  { name: "Financials", path: "/financials" },
  { name: "Stakeholders", path: "/stakeholders" },
  { name: "Inbox", path: "/inbox" },
];

export default function ProgramDetailLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const pathname = usePathname();
  const basePath = `/programs/${resolvedParams.id}`;
  const [program, setProgram] = useState<any>(null);
  const { setBreadcrumbContext } = useAppStore();

  useEffect(() => {
    fetchProgram(resolvedParams.id).then(data => {
      setProgram(data);
      setBreadcrumbContext([
        { label: 'Programs', path: '/programs' },
        { label: data.name, path: basePath }
      ]);
    }).catch(console.error);

    return () => setBreadcrumbContext([]); // clear on unmount
  }, [resolvedParams.id, basePath, setBreadcrumbContext]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Program Header */}
      <div className="bg-black/20 border-b border-white/10 p-6 flex-shrink-0">
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-white">{program?.name || "Loading..."}</h1>
              {program && (
                <span className={cn(
                  "px-2.5 py-0.5 rounded-full text-xs font-medium border",
                  program.status === 'done' || program.status === 'completed' ? "bg-green-500/10 text-green-400 border-green-500/20" :
                  program.status === 'in_progress' ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                  "bg-amber-500/10 text-amber-400 border-amber-500/20"
                )}>
                  {program.status.replace('_', ' ')}
                </span>
              )}
            </div>
            <p className="text-muted-foreground text-sm max-w-2xl">
              {program?.description || "Loading description..."}
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-white">{program?.owner_name || "Unassigned"}</div>
            <div className="text-xs text-muted-foreground capitalize">{program?.item_type ? program.item_type.replace('_', ' ') + ' Owner' : "Owner"}</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 overflow-x-auto no-scrollbar">
          {TABS.map((tab) => {
            const href = `${basePath}${tab.path}`;
            const isActive = tab.path === "" 
              ? pathname === basePath 
              : pathname.startsWith(href);
              
            return (
              <Link
                key={tab.name}
                href={href}
                className={cn(
                  "px-4 py-2 text-sm font-medium rounded-t-lg transition-colors border-b-2",
                  isActive
                    ? "text-primary border-primary bg-primary/5"
                    : "text-muted-foreground border-transparent hover:text-white hover:bg-white/5"
                )}
              >
                {tab.name}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Tab Content Area */}
      <div className="flex-1 overflow-auto bg-[#0a0a0c] p-6">
        {children}
      </div>
    </div>
  );
}
