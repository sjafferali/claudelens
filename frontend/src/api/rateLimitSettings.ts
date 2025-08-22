import { apiClient } from './client';

export interface RateLimitSettings {
  export_limit_per_hour: number;
  import_limit_per_hour: number;
  backup_limit_per_hour: number;
  restore_limit_per_hour: number;
  max_upload_size_mb: number;
  max_export_size_mb: number;
  max_backup_size_gb: number;
  max_page_size: number;
  default_page_size: number;
  rate_limit_window_hours: number;
  rate_limiting_enabled: boolean;
  updated_at: string;
  updated_by?: string;
  current_usage?: {
    export: {
      current: number;
      limit: number | 'unlimited';
      remaining: number | 'unlimited';
      reset_in_seconds?: number;
    };
    import: {
      current: number;
      limit: number | 'unlimited';
      remaining: number | 'unlimited';
      reset_in_seconds?: number;
    };
    backup: {
      current: number;
      limit: number | 'unlimited';
      remaining: number | 'unlimited';
      reset_in_seconds?: number;
    };
    restore: {
      current: number;
      limit: number | 'unlimited';
      remaining: number | 'unlimited';
      reset_in_seconds?: number;
    };
  };
}

export interface RateLimitSettingsUpdate {
  export_limit_per_hour?: number;
  import_limit_per_hour?: number;
  backup_limit_per_hour?: number;
  restore_limit_per_hour?: number;
  max_upload_size_mb?: number;
  max_export_size_mb?: number;
  max_backup_size_gb?: number;
  max_page_size?: number;
  default_page_size?: number;
  rate_limit_window_hours?: number;
  rate_limiting_enabled?: boolean;
}

export interface RateLimitUsage {
  export: {
    current: number;
    limit: number | 'unlimited';
    remaining: number | 'unlimited';
    reset_in_seconds?: number;
  };
  import: {
    current: number;
    limit: number | 'unlimited';
    remaining: number | 'unlimited';
    reset_in_seconds?: number;
  };
  backup: {
    current: number;
    limit: number | 'unlimited';
    remaining: number | 'unlimited';
    reset_in_seconds?: number;
  };
  restore: {
    current: number;
    limit: number | 'unlimited';
    remaining: number | 'unlimited';
    reset_in_seconds?: number;
  };
}

export const rateLimitSettingsApi = {
  async getSettings(): Promise<RateLimitSettings> {
    return apiClient.get('/settings/rate-limit-settings');
  },

  async updateSettings(
    updates: RateLimitSettingsUpdate
  ): Promise<RateLimitSettings> {
    return apiClient.put('/settings/rate-limit-settings', updates);
  },

  async resetLimits(
    userId: string = 'anonymous',
    limitType?: string
  ): Promise<void> {
    const params = new URLSearchParams({ user_id: userId });
    if (limitType) {
      params.append('limit_type', limitType);
    }
    return apiClient.post(
      `/settings/rate-limit-settings/reset?${params.toString()}`
    );
  },

  async getUsage(userId: string = 'anonymous'): Promise<RateLimitUsage> {
    return apiClient.get(
      `/settings/rate-limit-settings/usage?user_id=${userId}`
    );
  },
};
