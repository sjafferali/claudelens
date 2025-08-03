import { useQuery } from '@tanstack/react-query';
import { analyticsApi, TimeRange } from '@/api/analytics';

export function useAnalyticsSummary(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS
) {
  return useQuery({
    queryKey: ['analytics', 'summary', timeRange],
    queryFn: () => analyticsApi.getSummary(timeRange),
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
  });
}

export function useActivityHeatmap(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  timezone: string = Intl.DateTimeFormat().resolvedOptions().timeZone
) {
  return useQuery({
    queryKey: ['analytics', 'heatmap', timeRange, timezone],
    queryFn: () => analyticsApi.getActivityHeatmap(timeRange, timezone),
    staleTime: 300000, // 5 minutes
  });
}

export function useCostAnalytics(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  groupBy: 'hour' | 'day' | 'week' | 'month' = 'day',
  projectId?: string
) {
  return useQuery({
    queryKey: ['analytics', 'costs', timeRange, groupBy, projectId],
    queryFn: () => analyticsApi.getCostAnalytics(timeRange, groupBy, projectId),
    staleTime: 300000, // 5 minutes
  });
}

export function useModelUsage(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  projectId?: string
) {
  return useQuery({
    queryKey: ['analytics', 'models', timeRange, projectId],
    queryFn: () => analyticsApi.getModelUsage(timeRange, projectId),
    staleTime: 300000, // 5 minutes
  });
}
