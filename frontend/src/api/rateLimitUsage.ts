import { apiClient } from './client';

// Types for rate limit usage
export type RateLimitType =
  | 'http'
  | 'ingestion'
  | 'ai'
  | 'export'
  | 'import'
  | 'backup'
  | 'restore'
  | 'search'
  | 'analytics'
  | 'websocket';

export type UsageInterval = 'minute' | 'hour' | 'day' | 'week' | 'month';

export interface UserUsageSnapshot {
  user_id: string;
  timestamp: string;
  http_usage: UsageDetails;
  ingestion_usage: UsageDetails;
  ai_usage: UsageDetails;
  export_usage: UsageDetails;
  import_usage: UsageDetails;
  backup_usage: UsageDetails;
  restore_usage: UsageDetails;
  search_usage: UsageDetails;
  analytics_usage: UsageDetails;
  websocket_usage: UsageDetails;
  total_requests_today: number;
  total_blocked_today: number;
}

export interface UsageDetails {
  current: number;
  limit: number | 'unlimited';
  remaining: number;
  blocked?: number;
  percentage_used: number;
  reset_in_seconds?: number;
}

export interface RateLimitUsageAggregation {
  user_id: string;
  limit_type: RateLimitType;
  interval: UsageInterval;
  period_start: string;
  period_end: string;
  total_requests: number;
  total_allowed: number;
  total_blocked: number;
  peak_usage_rate: number;
  average_usage_rate: number;
  violation_count: number;
  avg_response_time_ms?: number;
  p95_response_time_ms?: number;
  p99_response_time_ms?: number;
  total_bytes_transferred?: number;
}

export interface UsageSummary {
  time_range_hours: number;
  start_date: string;
  end_date: string;
  by_type: Record<RateLimitType, UsageTypeStats>;
  overall: {
    total_requests: number;
    total_blocked: number;
    block_rate: number;
    total_violations: number;
  };
}

export interface UsageTypeStats {
  total_requests: number;
  total_allowed: number;
  total_blocked: number;
  block_rate: number;
  peak_usage_rate: number;
  average_usage_rate: number;
  violation_count: number;
  average_response_time_ms?: number;
  total_bytes_transferred?: number;
}

export interface UsageChartData {
  limit_type: RateLimitType;
  interval: UsageInterval;
  timestamps: string[];
  series: {
    requests: number[];
    allowed: number[];
    blocked: number[];
    usage_rate: number[];
  };
  metadata: {
    total_requests: number;
    total_blocked: number;
    peak_usage_rate: number;
    average_usage_rate: number;
  };
}

export const rateLimitUsageApi = {
  // Get current usage snapshot
  getCurrentUsage: async (): Promise<UserUsageSnapshot> => {
    return await apiClient.get<UserUsageSnapshot>('/rate-limits/usage/current');
  },

  // Get historical usage data
  getUsageHistory: async (params: {
    limit_type?: RateLimitType;
    interval?: UsageInterval;
    start_date?: string;
    end_date?: string;
  }): Promise<RateLimitUsageAggregation[]> => {
    return await apiClient.get<RateLimitUsageAggregation[]>(
      '/rate-limits/usage/history',
      {
        params,
      }
    );
  },

  // Get usage summary
  getUsageSummary: async (timeRangeHours = 24): Promise<UsageSummary> => {
    return await apiClient.get<UsageSummary>('/rate-limits/usage/summary', {
      params: { time_range_hours: timeRangeHours },
    });
  },

  // Get chart data
  getChartData: async (params: {
    limit_type: RateLimitType;
    interval?: UsageInterval;
    hours?: number;
  }): Promise<UsageChartData> => {
    return await apiClient.get<UsageChartData>(
      '/rate-limits/usage/chart-data',
      {
        params,
      }
    );
  },

  // Force flush metrics
  flushMetrics: async (): Promise<{ message: string }> => {
    return await apiClient.post<{ message: string }>(
      '/rate-limits/usage/flush'
    );
  },
};

// Helper functions
export const formatRateLimitType = (type: RateLimitType): string => {
  const labels: Record<RateLimitType, string> = {
    http: 'HTTP API',
    ingestion: 'Data Ingestion',
    ai: 'AI Features',
    export: 'Export',
    import: 'Import',
    backup: 'Backup',
    restore: 'Restore',
    search: 'Search',
    analytics: 'Analytics',
    websocket: 'WebSocket',
  };
  return labels[type] || type;
};

export const formatUsageInterval = (interval: UsageInterval): string => {
  const labels: Record<UsageInterval, string> = {
    minute: 'Per Minute',
    hour: 'Hourly',
    day: 'Daily',
    week: 'Weekly',
    month: 'Monthly',
  };
  return labels[interval] || interval;
};

export const getUsageColor = (percentage: number): string => {
  if (percentage < 50) return 'green';
  if (percentage < 75) return 'yellow';
  if (percentage < 90) return 'orange';
  return 'red';
};

export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
