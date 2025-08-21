import * as React from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import {
  useExportsList,
  useDownloadExport,
  useCancelExport,
  useDeleteExport,
} from '@/hooks/useExport';
import {
  Download,
  X,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
  Calendar,
  HardDrive,
  Trash2,
} from 'lucide-react';

interface ExportHistoryProps {
  className?: string;
}

export const ExportHistory: React.FC<ExportHistoryProps> = ({ className }) => {
  const [currentPage, setCurrentPage] = React.useState(0);
  const [statusFilter, setStatusFilter] = React.useState<string>('');
  const [deleteConfirmation, setDeleteConfirmation] = React.useState<{
    isOpen: boolean;
    jobId: string | null;
  }>({ isOpen: false, jobId: null });

  const { data: exportsData, isLoading } = useExportsList({
    page: currentPage,
    size: 10,
    status: statusFilter || undefined,
    sort: 'createdAt,desc',
  });

  const downloadExport = useDownloadExport();
  const cancelExport = useCancelExport();
  const deleteExport = useDeleteExport();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'cancelled':
        return <X className="w-4 h-4 text-gray-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses =
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';

    switch (status) {
      case 'queued':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300`;
      case 'processing':
        return `${baseClasses} bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300`;
      case 'cancelled':
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300`;
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const handleDownload = async (jobId: string) => {
    try {
      await downloadExport.mutateAsync(jobId);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleCancel = async (jobId: string) => {
    try {
      await cancelExport.mutateAsync(jobId);
    } catch (error) {
      console.error('Cancel failed:', error);
    }
  };

  const handleDelete = async (jobId: string) => {
    try {
      await deleteExport.mutateAsync(jobId);
      setDeleteConfirmation({ isOpen: false, jobId: null });
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const canCancel = (status: string) =>
    ['queued', 'processing'].includes(status);
  const canDownload = (status: string) => status === 'completed';

  if (isLoading) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('p-6', className)}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Export History
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              View and manage your export jobs
            </p>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Status:
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(0);
              }}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
            >
              <option value="">All</option>
              <option value="queued">Queued</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Export Jobs Table */}
        {exportsData && exportsData.content.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="text-left pb-3 font-medium text-gray-700 dark:text-gray-300">
                    Status
                  </th>
                  <th className="text-left pb-3 font-medium text-gray-700 dark:text-gray-300">
                    Format
                  </th>
                  <th className="text-left pb-3 font-medium text-gray-700 dark:text-gray-300">
                    Created
                  </th>
                  <th className="text-left pb-3 font-medium text-gray-700 dark:text-gray-300">
                    Size / Items
                  </th>
                  <th className="text-left pb-3 font-medium text-gray-700 dark:text-gray-300">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {exportsData.content.map((job) => (
                  <tr
                    key={job.jobId}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    <td className="py-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(job.status)}
                        <span className={getStatusBadge(job.status)}>
                          {job.status.charAt(0).toUpperCase() +
                            job.status.slice(1)}
                        </span>
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300">
                        {job.format.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 text-gray-600 dark:text-gray-400">
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3" />
                        <span className="text-xs">
                          {formatDate(job.createdAt)}
                        </span>
                      </div>
                      {job.completedAt && (
                        <div className="text-xs text-gray-500 mt-1">
                          Completed: {formatDate(job.completedAt)}
                        </div>
                      )}
                    </td>
                    <td className="py-4 text-gray-600 dark:text-gray-400">
                      {job.fileInfo && (
                        <div className="space-y-1">
                          <div className="flex items-center space-x-1">
                            <HardDrive className="w-3 h-3" />
                            <span className="text-xs">
                              {formatFileSize(job.fileInfo.sizeBytes || 0)}
                            </span>
                          </div>
                          {job.fileInfo.conversationsCount && (
                            <div className="text-xs text-gray-500">
                              {job.fileInfo.conversationsCount} conversations
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-4">
                      <div className="flex items-center space-x-2">
                        {canDownload(job.status) && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDownload(job.jobId)}
                            disabled={downloadExport.isPending}
                            className="text-green-600 border-green-300 hover:bg-green-50 dark:text-green-400 dark:border-green-600 dark:hover:bg-green-900/20"
                          >
                            {downloadExport.isPending ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Download className="w-3 h-3" />
                            )}
                          </Button>
                        )}
                        {canCancel(job.status) && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCancel(job.jobId)}
                            disabled={cancelExport.isPending}
                            className="text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-600 dark:hover:bg-red-900/20"
                          >
                            {cancelExport.isPending ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <X className="w-3 h-3" />
                            )}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            setDeleteConfirmation({
                              isOpen: true,
                              jobId: job.jobId,
                            })
                          }
                          disabled={deleteExport.isPending}
                          className="text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-600 dark:hover:bg-red-900/20"
                          title="Delete export"
                        >
                          {deleteExport.isPending &&
                          deleteConfirmation.jobId === job.jobId ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Trash2 className="w-3 h-3" />
                          )}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              No export jobs found
            </h4>
            <p className="text-gray-600 dark:text-gray-400">
              {statusFilter
                ? `No exports with status "${statusFilter}"`
                : 'Create your first export to see it here'}
            </p>
          </div>
        )}

        {/* Pagination */}
        {exportsData && exportsData.totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Showing {currentPage * 10 + 1} to{' '}
              {Math.min((currentPage + 1) * 10, exportsData.totalElements)} of{' '}
              {exportsData.totalElements} exports
            </div>
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setCurrentPage((prev) => Math.max(0, prev - 1))}
                disabled={currentPage === 0}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Page {currentPage + 1} of {exportsData.totalPages}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                  setCurrentPage((prev) =>
                    Math.min(exportsData.totalPages - 1, prev + 1)
                  )
                }
                disabled={currentPage >= exportsData.totalPages - 1}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirmation.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() =>
              setDeleteConfirmation({ isOpen: false, jobId: null })
            }
          />
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Delete Export
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to permanently delete this export? This
              action cannot be undone.
            </p>
            <div className="flex items-center justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() =>
                  setDeleteConfirmation({ isOpen: false, jobId: null })
                }
                disabled={deleteExport.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                onClick={() =>
                  deleteConfirmation.jobId &&
                  handleDelete(deleteConfirmation.jobId)
                }
                disabled={deleteExport.isPending}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                {deleteExport.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
