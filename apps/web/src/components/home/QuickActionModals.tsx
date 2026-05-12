"use client";

import { useState } from "react";
import { sendMiloMessage } from "@/lib/api";
import { X, Loader2 } from "lucide-react";
import { useAppStore } from "@/store/useAppStore";

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

function BaseModal({ isOpen, onClose, title, children }: ModalProps & { title: string, children: React.ReactNode }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#111115] border border-white/10 rounded-xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
}

export function NewApprovalModal({ isOpen, onClose }: ModalProps) {
  const [toolName, setToolName] = useState("");
  const [justification, setJustification] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toggleRightRail, isRightRailOpen } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        tool: "approval.create",
        args: {
          tool_name: toolName,
          payload: { justification }
        }
      };
      // Send invisible message to trigger tool
      sendMiloMessage(`Please execute the tool approval.create with the following JSON: ${JSON.stringify(payload.args)}`, "QuickAction");
      if (!isRightRailOpen) toggleRightRail();
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="Request New Approval">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-white mb-1">Target Tool / Action</label>
          <input required type="text" value={toolName} onChange={e => setToolName(e.target.value)} placeholder="e.g. github.write" className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium text-white mb-1">Justification</label>
          <textarea required value={justification} onChange={e => setJustification(e.target.value)} placeholder="Why is this needed?" className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary min-h-[100px]" />
        </div>
        <button disabled={isSubmitting} type="submit" className="w-full bg-primary hover:bg-primary/90 text-white font-medium py-2 rounded-md transition-colors flex items-center justify-center">
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Submit Request"}
        </button>
      </form>
    </BaseModal>
  );
}

export function LogRiskModal({ isOpen, onClose }: ModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toggleRightRail, isRightRailOpen } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        entity_type: "risk",
        payload: { title, description, status: "open", impact: 4, likelihood: 4 }
      };
      sendMiloMessage(`Please execute the tool work_item.update to create a new risk with the following JSON: ${JSON.stringify(payload)}`, "QuickAction");
      if (!isRightRailOpen) toggleRightRail();
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="Log a Risk">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-white mb-1">Risk Title</label>
          <input required type="text" value={title} onChange={e => setTitle(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium text-white mb-1">Description</label>
          <textarea required value={description} onChange={e => setDescription(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary min-h-[100px]" />
        </div>
        <button disabled={isSubmitting} type="submit" className="w-full bg-red-500 hover:bg-red-600 text-white font-medium py-2 rounded-md transition-colors flex items-center justify-center">
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Log Risk"}
        </button>
      </form>
    </BaseModal>
  );
}

export function AddTaskModal({ isOpen, onClose }: ModalProps) {
  const [name, setName] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toggleRightRail, isRightRailOpen } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        entity_type: "task",
        payload: { name, due_date: dueDate || undefined, status: "todo" }
      };
      sendMiloMessage(`Please execute the tool work_item.update to create a new task with the following JSON: ${JSON.stringify(payload)}`, "QuickAction");
      if (!isRightRailOpen) toggleRightRail();
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="Add New Task">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-white mb-1">Task Name</label>
          <input required type="text" value={name} onChange={e => setName(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium text-white mb-1">Due Date</label>
          <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
        </div>
        <button disabled={isSubmitting} type="submit" className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-medium py-2 rounded-md transition-colors flex items-center justify-center">
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Add Task"}
        </button>
      </form>
    </BaseModal>
  );
}

export function InviteStakeholderModal({ isOpen, onClose }: ModalProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toggleRightRail, isRightRailOpen } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = { email, role };
      sendMiloMessage(`Please execute the tool stakeholder.invite with the following JSON: ${JSON.stringify(payload)}`, "QuickAction");
      if (!isRightRailOpen) toggleRightRail();
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="Invite Stakeholder">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-white mb-1">Email Address</label>
          <input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="colleague@company.com" className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium text-white mb-1">Project Role</label>
          <input required type="text" value={role} onChange={e => setRole(e.target.value)} placeholder="e.g. Sponsor, Viewer" className="w-full bg-black/50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
        </div>
        <button disabled={isSubmitting} type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 rounded-md transition-colors flex items-center justify-center">
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Send Invite"}
        </button>
      </form>
    </BaseModal>
  );
}
