/**
 * Earnings Hooks
 * TanStack Query hooks for earnings data
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Query keys
export const earningsKeys = {
  all: ['earnings'] as const,
  summary: () => [...earningsKeys.all, 'summary'] as const,
  history: (period: string, days: number) => [...earningsKeys.all, 'history', period, days] as const,
};

/**
 * Hook to fetch earnings summary
 */
export function useEarningsSummary(enabled = true) {
  return useQuery({
    queryKey: earningsKeys.summary(),
    queryFn: () => api.earnings.getSummary(),
    enabled,
    // Refetch every 5 minutes
    refetchInterval: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch earnings history
 */
export function useEarningsHistory(
  period: 'daily' | 'weekly' | 'monthly' = 'daily',
  days = 30,
  enabled = true
) {
  return useQuery({
    queryKey: earningsKeys.history(period, days),
    queryFn: () => api.earnings.getHistory(period, days),
    enabled,
    // Earnings history doesn't change frequently
    staleTime: 10 * 60 * 1000,
  });
}
