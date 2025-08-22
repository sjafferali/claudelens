import { useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { useQueryClient } from '@tanstack/react-query';

export interface ImportProgressEvent {
  type: 'import_progress';
  job_id: string;
  progress: {
    current: number;
    total: number;
    percentage: number;
  };
  statistics?: {
    imported: number;
    skipped: number;
    failed: number;
    merged: number;
    replaced: number;
  };
  message?: string;
  completed: boolean;
  error?: string;
  [key: string]: unknown;
}

export interface ExportProgressEvent {
  type: 'export_progress';
  job_id: string;
  progress: {
    current: number;
    total: number;
    percentage: number;
  };
  message?: string;
  completed: boolean;
  error?: string;
  [key: string]: unknown;
}

interface UseImportExportWebSocketOptions {
  onImportProgress?: (event: ImportProgressEvent) => void;
  onExportProgress?: (event: ExportProgressEvent) => void;
}

export function useImportExportWebSocket(
  options: UseImportExportWebSocketOptions = {}
) {
  const queryClient = useQueryClient();
  const { onImportProgress, onExportProgress } = options;

  // Store callback refs to avoid recreating WebSocket on every render
  const importCallbackRef = useRef(onImportProgress);
  const exportCallbackRef = useRef(onExportProgress);

  useEffect(() => {
    importCallbackRef.current = onImportProgress;
    exportCallbackRef.current = onExportProgress;
  }, [onImportProgress, onExportProgress]);

  const handleMessage = useCallback(
    (message: unknown) => {
      const msg = message as { type: string; [key: string]: unknown };
      if (msg.type === 'import_progress') {
        const event = msg as unknown as ImportProgressEvent;

        // Update React Query cache with latest progress
        queryClient.setQueryData(
          ['import', event.job_id],
          (oldData: unknown) => ({
            ...(oldData as Record<string, unknown>),
            status: event.completed ? 'completed' : 'processing',
            progress: event.progress,
            statistics:
              event.statistics ||
              (oldData as Record<string, unknown>)?.statistics,
            errors: event.error
              ? [{ message: event.error }]
              : (oldData as Record<string, unknown>)?.errors,
          })
        );

        // Call the callback if provided
        importCallbackRef.current?.(event);
      } else if (msg.type === 'export_progress') {
        const event = msg as unknown as ExportProgressEvent;

        // Update React Query cache with latest progress
        queryClient.setQueryData(
          ['export', event.job_id, 'status'],
          (oldData: unknown) => ({
            ...(oldData as Record<string, unknown>),
            status: event.completed ? 'completed' : 'processing',
            progress: event.progress,
            errors: event.error
              ? [{ message: event.error }]
              : (oldData as Record<string, unknown>)?.errors,
          })
        );

        // Call the callback if provided
        exportCallbackRef.current?.(event);
      }
    },
    [queryClient]
  );

  const { isConnected, error } = useWebSocket('/ws/stats', {
    onMessage: handleMessage,
  });

  return {
    isConnected,
    error,
  };
}
