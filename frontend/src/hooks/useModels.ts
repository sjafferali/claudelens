import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export function useAvailableModels() {
  return useQuery({
    queryKey: ['available-models'],
    queryFn: async () => {
      // Fetch model usage stats to get all available models
      const response = await apiClient.get<{
        models: Array<{ model: string; message_count: number }>;
      }>('/analytics/models/usage');

      // Extract unique models
      const models = response.models
        .map((m) => m.model)
        .filter(Boolean)
        .sort();

      return models;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
