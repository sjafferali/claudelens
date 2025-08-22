import * as React from 'react';
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { backupApi } from '@/api/backupApi';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Database,
  Calendar,
  Info,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface RestoreHistoryProps {
  onRefresh?: () => void;
}

export const RestoreHistory: React.FC<RestoreHistoryProps> = ({
  onRefresh,
}) => {
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['restore-history', page],
    queryFn: () =>
      backupApi.listRestoreJobs({
        page,
        size: 10,
        sort: 'created_at,desc',
      }),
    refetchInterval: autoRefresh ? 5000 : false, // Auto-refresh every 5 seconds
  });

  // Auto-disable refresh when all jobs are completed
  useEffect(() => {
    if (data?.items) {
      const hasActiveJobs = data.items.some(
        (job) => job.status === 'processing' || job.status === 'queued'
      );
      if (!hasActiveJobs && autoRefresh) {
        setAutoRefresh(false);
      }
    }
  }, [data, autoRefresh]);

  const toggleExpand = (jobId: string) => {
    setExpandedJobs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'queued':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
      case 'failed':
        return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20';
      case 'processing':
        return 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20';
      case 'queued':
        return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20';
      default:
        return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20';
    }
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = endTime - startTime;

    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const handleRefresh = () => {
    refetch();
    onRefresh?.();
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <Loading />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-red-500">
            Failed to load restore history
          </div>
        </CardContent>
      </Card>
    );
  }

  const restoreJobs = data?.items || [];
  const pagination = data?.pagination;

  if (restoreJobs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Restore History
            </span>
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <Database className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No restore operations yet</p>
            <p className="text-sm mt-1">
              Your restore history will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Restore History
          </span>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm font-normal">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              Auto-refresh
            </label>
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {restoreJobs.map((job) => {
          const isExpanded = expandedJobs.has(job.job_id);
          const isActive =
            job.status === 'processing' || job.status === 'queued';

          return (
            <div
              key={job.job_id}
              className={cn(
                'border rounded-lg transition-all',
                isActive && 'border-blue-300 dark:border-blue-700'
              )}
            >
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                onClick={() => toggleExpand(job.job_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <div className="font-medium">{job.backup_name}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                        <Calendar className="w-3 h-3" />
                        {new Date(job.created_at).toLocaleString()}
                        {job.started_at && (
                          <span className="ml-2">
                            Duration:{' '}
                            {formatDuration(job.started_at, job.completed_at)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        'px-2 py-1 rounded-full text-xs font-medium',
                        getStatusColor(job.status)
                      )}
                    >
                      {job.status.toUpperCase()}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Progress bar for active jobs */}
                {isActive && job.progress && (
                  <div className="mt-3">
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                      <span>
                        {job.progress.processed} / {job.progress.total} items
                      </span>
                      <span>{job.progress.percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${job.progress.percentage}%` }}
                      />
                    </div>
                    {job.progress.current_item && (
                      <div className="text-xs text-gray-500 mt-1">
                        Processing: {job.progress.current_item}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="border-t px-4 py-3 bg-gray-50 dark:bg-gray-800/50">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">
                        Mode:
                      </span>{' '}
                      <span className="font-medium capitalize">{job.mode}</span>
                    </div>
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">
                        Conflict Resolution:
                      </span>{' '}
                      <span className="font-medium capitalize">
                        {job.conflict_resolution || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Statistics */}
                  {job.statistics && Object.keys(job.statistics).length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <h4 className="font-medium mb-2 flex items-center gap-1">
                        <Info className="w-4 h-4" />
                        Statistics
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {Object.entries(job.statistics).map(([key, value]) => (
                          <div
                            key={key}
                            className="bg-white dark:bg-gray-700 p-2 rounded"
                          >
                            <div className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                              {key.replace(/_/g, ' ')}
                            </div>
                            <div className="font-medium">{value}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Errors */}
                  {job.errors && job.errors.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <h4 className="font-medium mb-2 text-red-600 dark:text-red-400 flex items-center gap-1">
                        <AlertCircle className="w-4 h-4" />
                        Errors ({job.errors.length})
                      </h4>
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {job.errors.map((error, idx) => (
                          <div
                            key={idx}
                            className="text-sm bg-red-50 dark:bg-red-900/20 p-2 rounded"
                          >
                            <div className="font-medium text-red-700 dark:text-red-300">
                              {error.error}
                            </div>
                            {error.details && (
                              <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                                {error.details}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex justify-center gap-2 pt-4">
            <Button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              variant="outline"
              size="sm"
            >
              Previous
            </Button>
            <span className="flex items-center px-3 text-sm">
              Page {page + 1} of {pagination.total_pages}
            </span>
            <Button
              onClick={() =>
                setPage((p) => Math.min(pagination.total_pages - 1, p + 1))
              }
              disabled={page >= pagination.total_pages - 1}
              variant="outline"
              size="sm"
            >
              Next
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
