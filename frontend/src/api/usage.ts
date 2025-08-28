import { apiClient } from './client';

export interface StorageBreakdown {
  sessions: number;
  messages: number;
  projects: number;
}

export interface ResourceCounts {
  projects: number;
  sessions: number;
  messages: number;
}

export interface UsageMetrics {
  storage: {
    total_bytes: number;
    breakdown: StorageBreakdown;
  };
  counts: ResourceCounts;
  details: {
    sessions: {
      total_size: number;
      document_count: number;
      avg_size: number;
      max_size: number;
    };
    messages: {
      total_size: number;
      document_count: number;
      avg_size: number;
      max_size: number;
    };
    projects: {
      total_size: number;
      document_count: number;
      avg_size: number;
      max_size: number;
    };
  };
}

export const usageApi = {
  async getMyUsageMetrics(): Promise<UsageMetrics> {
    return apiClient.get('/auth/me/usage');
  },
};
