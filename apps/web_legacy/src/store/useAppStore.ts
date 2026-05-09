import { create } from 'zustand';

interface AppState {
  // Navigation State
  isRightRailOpen: boolean;
  toggleRightRail: () => void;
  setRightRailOpen: (open: boolean) => void;
  
  // Breadcrumb Context
  breadcrumbContext: { label: string; path: string }[];
  setBreadcrumbContext: (context: { label: string; path: string }[]) => void;
  
  // Approvals State
  pendingApprovalsCount: number;
  setPendingApprovalsCount: (count: number) => void;
  decrementPendingApprovals: () => void;
  
  // Global Search
  isSearchOpen: boolean;
  toggleSearch: () => void;
  setSearchOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Navigation State
  isRightRailOpen: true,
  toggleRightRail: () => set((state) => ({ isRightRailOpen: !state.isRightRailOpen })),
  setRightRailOpen: (open) => set({ isRightRailOpen: open }),
  
  // Breadcrumb Context
  breadcrumbContext: [],
  setBreadcrumbContext: (context) => set({ breadcrumbContext: context }),
  
  // Approvals State
  pendingApprovalsCount: 0,
  setPendingApprovalsCount: (count) => set({ pendingApprovalsCount: count }),
  decrementPendingApprovals: () => set((state) => ({ pendingApprovalsCount: Math.max(0, state.pendingApprovalsCount - 1) })),
  
  // Global Search
  isSearchOpen: false,
  toggleSearch: () => set((state) => ({ isSearchOpen: !state.isSearchOpen })),
  setSearchOpen: (open) => set({ isSearchOpen: open }),
}));
