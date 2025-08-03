import { useQuery } from '@tanstack/react-query';
import {
  analyticsApi,
  DirectoryUsageResponse,
  TimeRange,
} from '../api/analytics';

export interface UseDirectoryAnalyticsOptions {
  timeRange?: TimeRange;
  depth?: number;
  minCost?: number;
  enabled?: boolean;
}

export const useDirectoryAnalytics = ({
  timeRange = TimeRange.LAST_30_DAYS,
  depth = 3,
  minCost = 0.0,
  enabled = true,
}: UseDirectoryAnalyticsOptions = {}) => {
  return useQuery<DirectoryUsageResponse>({
    queryKey: ['directory-analytics', timeRange, depth, minCost],
    queryFn: () => analyticsApi.getDirectoryUsage(timeRange, depth, minCost),
    enabled,
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
    refetchOnWindowFocus: false,
  });
};
