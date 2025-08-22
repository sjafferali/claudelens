import * as React from 'react';
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/common/Button';
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  FileDown,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { backupApi, RestoreProgressResponse } from '@/api/backupApi';

interface BackupProgressProps {
  jobId: string;
  jobType: 'backup' | 'restore';
  onComplete?: () => void;
  onError?: (error: string) => void;
  className?: string;
}

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />;
    case 'cancelled':
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    case 'processing':
    case 'queued':
      return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    default:
      return <Clock className="w-5 h-5 text-gray-500" />;
  }
};

const StatusBadge = ({ status }: { status: string }) => {
  const statusColors = {
    completed:
      'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    cancelled:
      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    processing:
      'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    queued: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
        statusColors[status as keyof typeof statusColors] || statusColors.queued
      )}
    >
      <StatusIcon status={status} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

export const BackupProgress: React.FC<BackupProgressProps> = ({
  jobId,
  jobType,
  onComplete,
  onError,
  className,
}) => {
  const [hasCompleted, setHasCompleted] = useState(false);

  // Poll for job status
  const { data, error, refetch } = useQuery<RestoreProgressResponse>({
    queryKey: [
      jobType === 'restore' ? 'restore-status' : 'backup-status',
      jobId,
    ],
    queryFn: () =>
      jobType === 'restore'
        ? backupApi.getRestoreStatus(jobId)
        : // For backup jobs, we'd need a similar endpoint - using restore for now
          backupApi.getRestoreStatus(jobId),
    refetchInterval: ({ state }) => {
      if (!state.data) return 2000;
      const isComplete = ['completed', 'failed', 'cancelled'].includes(
        state.data.status || ''
      );
      return isComplete ? false : 2000;
    },
    enabled: !!jobId,
  });

  useEffect(() => {
    if (data && !hasCompleted) {
      if (data.status === 'completed') {
        setHasCompleted(true);
        onComplete?.();
      } else if (data.status === 'failed') {
        setHasCompleted(true);
        const errorMsg = data.errors?.[0]?.error || 'Operation failed';
        onError?.(errorMsg);
      }
    }
  }, [data, hasCompleted, onComplete, onError]);

  if (error) {
    return (
      <div
        className={cn(
          'bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-900/20 dark:border-red-800',
          className
        )}
      >
        <div className="flex items-center gap-2">
          <XCircle className="h-4 w-4 text-red-500" />
          <h4 className="font-medium text-red-800 dark:text-red-400">Error</h4>
        </div>
        <p className="text-sm text-red-600 dark:text-red-300 mt-1">
          Failed to load job status. Please refresh the page.
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const progress = data.progress;
  const statistics = data.statistics;
  const isComplete = ['completed', 'failed', 'cancelled'].includes(data.status);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            {jobType === 'backup' ? (
              <FileDown className="w-5 h-5" />
            ) : (
              <RotateCcw className="w-5 h-5" />
            )}
            {jobType === 'backup' ? 'Backup' : 'Restore'} Progress
          </span>
          <StatusBadge status={data.status} />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        {!isComplete && progress && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
              <span>
                {progress.processed || 0} / {progress.total || 0} items
              </span>
              <span>{progress.percentage || 0}%</span>
            </div>
            <Progress value={progress.percentage || 0} className="h-2" />
            {progress.current_item && (
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                Processing: {progress.current_item}
              </p>
            )}
          </div>
        )}

        {/* Statistics */}
        {statistics && Object.keys(statistics).length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {statistics.imported !== undefined && (
              <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {statistics.imported}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Imported
                </div>
              </div>
            )}
            {statistics.skipped !== undefined && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                <div className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                  {statistics.skipped}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Skipped
                </div>
              </div>
            )}
            {statistics.failed !== undefined && statistics.failed > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                <div className="text-lg font-bold text-red-600 dark:text-red-400">
                  {statistics.failed}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Failed
                </div>
              </div>
            )}
            {statistics.merged !== undefined && (
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {statistics.merged}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Merged
                </div>
              </div>
            )}
          </div>
        )}

        {/* Errors */}
        {data.errors && data.errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 dark:bg-red-900/20 dark:border-red-800">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <h4 className="font-medium text-red-800 dark:text-red-400">
                Errors Occurred
              </h4>
            </div>
            <ul className="list-disc list-inside space-y-1">
              {data.errors.slice(0, 3).map((error, index) => (
                <li
                  key={index}
                  className="text-sm text-red-600 dark:text-red-300"
                >
                  {error.error || error.details}
                </li>
              ))}
              {data.errors.length > 3 && (
                <li className="text-sm text-red-600 dark:text-red-300">
                  ...and {data.errors.length - 3} more errors
                </li>
              )}
            </ul>
          </div>
        )}

        {/* Completion Message */}
        {isComplete && (
          <div
            className={cn(
              'border rounded-lg p-4',
              data.status === 'completed'
                ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              {data.status === 'completed' ? (
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
              ) : (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              <h4
                className={cn(
                  'font-medium',
                  data.status === 'completed'
                    ? 'text-green-800 dark:text-green-400'
                    : 'text-red-800 dark:text-red-400'
                )}
              >
                {data.status === 'completed'
                  ? `${jobType === 'backup' ? 'Backup' : 'Restore'} Completed`
                  : data.status === 'cancelled'
                    ? 'Operation Cancelled'
                    : 'Operation Failed'}
              </h4>
            </div>
            <div
              className={cn(
                'text-sm',
                data.status === 'completed'
                  ? 'text-green-600 dark:text-green-300'
                  : 'text-red-600 dark:text-red-300'
              )}
            >
              {data.status === 'completed' ? (
                <>
                  {jobType === 'backup'
                    ? 'Your backup has been created successfully.'
                    : 'Your data has been restored successfully.'}
                  {data.completed_at && (
                    <span className="block mt-1 text-xs">
                      Completed at{' '}
                      {new Date(data.completed_at).toLocaleString()}
                    </span>
                  )}
                </>
              ) : (
                'The operation did not complete successfully. Please check the errors above.'
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        {isComplete && (
          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Refresh Status
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
