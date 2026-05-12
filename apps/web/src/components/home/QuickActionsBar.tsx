"use client";

import { PlusCircle, FileText, AlertTriangle, Sparkles, UserPlus } from "lucide-react";

import { useState } from "react";
import { NewApprovalModal, LogRiskModal, AddTaskModal, InviteStakeholderModal } from "./QuickActionModals";

export function QuickActionsBar() {
  const [openModal, setOpenModal] = useState<"approval" | "risk" | "task" | "stakeholder" | null>(null);

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-2 flex flex-wrap gap-2">
      <button suppressHydrationWarning onClick={() => setOpenModal("task")} className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <PlusCircle className="w-4 h-4 text-emerald-400" />
        New Task
      </button>
      <button suppressHydrationWarning onClick={() => setOpenModal("approval")} className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <FileText className="w-4 h-4 text-blue-400" />
        New Approval
      </button>
      <button suppressHydrationWarning onClick={() => setOpenModal("risk")} className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <AlertTriangle className="w-4 h-4 text-red-400" />
        Log Risk
      </button>
      <button suppressHydrationWarning onClick={() => setOpenModal("stakeholder")} className="flex-1 min-w-[120px] bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 text-white text-sm font-medium py-2 px-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
        <UserPlus className="w-4 h-4 text-indigo-400" />
        Invite Stakeholder
      </button>

      <NewApprovalModal isOpen={openModal === "approval"} onClose={() => setOpenModal(null)} />
      <LogRiskModal isOpen={openModal === "risk"} onClose={() => setOpenModal(null)} />
      <AddTaskModal isOpen={openModal === "task"} onClose={() => setOpenModal(null)} />
      <InviteStakeholderModal isOpen={openModal === "stakeholder"} onClose={() => setOpenModal(null)} />
    </div>
  );
}
