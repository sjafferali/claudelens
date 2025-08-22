import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  backupApi,
  CreateBackupRequest,
  CreateBackupResponse,
  CreateRestoreRequest,
  CreateRestoreResponse,
  ListBackupsParams,
  BackupMetadata,
} from '@/api/backupApi';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

export function useCreateBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateBackupRequest) => backupApi.createBackup(data),
    onSuccess: (response: CreateBackupResponse) => {
      toast.success(
        response.message || `Backup job created. Job ID: ${response.job_id}`
      );
      queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to create backup';
      toast.error(message);
    },
  });
}

export function useBackups(params?: ListBackupsParams) {
  return useQuery({
    queryKey: ['backups', params],
    queryFn: () => backupApi.listBackups(params),
    staleTime: 30000, // 30 seconds
    refetchInterval: ({ state }) => {
      // Auto-refresh if there are in-progress backups
      const hasInProgress = state.data?.items?.some((item: BackupMetadata) =>
        ['pending', 'in_progress'].includes(item.status)
      );
      return hasInProgress ? 5000 : false; // Poll every 5 seconds
    },
  });
}

export function useBackupDetails(backupId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['backup', backupId],
    queryFn: () => (backupId ? backupApi.getBackup(backupId) : null),
    enabled: !!backupId && enabled,
    staleTime: 60000, // 1 minute
  });
}

export function useDeleteBackup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (backupId: string) => backupApi.deleteBackup(backupId),
    onSuccess: (response) => {
      toast.success(response.message || 'Backup deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to delete backup';
      toast.error(message);
    },
  });
}

export function useDownloadBackup() {
  return useMutation({
    mutationFn: (backupId: string) => backupApi.downloadBackup(backupId),
    onSuccess: () => {
      toast.success('Download started');
    },
    onError: (error: ApiError) => {
      const message =
        error.response?.data?.detail || 'Failed to download backup';
      toast.error(message);
    },
  });
}

export function useCreateRestore() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateRestoreRequest) => backupApi.createRestore(data),
    onSuccess: (response: CreateRestoreResponse) => {
      toast.success(
        response.message || `Restore job created. Job ID: ${response.job_id}`
      );
      queryClient.invalidateQueries({ queryKey: ['restores'] });
    },
    onError: (error: ApiError) => {
      const message =
        error.response?.data?.detail || 'Failed to create restore';
      toast.error(message);
    },
  });
}

export function useUploadAndRestore() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { file: File; options?: Record<string, unknown> }) =>
      backupApi.uploadAndRestore(data.file, data.options),
    onSuccess: (response: CreateRestoreResponse) => {
      toast.success(
        response.message || `Restore job created. Job ID: ${response.job_id}`
      );
      queryClient.invalidateQueries({ queryKey: ['restores'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to start restore';
      toast.error(message);
    },
  });
}

export function useRestoreStatus(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['restore', jobId],
    queryFn: () => (jobId ? backupApi.getRestoreStatus(jobId) : null),
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

export function usePreviewBackup(backupId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['backup-preview', backupId],
    queryFn: () => (backupId ? backupApi.previewBackup(backupId) : null),
    enabled: !!backupId && enabled,
    staleTime: 300000, // 5 minutes
  });
}
