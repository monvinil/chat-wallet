/**
 * Wallet Hooks
 * TanStack Query hooks for wallet data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type {
  WalletBalances,
  WalletAddress,
  TransactionPreviewRequest,
  TransactionSendRequest,
} from '@/lib/api';
import { toast } from 'sonner';

// Query keys
export const walletKeys = {
  all: ['wallet'] as const,
  balances: () => [...walletKeys.all, 'balances'] as const,
  address: (chain: string) => [...walletKeys.all, 'address', chain] as const,
};

/**
 * Hook to fetch wallet balances
 */
export function useWalletBalances(enabled = true) {
  return useQuery({
    queryKey: walletKeys.balances(),
    queryFn: () => api.wallet.getBalances(),
    enabled,
    // Refetch every 30 seconds for near-real-time balance updates
    refetchInterval: 30 * 1000,
  });
}

/**
 * Hook to fetch deposit address for a specific chain
 */
export function useWalletAddress(chain: string, enabled = true) {
  return useQuery({
    queryKey: walletKeys.address(chain),
    queryFn: () => api.wallet.getAddress(chain),
    enabled: enabled && !!chain,
    // Addresses don't change, cache longer
    staleTime: 5 * 60 * 1000,
  });
}

// Transaction keys
export const transactionKeys = {
  all: ['transactions'] as const,
  history: (page?: number) => [...transactionKeys.all, 'history', page] as const,
  status: (hash: string) => [...transactionKeys.all, 'status', hash] as const,
};

/**
 * Hook to fetch transaction history
 */
export function useTransactionHistory(page = 1, perPage = 20, enabled = true) {
  return useQuery({
    queryKey: transactionKeys.history(page),
    queryFn: () => api.transactions.getHistory(page, perPage),
    enabled,
  });
}

/**
 * Hook to preview a transaction
 */
export function useTransactionPreview() {
  return useMutation({
    mutationFn: (data: TransactionPreviewRequest) => api.transactions.preview(data),
  });
}

/**
 * Hook to send a transaction
 */
export function useTransactionSend() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TransactionSendRequest) => api.transactions.send(data),
    onSuccess: () => {
      // Invalidate balances and history after successful send
      queryClient.invalidateQueries({ queryKey: walletKeys.balances() });
      queryClient.invalidateQueries({ queryKey: transactionKeys.all });
      toast.success('Transaction sent successfully');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Transaction failed');
    },
  });
}

/**
 * Hook to poll transaction status
 */
export function useTransactionStatus(hash: string, enabled = true) {
  return useQuery({
    queryKey: transactionKeys.status(hash),
    queryFn: () => api.transactions.getStatus(hash),
    enabled: enabled && !!hash,
    // Poll every 5 seconds until confirmed
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'confirmed' || data?.status === 'failed') {
        return false; // Stop polling
      }
      return 5000; // Poll every 5 seconds
    },
  });
}
