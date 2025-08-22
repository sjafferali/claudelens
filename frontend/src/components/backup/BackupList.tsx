import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  Download,
  Trash2,
  RefreshCw,
  Archive,
  AlertCircle,
  CheckCircle,
  Clock,
  AlertTriangle,
  Database,
  HardDrive,
  RotateCcw,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import Loading from '@/components/common/Loading';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import Tooltip from '@/components/common/Tooltip';
import { backupApi, BackupMetadata, ListBackupsParams } from '@/api/backupApi';
import toast from 'react-hot-toast';

interface BackupListProps {
  className?: string;
  onCreateBackup?: () => void;
  onRestoreBackup?: (backupId: string) => void;
}

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'in_progress':
      return <Clock className="w-4 h-4 text-blue-500 animate-pulse" />;
    case 'failed':
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    case 'pending':
      return <Clock className="w-4 h-4 text-yellow-500" />;
    case 'corrupted':
      return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    default:
      return <Archive className="w-4 h-4 text-gray-500" />;
  }
};

const StatusBadge = ({ status }: { status: string }) => {
  const statusConfig = {
    completed:
      'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    in_progress:
      'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    pending:
      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    corrupted:
      'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
    deleting:
      'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
        statusConfig[status as keyof typeof statusConfig] ||
          statusConfig.pending
      )}
    >
      <StatusIcon status={status} />
      {status.replace('_', ' ').toUpperCase()}
    </span>
  );
};

