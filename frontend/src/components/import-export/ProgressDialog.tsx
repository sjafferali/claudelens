import * as React from 'react';
import { Button } from '@/components/common/Button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { useExportStatus, useCancelExport } from '@/hooks/useExport';
import { useImportProgress, useRollbackImport } from '@/hooks/useImport';
import { useImportExportWebSocket } from '@/hooks/useImportExportWebSocket';
import type {
  ExportStatusResponse,
  ImportProgressResponse,
} from '@/api/import-export';

// Type guards for error types
type ExportError = { code: string; message: string; details?: unknown };
type ImportError = { itemId: string; error: string; details?: string };

function isImportError(error: ExportError | ImportError): error is ImportError {
  return 'itemId' in error;
}
import {
  CheckCircle,
  AlertCircle,
  X,
  RotateCcw,
  Clock,
  FileText,
  MessageSquare,
  TrendingUp,
} from 'lucide-react';

interface ProgressDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobId: string | null;
  jobType: 'export' | 'import';
  onComplete?: () => void;
}

export const ProgressDialog: React.FC<ProgressDialogProps> = ({
  open,
  onOpenChange,
  jobId,
  jobType,
  onComplete,
}) => {
  const [showSuccessState, setShowSuccessState] = React.useState(false);

  // Hooks based on job type
  const exportStatus = useExportStatus(
    jobType === 'export' ? jobId : null,
    open && jobType === 'export'
  );
  const importProgress = useImportProgress(
    jobType === 'import' ? jobId : null,
    open && jobType === 'import'
  );

  const cancelExport = useCancelExport();
  const rollbackImport = useRollbackImport();

  // Use WebSocket for real-time updates
  useImportExportWebSocket({
    onImportProgress: React.useCallback(
      (event: {
        job_id: string;
        completed: boolean;
        [key: string]: unknown;
      }) => {
        if (event.job_id === jobId && event.completed) {
          // Show success state for 3 seconds before closing
          setShowSuccessState(true);
          setTimeout(() => {
            onComplete?.();
          }, 3000);
        }
      },
      [jobId, onComplete]
    ),
    onExportProgress: React.useCallback(
      (event: {
        job_id: string;
        completed: boolean;
        [key: string]: unknown;
      }) => {
        if (event.job_id === jobId && event.completed) {
          // Show success state for 3 seconds before closing
          setShowSuccessState(true);
          setTimeout(() => {
            onComplete?.();
          }, 3000);
        }
      },
      [jobId, onComplete]
    ),
  });

  // Get current job data based on type
  const jobData =
    jobType === 'export'
      ? (exportStatus.data as ExportStatusResponse | null)
      : (importProgress.data as ImportProgressResponse | null);
  const isLoading =
    jobType === 'export' ? exportStatus.isLoading : importProgress.isLoading;

  // Handle job completion - don't auto-close, let the WebSocket handler do it
  React.useEffect(() => {
    if (jobData?.status === 'completed' && showSuccessState) {
      // Success state is already set by WebSocket handler
      // which will call onComplete after delay
    }
  }, [jobData?.status, showSuccessState]);

  const handleCancel = async () => {
    if (!jobId) return;

    try {
      if (jobType === 'export') {
        await cancelExport.mutateAsync(jobId);
      } else {
        await rollbackImport.mutateAsync(jobId);
      }
      onOpenChange(false);
    } catch (error) {
      console.error(`${jobType} operation failed:`, error);
    }
  };

  const getStatusIcon = () => {
    if (!jobData) return <Clock className="w-6 h-6 text-gray-400" />;

    switch (jobData.status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      case 'cancelled':
        return <X className="w-6 h-6 text-gray-500" />;
      case 'partial':
        return <AlertCircle className="w-6 h-6 text-yellow-500" />;
      default:
        return (
          <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        );
    }
  };

  const getStatusText = () => {
    if (!jobData) return 'Loading...';

    switch (jobData.status) {
      case 'queued':
        return 'Queued';
      case 'processing':
        return jobType === 'export' ? 'Exporting...' : 'Importing...';
      case 'completed':
        return jobType === 'export' ? 'Export Complete' : 'Import Complete';
      case 'failed':
        return jobType === 'export' ? 'Export Failed' : 'Import Failed';
      case 'cancelled':
        return jobType === 'export' ? 'Export Cancelled' : 'Import Cancelled';
      case 'partial':
        return 'Import Partially Complete';
      default:
        return 'Processing...';
    }
  };

  const getProgressPercentage = () => {
    if (!jobData) return 0;

    if (jobType === 'export') {
      return jobData.progress?.percentage || 0;
    } else {
      return jobData.progress?.percentage || 0;
    }
  };

  const getCurrentItem = () => {
    if (!jobData) return null;

    if (jobType === 'export') {
      return (jobData as ExportStatusResponse).currentItem;
    } else {
      return (jobData as ImportProgressResponse).progress?.currentItem;
    }
  };

  const canCancel = () => {
    return jobData && ['queued', 'processing'].includes(jobData.status);
  };

  const canRollback = () => {
    return jobType === 'import' && jobData && jobData.status === 'completed';
  };

  if (isLoading && !jobData) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <div className="flex items-center justify-center h-32">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            {getStatusIcon()}
            <span>
              {jobType === 'export' ? 'Export Progress' : 'Import Progress'}
            </span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Show success message when complete */}
          {showSuccessState && jobData?.status === 'completed' && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-8 h-8 text-green-500" />
                <div>
                  <h3 className="font-semibold text-green-900 dark:text-green-100">
                    {jobType === 'export' ? 'Export' : 'Import'} Completed
                    Successfully!
                  </h3>
                  {jobType === 'import' &&
                    jobData &&
                    'statistics' in jobData && (
                      <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                        {
                          (jobData as ImportProgressResponse).statistics
                            .imported
                        }{' '}
                        items imported,{' '}
                        {(jobData as ImportProgressResponse).statistics.skipped}{' '}
                        skipped
                      </p>
                    )}
                  {jobType === 'export' && jobData && 'fileInfo' in jobData && (
                    <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                      Export ready for download
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Status and Progress */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {getStatusText()}
              </span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {getProgressPercentage().toFixed(0)}%
              </span>
            </div>

            <Progress value={getProgressPercentage()} className="h-3" />

            {getCurrentItem() && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-medium">Current: </span>
                {getCurrentItem()}
              </div>
            )}
          </div>

          {/* Progress Details */}
          {jobData && (
            <div className="grid grid-cols-2 gap-4">
              {/* Export Details */}
              {jobType === 'export' &&
                (jobData as ExportStatusResponse).progress && (
                  <>
                    <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <FileText className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Items
                        </span>
                      </div>
                      <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                        {(
                          jobData as ExportStatusResponse
                        ).progress!.current.toLocaleString()}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        /{' '}
                        {(
                          jobData as ExportStatusResponse
                        ).progress!.total.toLocaleString()}
                      </span>
                    </div>

                    {(jobData as ExportStatusResponse).fileInfo && (
                      <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                        <div className="flex items-center space-x-2 mb-1">
                          <MessageSquare className="w-4 h-4 text-green-500" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Messages
                          </span>
                        </div>
                        <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                          {(
                            jobData as ExportStatusResponse
                          ).fileInfo!.messagesCount?.toLocaleString() || '0'}
                        </span>
                      </div>
                    )}
                  </>
                )}

              {/* Import Details */}
              {jobType === 'import' &&
                (jobData as ImportProgressResponse).statistics && (
                  <>
                    <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Imported
                        </span>
                      </div>
                      <span className="text-lg font-bold text-green-700 dark:text-green-400">
                        {(
                          jobData as ImportProgressResponse
                        ).statistics.imported.toLocaleString()}
                      </span>
                    </div>

                    <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                      <div className="flex items-center space-x-2 mb-1">
                        <Clock className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Skipped
                        </span>
                      </div>
                      <span className="text-lg font-bold text-yellow-700 dark:text-yellow-400">
                        {(
                          jobData as ImportProgressResponse
                        ).statistics.skipped.toLocaleString()}
                      </span>
                    </div>

                    {(jobData as ImportProgressResponse).statistics.failed >
                      0 && (
                      <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                        <div className="flex items-center space-x-2 mb-1">
                          <AlertCircle className="w-4 h-4 text-red-500" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Failed
                          </span>
                        </div>
                        <span className="text-lg font-bold text-red-700 dark:text-red-400">
                          {(
                            jobData as ImportProgressResponse
                          ).statistics.failed.toLocaleString()}
                        </span>
                      </div>
                    )}

                    {(jobData as ImportProgressResponse).statistics.merged >
                      0 && (
                      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                        <div className="flex items-center space-x-2 mb-1">
                          <TrendingUp className="w-4 h-4 text-blue-500" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Merged
                          </span>
                        </div>
                        <span className="text-lg font-bold text-blue-700 dark:text-blue-400">
                          {(
                            jobData as ImportProgressResponse
                          ).statistics.merged.toLocaleString()}
                        </span>
                      </div>
                    )}
                  </>
                )}
            </div>
          )}

          {/* Errors */}
          {jobData?.errors && jobData.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-900/20 dark:border-red-800">
              <h4 className="font-medium text-red-900 dark:text-red-100 mb-2">
                Errors ({jobData.errors.length})
              </h4>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {jobData.errors.slice(0, 3).map((error, index) => (
                  <div
                    key={index}
                    className="text-sm text-red-700 dark:text-red-300"
                  >
                    {isImportError(error as ExportError | ImportError) ? (
                      <>
                        <span className="font-medium">
                          Item {(error as ImportError).itemId}:
                        </span>{' '}
                        {(error as ImportError).error}
                      </>
                    ) : (
                      <>
                        <span className="font-medium">
                          {(error as ExportError).code || 'Error'}:
                        </span>{' '}
                        {(error as ExportError).message}
                      </>
                    )}
                  </div>
                ))}
                {jobData.errors.length > 3 && (
                  <div className="text-sm text-red-600 dark:text-red-400">
                    ... and {jobData.errors.length - 3} more errors
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <div>
              {canRollback() && (
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  disabled={rollbackImport.isPending}
                  className="text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-600"
                >
                  {rollbackImport.isPending ? (
                    <div className="w-4 h-4 border-2 border-red-300 border-t-red-600 rounded-full animate-spin mr-2" />
                  ) : (
                    <RotateCcw className="w-4 h-4 mr-2" />
                  )}
                  Rollback
                </Button>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {canCancel() && (
                <Button
                  variant="outline"
                  onClick={handleCancel}
                  disabled={cancelExport.isPending || rollbackImport.isPending}
                >
                  {cancelExport.isPending || rollbackImport.isPending ? (
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin mr-2" />
                  ) : (
                    <X className="w-4 h-4 mr-2" />
                  )}
                  Cancel
                </Button>
              )}

              <Button onClick={() => onOpenChange(false)}>
                {jobData?.status === 'completed' ? 'Close' : 'Hide'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
