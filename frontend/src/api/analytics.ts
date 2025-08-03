import { apiClient } from './client';

export enum TimeRange {
  LAST_24_HOURS = '24h',
  LAST_7_DAYS = '7d',
  LAST_30_DAYS = '30d',
  LAST_90_DAYS = '90d',
  LAST_YEAR = '1y',
  ALL_TIME = 'all',
}

export interface AnalyticsSummary {
  total_messages: number;
  total_sessions: number;
  total_projects: number;
  total_cost: number;
  messages_trend: number;
  cost_trend: number;
  most_active_project: string | null;
  most_used_model: string | null;
  time_range: TimeRange;
  generated_at: string;
}

export interface ActivityHeatmap {
  cells: HeatmapCell[];
  total_messages: number;
  time_range: TimeRange;
  timezone: string;
  peak_hour: number | null;
  peak_day: number | null;
}

export interface HeatmapCell {
  day_of_week: number;
  hour: number;
  count: number;
  avg_cost?: number;
  avg_response_time?: number;
}

export interface CostAnalytics {
  data_points: CostDataPoint[];
  total_cost: number;
  average_cost_per_message: number;
  time_range: TimeRange;
  group_by: string;
  cost_by_model: Record<string, number>;
  cost_by_project?: Record<string, number>;
}

export interface CostDataPoint {
  timestamp: string;
  cost: number;
  message_count: number;
}

export interface ModelUsageStats {
  models: ModelUsage[];
  total_models: number;
  time_range: TimeRange;
  most_used: string | null;
  least_used: string | null;
}

export interface ModelUsage {
  model: string;
  message_count: number;
  total_cost: number;
  avg_cost_per_message: number;
  avg_response_time_ms?: number | null;
  avg_tokens_input?: number | null;
  avg_tokens_output?: number | null;
  trend_percentage?: number | null;
}

export const analyticsApi = {
  async getSummary(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS
  ): Promise<AnalyticsSummary> {
    return apiClient.get<AnalyticsSummary>(
      `/analytics/summary?time_range=${timeRange}`
    );
  },

  async getActivityHeatmap(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    timezone: string = 'UTC'
  ): Promise<ActivityHeatmap> {
    return apiClient.get<ActivityHeatmap>(
      `/analytics/activity/heatmap?time_range=${timeRange}&timezone=${timezone}`
    );
  },

  async getCostAnalytics(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    groupBy: 'hour' | 'day' | 'week' | 'month' = 'day',
    projectId?: string
  ): Promise<CostAnalytics> {
    const params = new URLSearchParams({
      time_range: timeRange,
      group_by: groupBy,
    });
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<CostAnalytics>(
      `/analytics/costs?${params.toString()}`
    );
  },

  async getModelUsage(
    timeRange: TimeRange = TimeRange.LAST_30_DAYS,
    projectId?: string
  ): Promise<ModelUsageStats> {
    const params = new URLSearchParams({
      time_range: timeRange,
    });
    if (projectId) params.append('project_id', projectId);

    return apiClient.get<ModelUsageStats>(
      `/analytics/models/usage?${params.toString()}`
    );
  },
};