const TypeBadge = ({ type }: { type: string }) => {
  const typeConfig = {
    full: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
    incremental:
      'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    selective:
      'bg-teal-100 text-teal-800 dark:bg-teal-900/20 dark:text-teal-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
        typeConfig[type as keyof typeof typeConfig] || typeConfig.full
      )}
    >
      {type.toUpperCase()}
    </span>
  );
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const BackupList: React.FC<BackupListProps> = ({
  className,
  onCreateBackup,
  onRestoreBackup,
}) => {
  const queryClient = useQueryClient();
  const [page, setPage] = React.useState(0);
  const [filters, setFilters] = React.useState<ListBackupsParams>({
    page: 0,
    size: 20,
    sort: 'created_at,desc',
  });
  const [deleteConfirm, setDeleteConfirm] = React.useState<{
    open: boolean;
    backup: BackupMetadata | null;
  }>({ open: false, backup: null });

  // Fetch backups
  const {
    data: backupsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['backups', filters],
    queryFn: () => backupApi.listBackups(filters),
    refetchInterval: ({ state }) => {
      // Auto-refresh if there are in-progress backups
      const hasInProgress = state.data?.items?.some((item: BackupMetadata) =>
        ['pending', 'in_progress'].includes(item.status)
      );
      return hasInProgress ? 5000 : false;
    },
  });

  // Delete backup mutation
  const deleteMutation = useMutation({
    mutationFn: (backupId: string) => backupApi.deleteBackup(backupId),
    onSuccess: (data) => {
      toast.success(data.message || 'Backup deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['backups'] });
      setDeleteConfirm({ open: false, backup: null });
    },
    onError: (error: unknown) => {
      const errorMessage =
        (error as Error & { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail || 'Failed to delete backup';
      toast.error(errorMessage);
    },
  });

  // Download backup mutation
  const downloadMutation = useMutation({
    mutationFn: (backupId: string) => backupApi.downloadBackup(backupId),
    onSuccess: () => {
      toast.success('Download started');
    },
    onError: (error: unknown) => {
      const errorMessage =
        (error as Error & { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail || 'Failed to download backup';
      toast.error(errorMessage);
    },
  });

  const handleDeleteBackup = (backup: BackupMetadata) => {
    setDeleteConfirm({ open: true, backup });
  };

  const handleConfirmDelete = () => {
    if (deleteConfirm.backup) {
      deleteMutation.mutate(deleteConfirm.backup._id);
    }
  };

  const handleDownload = (backup: BackupMetadata) => {
    if (backup.status !== 'completed') {
      toast.error('Backup is not ready for download');
      return;
    }
    downloadMutation.mutate(backup._id);
  };

  const handleRestore = (backup: BackupMetadata) => {
    if (backup.status !== 'completed') {
      toast.error('Backup is not ready for restore');
      return;
    }
    if (!backup.can_restore) {
      toast.error('This backup cannot be restored');
      return;
    }
    onRestoreBackup?.(backup._id);
  };

  const handleFilterChange = (newFilters: Partial<ListBackupsParams>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 0 }));
    setPage(0);
  };

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-600 dark:text-red-400">
              Failed to load backups. Please try again.
            </p>
            <Button
              onClick={() => refetch()}
              variant="outline"
              size="sm"
              className="mt-2"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with Create Backup button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Backup Library</h2>
          <p className="text-sm text-muted-foreground">
            Manage your data backups and restore points
          </p>
        </div>
        <Button onClick={onCreateBackup} className="gap-2">
          <Archive className="w-4 h-4" />
          Create Backup
        </Button>
      </div>

      {/* Summary Statistics */}
      {backupsData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-green-500" />
                <div>
                  <p className="text-sm font-medium">Completed</p>
                  <p className="text-xl font-bold text-green-600">
                    {backupsData.summary.completed_count}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-500" />
                <div>
                  <p className="text-sm font-medium">In Progress</p>
                  <p className="text-xl font-bold text-blue-600">
                    {backupsData.summary.in_progress_count}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-500" />
                <div>
                  <p className="text-sm font-medium">Failed</p>
                  <p className="text-xl font-bold text-red-600">
                    {backupsData.summary.failed_count}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-purple-500" />
                <div>
                  <p className="text-sm font-medium">Total Size</p>
                  <p className="text-xl font-bold text-purple-600">
                    {formatFileSize(backupsData.summary.total_size_bytes)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Status:</label>
              <select
                value={filters.status || ''}
                onChange={(e) =>
                  handleFilterChange({
                    status: e.target.value || undefined,
                  })
                }
                className="px-3 py-1 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800"
              >
                <option value="">All</option>
                <option value="completed">Completed</option>
                <option value="in_progress">In Progress</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Type:</label>
              <select
                value={filters.type || ''}
                onChange={(e) =>
                  handleFilterChange({
                    type: e.target.value || undefined,
                  })
                }
                className="px-3 py-1 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800"
              >
                <option value="">All</option>
                <option value="full">Full</option>
                <option value="incremental">Incremental</option>
                <option value="selective">Selective</option>
              </select>
            </div>
            <Button
              onClick={() => refetch()}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Backup Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Backups</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loading />
            </div>
          ) : !backupsData?.items?.length ? (
            <div className="text-center py-8">
              <Archive className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No backups found. Create your first backup to get started.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      Name
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      Type
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      Size
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      Created
                    </th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      Status
                    </th>
                    <th className="text-right py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {backupsData.items.map((backup) => (
                    <tr
                      key={backup._id}
                      className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50"
                    >
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {backup.name}
                          </p>
                          {backup.description && (
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {backup.description}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {backup.contents.total_documents} documents •{' '}
                            {backup.contents.sessions_count} sessions •{' '}
                            {backup.contents.messages_count} messages
                          </p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <TypeBadge type={backup.type} />
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="text-sm font-medium">
                            {formatFileSize(backup.size_bytes)}
                          </p>
                          {backup.compressed_size_bytes && (
                            <p className="text-xs text-gray-500">
                              Compressed:{' '}
                              {formatFileSize(backup.compressed_size_bytes)}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="text-sm">
                            {format(new Date(backup.created_at), 'MMM d, yyyy')}
                          </p>
                          <p className="text-xs text-gray-500">
                            {format(new Date(backup.created_at), 'h:mm a')}
                          </p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <StatusBadge status={backup.status} />
                        {backup.error_message && (
                          <Tooltip content={backup.error_message}>
                            <AlertCircle className="w-4 h-4 text-red-500 mt-1 cursor-help" />
                          </Tooltip>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2">
                          {backup.status === 'completed' && (
                            <>
                              <Tooltip content="Download backup">
                                <Button
                                  onClick={() => handleDownload(backup)}
                                  variant="outline"
                                  size="sm"
                                  disabled={downloadMutation.isPending}
                                >
                                  <Download className="w-4 h-4" />
                                </Button>
                              </Tooltip>
                              {backup.can_restore && (
                                <Tooltip content="Restore from backup">
                                  <Button
                                    onClick={() => handleRestore(backup)}
                                    variant="outline"
                                    size="sm"
                                  >
                                    <RotateCcw className="w-4 h-4" />
                                  </Button>
                                </Tooltip>
                              )}
                            </>
                          )}
                          <Tooltip content="Delete backup">
                            <Button
                              onClick={() => handleDeleteBackup(backup)}
                              variant="outline"
                              size="sm"
                              disabled={deleteMutation.isPending}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </Tooltip>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {backupsData?.pagination &&
            backupsData.pagination.total_pages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Showing{' '}
                  {backupsData.pagination.page * backupsData.pagination.size +
                    1}{' '}
                  to{' '}
                  {Math.min(
                    (backupsData.pagination.page + 1) *
                      backupsData.pagination.size,
                    backupsData.pagination.total_elements
                  )}{' '}
                  of {backupsData.pagination.total_elements} backups
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => {
                      const newPage = page - 1;
                      setPage(newPage);
                      handleFilterChange({ page: newPage });
                    }}
                    disabled={page === 0}
                    variant="outline"
                    size="sm"
                  >
                    Previous
                  </Button>
                  <span className="text-sm px-2">
                    Page {page + 1} of {backupsData.pagination.total_pages}
                  </span>
                  <Button
                    onClick={() => {
                      const newPage = page + 1;
                      setPage(newPage);
                      handleFilterChange({ page: newPage });
                    }}
                    disabled={page >= backupsData.pagination.total_pages - 1}
                    variant="outline"
                    size="sm"
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.open}
        onCancel={() => setDeleteConfirm({ open: false, backup: null })}
        title="Delete Backup"
        message={
          deleteConfirm.backup
            ? `Are you sure you want to delete the backup "${deleteConfirm.backup.name}"? This action cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        onConfirm={handleConfirmDelete}
        variant="destructive"
      />
    </div>
  );
};
