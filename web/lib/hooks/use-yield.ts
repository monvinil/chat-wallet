/**
 * Yield Hooks
 * TanStack Query hooks for yield/Aave data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { YieldDepositRequest, YieldWithdrawRequest } from '@/lib/api';
import { toast } from 'sonner';
import { walletKeys } from './use-wallet';

// Query keys
export const yieldKeys = {
  all: ['yield'] as const,
  status: () => [...yieldKeys.all, 'status'] as const,
};

/**
 * Hook to fetch yield status
 */
export function useYieldStatus(enabled = true) {
  return useQuery({
    queryKey: yieldKeys.status(),
    queryFn: () => api.yield.getStatus(),
    enabled,
    // Refetch every minute for earnings updates
    refetchInterval: 60 * 1000,
  });
}

/**
 * Hook to deposit into yield (Aave)
 */
export function useYieldDeposit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: YieldDepositRequest) => api.yield.deposit(data),
    onSuccess: () => {
      // Invalidate both yield status and wallet balances
      queryClient.invalidateQueries({ queryKey: yieldKeys.status() });
      queryClient.invalidateQueries({ queryKey: walletKeys.balances() });
      toast.success('Successfully enabled yield!');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to enable yield');
    },
  });
}

/**
 * Hook to withdraw from yield (Aave)
 */
export function useYieldWithdraw() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: YieldWithdrawRequest) => api.yield.withdraw(data),
    onSuccess: () => {
      // Invalidate both yield status and wallet balances
      queryClient.invalidateQueries({ queryKey: yieldKeys.status() });
      queryClient.invalidateQueries({ queryKey: walletKeys.balances() });
      toast.success('Successfully withdrew from yield');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to withdraw');
    },
  });
}
