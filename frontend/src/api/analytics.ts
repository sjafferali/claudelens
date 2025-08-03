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
  data: HeatmapCell[];
  time_range: TimeRange;
}

export interface HeatmapCell {
  day_of_week: number;
  hour: number;
  count: number;
  avg_cost?: number;
  avg_response_time?: number;
}

export interface CostAnalytics {
  data: CostDataPoint[];
  total: number;
  time_range: TimeRange;
}

export interface CostDataPoint {
  timestamp: string;
  cost: number;
  message_count: number;
}

export interface ModelUsageStats {
  models: ModelUsage[];
  time_range: TimeRange;
}

export interface ModelUsage {
  model: string;
  message_count: number;
  total_cost: number;
  avg_response_time: number;
  input_tokens: number;
  output_tokens: number;
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
