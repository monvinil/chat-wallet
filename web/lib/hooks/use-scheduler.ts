/**
 * Scheduler/DCA Hooks
 * TanStack Query hooks for scheduled tasks (DCA)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ScheduleCreateRequest } from '@/lib/api';
import { toast } from 'sonner';

// Query keys
export const schedulerKeys = {
  all: ['scheduler'] as const,
  list: () => [...schedulerKeys.all, 'list'] as const,
};

/**
 * Hook to fetch all schedules
 */
export function useSchedules(enabled = true) {
  return useQuery({
    queryKey: schedulerKeys.list(),
    queryFn: () => api.scheduler.list(),
    enabled,
  });
}

/**
 * Hook to create a new schedule (DCA)
 */
export function useCreateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ScheduleCreateRequest) => api.scheduler.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: schedulerKeys.list() });
      toast.success('Auto-invest schedule created!');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to create schedule');
    },
  });
}

/**
 * Hook to cancel a schedule
 */
export function useCancelSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.scheduler.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: schedulerKeys.list() });
      toast.success('Schedule cancelled');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to cancel schedule');
    },
  });
}

/**
 * Hook to pause a schedule
 */
export function usePauseSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.scheduler.pause(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: schedulerKeys.list() });
      toast.info('Schedule paused');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to pause schedule');
    },
  });
}

/**
 * Hook to resume a schedule
 */
export function useResumeSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.scheduler.resume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: schedulerKeys.list() });
      toast.success('Schedule resumed');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to resume schedule');
    },
  });
}
