import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  aiApi,
  AISettingsUpdate,
  GenerateMetadataRequest,
  GenerateContentRequest,
  TestConnectionRequest,
  CountTokensRequest,
} from '@/api/ai';

// AI Settings hooks
export function useAISettings() {
  return useQuery({
    queryKey: ['ai-settings'],
    queryFn: () => aiApi.getAISettings(),
    staleTime: 30000, // 30 seconds
    retry: (failureCount, error: unknown) => {
      // Don't retry on 404 (settings not configured yet)
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return false;
        }
      }
      return failureCount < 3;
    },
  });
}

export function useUpdateAISettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: AISettingsUpdate) =>
      aiApi.updateAISettings(settings),
    onSuccess: (updatedSettings) => {
      // Update the cache with the new data immediately
      queryClient.setQueryData(['ai-settings'], updatedSettings);

      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['ai-stats'] });

      toast.success('AI settings updated successfully');
    },
    onError: (error: unknown) => {
      console.error('AI settings update failed:', error);
      toast.error('Failed to update AI settings');
    },
  });
}

// Generation hooks
export function useGenerateMetadata() {
  return useMutation({
    mutationFn: (request: GenerateMetadataRequest) =>
      aiApi.generateMetadata(request),
    onError: (error: unknown) => {
      console.error('Metadata generation failed:', error);
      toast.error('Failed to generate metadata');
    },
  });
}

export function useGenerateContent() {
  return useMutation({
    mutationFn: (request: GenerateContentRequest) =>
      aiApi.generateContent(request),
    onError: (error: unknown) => {
      console.error('Content generation failed:', error);
      toast.error('Failed to generate content');
    },
  });
}

// Connection testing hook
export function useTestConnection() {
  return useMutation({
    mutationFn: (request?: TestConnectionRequest) =>
      aiApi.testConnection(request),
    onSuccess: (response) => {
      if (response.success) {
        toast.success('Connection test successful!');
      } else {
        toast.error(`Connection failed: ${response.message}`);
      }
    },
    onError: (error: unknown) => {
      console.error('Connection test failed:', error);
      toast.error('Failed to test connection');
    },
  });
}

// Token counting hook
export function useCountTokens() {
  return useMutation({
    mutationFn: (request: CountTokensRequest) => aiApi.countTokens(request),
    onError: (error: unknown) => {
      console.error('Token counting failed:', error);
      toast.error('Failed to count tokens');
    },
  });
}

// Statistics hook
export function useAIStats() {
  return useQuery({
    queryKey: ['ai-stats'],
    queryFn: () => aiApi.getStats(),
    staleTime: 60000, // 1 minute
    retry: (failureCount, error: unknown) => {
      // Don't retry on 404 (no stats available)
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return false;
        }
      }
      return failureCount < 3;
    },
  });
}

// Helper hook to check if AI is enabled and available
export function useAIAvailable() {
  const { data: settings } = useAISettings();

  return {
    isAvailable: !!settings?.enabled && !!settings?.api_key,
    settings,
  };
}

// Available models hook
export function useAvailableModels() {
  return useQuery({
    queryKey: ['ai-models'],
    queryFn: () => aiApi.getAvailableModels(),
    staleTime: 300000, // 5 minutes
    retry: 1, // Only retry once for model fetching
  });
}
