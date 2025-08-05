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

export function useConversationFlow(
  sessionId: string | null,
  includeSidechains: boolean = true
) {
  return useQuery({
    queryKey: ['analytics', 'conversation-flow', sessionId, includeSidechains],
    queryFn: () =>
      analyticsApi.getConversationFlow(sessionId!, includeSidechains),
    enabled: !!sessionId,
    staleTime: 300000, // 5 minutes
  });
}

export function useResponseTimes(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  percentiles?: number[],
  groupBy: 'hour' | 'day' | 'model' | 'tool_count' = 'hour'
) {
  return useQuery({
    queryKey: ['analytics', 'response-times', timeRange, percentiles, groupBy],
    queryFn: () =>
      analyticsApi.getResponseTimes(timeRange, percentiles, groupBy),
    staleTime: 300000, // 5 minutes
  });
}

export function usePerformanceFactors(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS
) {
  return useQuery({
    queryKey: ['analytics', 'performance-factors', timeRange],
    queryFn: () => analyticsApi.getPerformanceFactors(timeRange),
    staleTime: 300000, // 5 minutes
  });
}

export function useSessionDepthAnalytics(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  projectId?: string,
  minDepth: number = 0,
  includeSidechains: boolean = true
) {
  return useQuery({
    queryKey: [
      'analytics',
      'session-depth',
      timeRange,
      projectId,
      minDepth,
      includeSidechains,
    ],
    queryFn: () =>
      analyticsApi.getSessionDepthAnalytics(
        timeRange,
        projectId,
        minDepth,
        includeSidechains
      ),
    staleTime: 300000, // 5 minutes
  });
}

export function useCostSummary(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  sessionId?: string | null,
  projectId?: string
) {
  return useQuery({
    queryKey: ['analytics', 'cost-summary', timeRange, sessionId, projectId],
    queryFn: () =>
      analyticsApi.getCostSummary(sessionId || undefined, projectId, timeRange),
    staleTime: 60000, // 1 minute
  });
}

export function useCostBreakdown(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  sessionId?: string | null,
  projectId?: string
) {
  return useQuery({
    queryKey: ['analytics', 'cost-breakdown', timeRange, sessionId, projectId],
    queryFn: () =>
      analyticsApi.getCostBreakdown(
        sessionId || undefined,
        projectId,
        timeRange
      ),
    staleTime: 300000, // 5 minutes
  });
}

export function useToolUsage(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  sessionId?: string | null,
  projectId?: string
) {
  return useQuery({
    queryKey: ['analytics', 'tool-usage', timeRange, sessionId, projectId],
    queryFn: () =>
      analyticsApi.getToolUsageDetailed(
        sessionId || undefined,
        projectId,
        timeRange
      ),
    staleTime: 300000, // 5 minutes
  });
}

export function useTokenEfficiency(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  sessionId?: string | null
) {
  return useQuery({
    queryKey: ['analytics', 'token-efficiency', timeRange, sessionId],
    queryFn: () =>
      analyticsApi.getTokenEfficiencyDetailed(
        sessionId || undefined,
        timeRange
      ),
    staleTime: 300000, // 5 minutes
  });
}

export function useGitBranchAnalytics(
  timeRange: TimeRange = TimeRange.LAST_30_DAYS,
  projectId?: string,
  includePattern?: string,
  excludePattern?: string
) {
  return useQuery({
    queryKey: [
      'analytics',
      'git-branches',
      timeRange,
      projectId,
      includePattern,
      excludePattern,
    ],
    queryFn: () =>
      analyticsApi.getGitBranchAnalytics(
        timeRange,
        projectId,
        includePattern,
        excludePattern
      ),
    staleTime: 300000, // 5 minutes
  });
}
