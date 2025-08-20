import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import {
  importApi,
  ValidateImportResponse,
  CheckConflictsRequest,
  ConflictsResponse,
  ExecuteImportRequest,
  ExecuteImportResponse,
} from '@/api/import-export';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

export function useValidateImport() {
  return useMutation({
    mutationFn: ({ file, dryRun = true }: { file: File; dryRun?: boolean }) =>
      importApi.validateImport(file, dryRun),
    onSuccess: (response: ValidateImportResponse) => {
      if (response.valid) {
        toast.success('File validated successfully');
      } else {
        toast.error('File validation failed. Check the errors.');
      }
    },
    onError: (error: ApiError) => {
      const message = error.message || 'Failed to validate file';
      toast.error(message);
    },
  });
}

export function useCheckConflicts() {
  return useMutation({
    mutationFn: (data: CheckConflictsRequest) => importApi.checkConflicts(data),
    onSuccess: (response: ConflictsResponse) => {
      if (response.conflictsCount > 0) {
        toast(`Found ${response.conflictsCount} conflicts`, {
          icon: '⚠️',
        });
      } else {
        toast.success('No conflicts found');
      }
    },
    onError: (error: ApiError) => {
      const message =
        error.response?.data?.detail || 'Failed to check conflicts';
      toast.error(message);
    },
  });
}

export function useExecuteImport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExecuteImportRequest) => importApi.executeImport(data),
    onSuccess: (response: ExecuteImportResponse) => {
      toast.success(`Import started. Job ID: ${response.jobId}`);
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['messages'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: ApiError) => {
      const message = error.response?.data?.detail || 'Failed to start import';
      toast.error(message);
    },
  });
}

export function useImportProgress(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ['import', jobId],
    queryFn: () => (jobId ? importApi.getImportProgress(jobId) : null),
    enabled: !!jobId && enabled,
    refetchInterval: ({ state }) => {
      // Poll while processing
      if (state.data?.status === 'processing') {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling
    },
    staleTime: 1000, // 1 second
  });
}

export function useRollbackImport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => importApi.rollbackImport(jobId),
    onSuccess: (_, jobId) => {
      toast.success('Import rolled back successfully');
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['import', jobId] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['messages'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (error: ApiError) => {
      const message =
        error.response?.data?.detail || 'Failed to rollback import';
      toast.error(message);
    },
  });
}

// Combined hook for managing the entire import workflow
export function useImportWorkflow() {
  const validateImport = useValidateImport();
  const checkConflicts = useCheckConflicts();
  const executeImport = useExecuteImport();
  const rollbackImport = useRollbackImport();

  return {
    validateImport,
    checkConflicts,
    executeImport,
    rollbackImport,
    // Helper to run the full workflow
    runImport: async (
      file: File,
      fieldMapping: Record<string, string>,
      conflictResolution: ExecuteImportRequest['conflictResolution'],
      options?: ExecuteImportRequest['options']
    ) => {
      try {
        // Step 1: Validate
        const validation = await validateImport.mutateAsync({ file });
        if (!validation.valid) {
          throw new Error('File validation failed');
        }

        // Step 2: Check conflicts
        const conflicts = await checkConflicts.mutateAsync({
          fileId: validation.fileId,
          fieldMapping,
        });

        // Step 3: Execute import
        const importJob = await executeImport.mutateAsync({
          fileId: validation.fileId,
          fieldMapping,
          conflictResolution,
          options,
        });

        return { validation, conflicts, importJob };
      } catch (error) {
        console.error('Import workflow failed:', error);
        throw error;
      }
    },
  };
}
