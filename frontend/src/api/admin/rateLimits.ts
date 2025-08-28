import { apiClient } from '../client';

export interface RateLimitSettings {
  // General HTTP rate limits
  http_rate_limit_enabled: boolean;
  http_calls_per_minute: number;
  http_rate_limit_window_seconds: number;

  // CLI/Ingestion specific limits
  ingest_enabled: boolean;
  ingest_rate_limit_per_hour: number;
  ingest_max_batch_size: number;
  ingest_max_file_size_mb: number;

  // AI/LLM rate limits
  ai_rate_limit_enabled: boolean;
  ai_rate_limit_per_minute: number;
  ai_max_tokens: number;

  // Export/Import limits
  export_limit_per_hour: number;
  import_limit_per_hour: number;

  // Backup/Restore limits
  backup_limit_per_hour: number;
  restore_limit_per_hour: number;

  // File size limits
  max_upload_size_mb: number;
  max_export_size_mb: number;
  max_backup_size_gb: number;

  // Pagination limits
  max_page_size: number;
  default_page_size: number;

  // WebSocket limits
  websocket_enabled: boolean;
  websocket_max_connections_per_user: number;
  websocket_message_rate_per_second: number;

  // Search limits
  search_rate_limit_per_minute: number;
  search_max_results: number;

  // Analytics limits
  analytics_rate_limit_per_minute: number;
  analytics_max_date_range_days: number;

  // Rate limit window
  rate_limit_window_hours: number;

  // Enable/disable rate limiting globally
  rate_limiting_enabled: boolean;

  // Metadata
  updated_at?: string;
  updated_by?: string;
}

export interface RateLimitUsageStats {
  current: number;
  limit: number | 'unlimited';
  remaining: number | 'unlimited';
  reset_in_seconds?: number;
}

export interface UserRateLimitUsage {
  user_id: string;
  username: string;
  usage: UserUsageData;
}

export interface UserUsageData {
  export: RateLimitUsageStats;
  import: RateLimitUsageStats;
  backup: RateLimitUsageStats;
  restore: RateLimitUsageStats;
  [key: string]: RateLimitUsageStats; // Allow additional rate limit types
}

export const adminRateLimitsApi = {
  getSettings: async (): Promise<RateLimitSettings> => {
    return await apiClient.get<RateLimitSettings>('/admin/rate-limits');
  },

  updateSettings: async (
    settings: RateLimitSettings
  ): Promise<RateLimitSettings> => {
    return await apiClient.put<RateLimitSettings>(
      '/admin/rate-limits',
      settings
    );
  },

  resetToDefaults: async (): Promise<{ message: string }> => {
    return await apiClient.post<{ message: string }>(
      '/admin/rate-limits/reset'
    );
  },

  getUsageStats: async (
    userId?: string
  ): Promise<
    { users: UserRateLimitUsage[] } | { user_id: string; usage: UserUsageData }
  > => {
    const params = userId ? { user_id: userId } : {};
    return await apiClient.get<
      | { users: UserRateLimitUsage[] }
      | { user_id: string; usage: UserUsageData }
    >('/admin/rate-limits/usage', {
      params,
    });
  },

  resetUserLimits: async (
    userId: string,
    limitType?: string
  ): Promise<{ message: string }> => {
    const params = limitType ? { limit_type: limitType } : {};
    return await apiClient.post<{ message: string }>(
      `/admin/rate-limits/reset-user/${userId}`,
      null,
      { params }
    );
  },

  getTopUsers: async (
    limit: number = 10,
    hours: number = 24
  ): Promise<{
    time_range_hours: number;
    top_users: Array<{
      user_id: string;
      username: string;
      total_requests: number;
      total_blocked: number;
      avg_usage_rate: number;
    }>;
  }> => {
    return await apiClient.get<{
      time_range_hours: number;
      top_users: Array<{
        user_id: string;
        username: string;
        total_requests: number;
        total_blocked: number;
        avg_usage_rate: number;
      }>;
    }>('/admin/rate-limits/top-users', {
      params: { limit, hours },
    });
  },

  cleanupUsageData: async (
    retentionDays: number = 30
  ): Promise<{
    message: string;
    deleted_count: number;
  }> => {
    return await apiClient.post<{
      message: string;
      deleted_count: number;
    }>('/admin/rate-limits/cleanup-usage-data', null, {
      params: { retention_days: retentionDays },
    });
  },
};
