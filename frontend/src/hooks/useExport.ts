import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  exportApi,
  CreateExportRequest,
  CreateExportResponse,
} from '@/api/import-export';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

export function useCreateExport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateExportRequest) => exportApi.createExport(data),
    onSuccess: (response: CreateExportResponse) => {
      toast.success(`Export job created. Job ID: ${response.jobId}`);
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to create export';
      toast.error(message);
    },
  });
}

export function useExportStatus(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['export', jobId],
    queryFn: () => (jobId ? exportApi.getExportStatus(jobId) : null),
    enabled: !!jobId && enabled,
    refetchInterval: ({ state }) => {
      // Poll while processing
      if (
        state.data?.status === 'processing' ||
        state.data?.status === 'queued'
      ) {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling
    },
    staleTime: 1000, // 1 second
  });
}

export function useDownloadExport() {
  return useMutation({
    mutationFn: (jobId: string) => exportApi.downloadExport(jobId),
    onSuccess: () => {
      toast.success('Export downloaded successfully');
    },
    onError: (error: ApiError) => {
      const message = error.message || 'Failed to download export';
      toast.error(message);
    },
  });
}

export function useCancelExport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => exportApi.cancelExport(jobId),
    onSuccess: (_, jobId) => {
      toast.success('Export cancelled');
      queryClient.invalidateQueries({ queryKey: ['export', jobId] });
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to cancel export';
      toast.error(message);
    },
  });
}

export function useDeleteExport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => exportApi.deleteExport(jobId),
    onSuccess: () => {
      toast.success('Export deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to delete export';
      toast.error(message);
    },
  });
}

export function useExportsList(params?: {
  page?: number;
  size?: number;
  sort?: string;
  status?: string;
}) {
  return useQuery({
    queryKey: ['exports', params],
    queryFn: () => exportApi.listExports(params),
    staleTime: 30000, // 30 seconds
  });
}

// Hook for managing export progress via WebSocket
export function useExportProgress(jobId: string | null) {
  // This would integrate with the WebSocket connection
  // Implementation depends on the WebSocket hook structure
  // For now, we can use the polling approach via useExportStatus
  return useExportStatus(jobId);
}
