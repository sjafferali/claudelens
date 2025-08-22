import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  FileText,
  Package,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '@/api/client';

interface ImportJobStatistics {
  imported: number;
  skipped: number;
  failed: number;
  merged: number;
  replaced: number;
}

interface ImportJob {
  jobId: string;
  status:
    | 'processing'
    | 'completed'
    | 'failed'
    | 'cancelled'
    | 'partial'
    | 'rolled_back';
  fileId?: string;
  createdAt: string;
  completedAt?: string;
  statistics: ImportJobStatistics;
  errors?: Array<{ message: string }>;
}

interface ImportJobsResponse {
  content: ImportJob[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
}

async function fetchImportJobs(page: number): Promise<ImportJobsResponse> {
  return apiClient.get('/import', {
    params: {
      page,
      size: 10,
      sort: 'createdAt,desc',
    },
  });
}

export const ImportHistory: React.FC = () => {
  const [page, setPage] = React.useState(0);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['importJobs', page],
    queryFn: () => fetchImportJobs(page),
    staleTime: 30000, // 30 seconds
  });

  const getStatusIcon = (status: ImportJob['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      case 'partial':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'rolled_back':
        return <RefreshCw className="w-5 h-5 text-orange-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: ImportJob['status']) => {
    const statusMap: Record<ImportJob['status'], string> = {
      processing: 'Processing',
      completed: 'Completed',
      failed: 'Failed',
      cancelled: 'Cancelled',
      partial: 'Partially Complete',
      rolled_back: 'Rolled Back',
    };
    return statusMap[status] || 'Unknown';
  };

  const getStatusColor = (status: ImportJob['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
      case 'failed':
        return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20';
      case 'processing':
        return 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20';
      case 'cancelled':
        return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20';
      case 'partial':
        return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20';
      case 'rolled_back':
        return 'text-orange-600 bg-orange-50 dark:text-orange-400 dark:bg-orange-900/20';
      default:
        return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900/20';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-700 dark:text-gray-300">
          Failed to load import history
        </p>
        <Button onClick={() => refetch()} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  if (!data || data.content.length === 0) {
    return (
      <div className="text-center py-12">
        <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
          No Import History
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Your import history will appear here once you start importing data.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Import Jobs List */}
      <div className="overflow-hidden border border-gray-200 dark:border-gray-700 rounded-lg">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                File ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Statistics
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Duration
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {data.content.map((job) => (
              <tr
                key={job.jobId}
                className="hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(job.status)}
                    <span
                      className={cn(
                        'px-2 py-1 text-xs font-medium rounded',
                        getStatusColor(job.status)
                      )}
                    >
                      {getStatusText(job.status)}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-900 dark:text-gray-100 font-mono">
                      {job.fileId ? job.fileId.substring(0, 8) + '...' : 'N/A'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    <div className="flex flex-wrap gap-2">
                      {job.statistics.imported > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300">
                          {job.statistics.imported} imported
                        </span>
                      )}
                      {job.statistics.skipped > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300">
                          {job.statistics.skipped} skipped
                        </span>
                      )}
                      {job.statistics.failed > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300">
                          {job.statistics.failed} failed
                        </span>
                      )}
                      {job.statistics.merged > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                          {job.statistics.merged} merged
                        </span>
                      )}
                      {job.statistics.replaced > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300">
                          {job.statistics.replaced} replaced
                        </span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                  {format(new Date(job.createdAt), 'MMM d, yyyy HH:mm')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                  {job.completedAt
                    ? `${Math.round(
                        (new Date(job.completedAt).getTime() -
                          new Date(job.createdAt).getTime()) /
                          1000
                      )}s`
                    : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Showing {data.number * data.size + 1} to{' '}
            {Math.min((data.number + 1) * data.size, data.totalElements)} of{' '}
            {data.totalElements} results
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page >= data.totalPages - 1}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
