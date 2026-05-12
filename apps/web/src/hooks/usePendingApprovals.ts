import { useQuery } from "@tanstack/react-query";
import { fetchApprovals } from "@/lib/api";

export function usePendingApprovals() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: async () => {
      // In a real app we might pass status='pending' to fetchApprovals
      // For now we'll just filter the results client-side if the API returns all,
      // or assume the API is updated to handle it.
      const res = await fetchApprovals();
      return res.filter((a: any) => a.status === 'pending');
    },
    refetchInterval: 60000, // 60 seconds
  });

  return {
    count: data ? data.length : 0,
    approvals: data || [],
    isLoading,
    error
  };
}
