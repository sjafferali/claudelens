import * as React from 'react';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import {
  backupApi,
  CreateRestoreRequest,
  CreateRestoreResponse,
} from '@/api/backupApi';
import { AlertCircle, Info, RotateCcw, Database } from 'lucide-react';
import toast from 'react-hot-toast';

interface RestoreDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  backupId: string;
  onRestoreStarted?: (jobId: string) => void;
}

export const RestoreDialog: React.FC<RestoreDialogProps> = ({
  open,
  onOpenChange,
  backupId,
  onRestoreStarted,
}) => {
  const [restoreOptions, setRestoreOptions] = useState<CreateRestoreRequest>({
    backup_id: backupId,
    mode: 'full',
    conflict_resolution: 'skip',
  });

  // Preview backup contents
  const {
    data: preview,
    isLoading: previewLoading,
    error: previewError,
  } = useQuery({
    queryKey: ['backup-preview', backupId],
    queryFn: () => backupApi.previewBackup(backupId),
    enabled: open && !!backupId,
  });

  // Restore mutation
  const restoreMutation = useMutation({
    mutationFn: (request: CreateRestoreRequest) =>
      backupApi.createRestore(request),
    onSuccess: (response: CreateRestoreResponse) => {
      toast.success(response.message || 'Restore started successfully');
      onRestoreStarted?.(response.job_id);
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      const errorMessage =
        (error as Error & { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail || 'Failed to start restore';
      toast.error(errorMessage);
    },
  });

  const handleRestore = () => {
    if (!preview?.can_restore) {
      toast.error('This backup cannot be restored');
      return;
    }
    restoreMutation.mutate(restoreOptions);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5" />
            Restore Backup
          </DialogTitle>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Configure how you want to restore this backup. Preview the contents
            below before proceeding.
          </p>
        </DialogHeader>

        {previewLoading ? (
          <div className="py-8">
            <Loading />
          </div>
        ) : previewError ? (
          <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-400">
                Error
              </h4>
              <p className="text-sm text-red-600 dark:text-red-300">
                Failed to load backup preview. Please try again.
              </p>
            </div>
          </div>
        ) : preview ? (
          <div className="space-y-6">
            {/* Backup Info */}
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <Database className="w-4 h-4" />
                Backup Information
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">
                    Name:
                  </span>{' '}
                  <span className="font-medium">{preview.name}</span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">
                    Type:
                  </span>{' '}
                  <span className="font-medium uppercase">{preview.type}</span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">
                    Size:
                  </span>{' '}
                  <span className="font-medium">
                    {formatBytes(preview.size_bytes)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">
                    Created:
                  </span>{' '}
                  <span className="font-medium">
                    {new Date(preview.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Backup Contents */}
            {preview.contents && (
              <div className="space-y-2">
                <h4 className="font-medium">Contents Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {preview.contents.projects_count > 0 && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {preview.contents.projects_count}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Projects
                      </div>
                    </div>
                  )}
                  {preview.contents.sessions_count > 0 && (
                    <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {preview.contents.sessions_count}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Sessions
                      </div>
                    </div>
                  )}
                  {preview.contents.messages_count > 0 && (
                    <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {preview.contents.messages_count}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Messages
                      </div>
                    </div>
                  )}
                  {preview.contents.prompts_count > 0 && (
                    <div className="bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                        {preview.contents.prompts_count}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Prompts
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Warnings */}
            {preview.warnings && preview.warnings.length > 0 && (
              <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-md dark:bg-yellow-900/20 dark:border-yellow-800">
                <Info className="h-4 w-4 text-yellow-500" />
                <div>
                  <h4 className="font-medium text-yellow-800 dark:text-yellow-400">
                    Warnings
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-yellow-600 dark:text-yellow-300">
                    {preview.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Restore Options */}
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Restore Mode
                </label>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="mode"
                      value="full"
                      checked={restoreOptions.mode === 'full'}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          mode: e.target.value as
                            | 'full'
                            | 'selective'
                            | 'merge',
                        }))
                      }
                      className="text-blue-600"
                    />
                    <span className="text-sm">
                      Full Restore - Replace all existing data
                    </span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="mode"
                      value="merge"
                      checked={restoreOptions.mode === 'merge'}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          mode: e.target.value as
                            | 'full'
                            | 'selective'
                            | 'merge',
                        }))
                      }
                      className="text-blue-600"
                    />
                    <span className="text-sm">
                      Merge - Add to existing data
                    </span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="mode"
                      value="selective"
                      checked={restoreOptions.mode === 'selective'}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          mode: e.target.value as
                            | 'full'
                            | 'selective'
                            | 'merge',
                        }))
                      }
                      className="text-blue-600"
                      disabled
                    />
                    <span className="text-sm text-gray-400">
                      Selective - Choose what to restore (Coming Soon)
                    </span>
                  </label>
                </div>
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="conflict-resolution"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Conflict Resolution
                </label>
                <select
                  id="conflict-resolution"
                  value={restoreOptions.conflict_resolution}
                  onChange={(e) =>
                    setRestoreOptions((prev) => ({
                      ...prev,
                      conflict_resolution: e.target.value as
                        | 'skip'
                        | 'overwrite'
                        | 'rename'
                        | 'merge',
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                >
                  <option value="skip">Skip Existing</option>
                  <option value="overwrite">Overwrite Existing</option>
                  <option value="rename">Rename Duplicates</option>
                  <option value="merge">Merge Data</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  How to handle conflicts when restoring data that already
                  exists
                </p>
              </div>
            </div>

            {!preview.can_restore && (
              <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800">
                <AlertCircle className="h-4 w-4 text-red-500" />
                <div>
                  <h4 className="font-medium text-red-800 dark:text-red-400">
                    Cannot Restore
                  </h4>
                  <p className="text-sm text-red-600 dark:text-red-300">
                    This backup cannot be restored. It may be corrupted or
                    incompatible.
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : null}

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleRestore}
            disabled={
              previewLoading ||
              !preview?.can_restore ||
              restoreMutation.isPending ||
              restoreOptions.mode === 'selective'
            }
          >
            {restoreMutation.isPending ? (
              <>
                <Loading className="mr-2 h-4 w-4" />
                Starting Restore...
              </>
            ) : (
              <>
                <RotateCcw className="mr-2 h-4 w-4" />
                Start Restore
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
