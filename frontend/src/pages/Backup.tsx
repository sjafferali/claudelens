import * as React from 'react';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { cn } from '@/utils/cn';
import {
  Archive,
  RotateCcw,
  Settings,
  Upload,
  FileUp,
  Eye,
} from 'lucide-react';
import { BackupList } from '@/components/backup/BackupList';
import { CreateBackupDialog } from '@/components/backup/CreateBackupDialog';
import { Button } from '@/components/common/Button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import Loading from '@/components/common/Loading';
import { backupApi, CreateRestoreRequest } from '@/api/backupApi';
import toast from 'react-hot-toast';

interface Tab {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  {
    id: 'backups',
    label: 'Backups',
    icon: <Archive className="w-4 h-4" />,
  },
  {
    id: 'restore',
    label: 'Restore',
    icon: <RotateCcw className="w-4 h-4" />,
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <Settings className="w-4 h-4" />,
  },
];

interface RestoreFromFileProps {
  onRestoreStarted?: (jobId: string) => void;
}

const RestoreFromFile: React.FC<RestoreFromFileProps> = ({
  onRestoreStarted,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [restoreOptions, setRestoreOptions] = useState({
    mode: 'full' as 'full' | 'selective' | 'merge',
    conflict_resolution: 'skip' as 'skip' | 'overwrite' | 'rename' | 'merge',
  });

  const uploadMutation = useMutation({
    mutationFn: (data: { file: File; options: typeof restoreOptions }) =>
      backupApi.uploadAndRestore(data.file, data.options),
    onSuccess: (response) => {
      toast.success(response.message || 'Restore started successfully');
      onRestoreStarted?.(response.job_id);
      setFile(null);
    },
    onError: (error: unknown) => {
      const errorMessage =
        (error as Error & { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail || 'Failed to start restore';
      toast.error(errorMessage);
    },
  });

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const selectedFile = files[0];
      if (selectedFile.name.endsWith('.claudelens')) {
        setFile(selectedFile);
      } else {
        toast.error('Please select a .claudelens backup file');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      setFile(files[0]);
    }
  };

  const handleRestore = () => {
    if (!file) return;
    uploadMutation.mutate({ file, options: restoreOptions });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Restore from File
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* File Upload Area */}
        <div
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
            dragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {file ? (
            <div className="space-y-2">
              <FileUp className="w-8 h-8 text-green-500 mx-auto" />
              <p className="font-medium text-green-700 dark:text-green-400">
                {file.name}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
              <Button onClick={() => setFile(null)} variant="outline" size="sm">
                Remove
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Drop your backup file here
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Or click to browse for a .claudelens file
                </p>
              </div>
              <label>
                <input
                  type="file"
                  accept=".claudelens"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Button variant="outline" className="cursor-pointer">
                  Browse Files
                </Button>
              </label>
            </div>
          )}
        </div>

        {/* Restore Options */}
        {file && (
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900 dark:text-gray-100">
              Restore Options
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Restore Mode
                </label>
                <select
                  value={restoreOptions.mode}
                  onChange={(e) =>
                    setRestoreOptions((prev) => ({
                      ...prev,
                      mode: e.target.value as typeof prev.mode,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                >
                  <option value="full">Full Restore</option>
                  <option value="selective">Selective Restore</option>
                  <option value="merge">Merge with Existing</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Conflict Resolution
                </label>
                <select
                  value={restoreOptions.conflict_resolution}
                  onChange={(e) =>
                    setRestoreOptions((prev) => ({
                      ...prev,
                      conflict_resolution: e.target
                        .value as typeof prev.conflict_resolution,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                >
                  <option value="skip">Skip Conflicts</option>
                  <option value="overwrite">Overwrite Existing</option>
                  <option value="rename">Rename New Items</option>
                  <option value="merge">Merge Content</option>
                </select>
              </div>
            </div>

            <Button
              onClick={handleRestore}
              disabled={uploadMutation.isPending}
              className="w-full gap-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Starting Restore...
                </>
              ) : (
                <>
                  <RotateCcw className="w-4 h-4" />
                  Start Restore
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface BackupPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  backupId: string | null;
  onRestore?: (backupId: string) => void;
}

const BackupPreviewModal: React.FC<BackupPreviewModalProps> = ({
  open,
  onOpenChange,
  backupId,
  onRestore,
}) => {
  const { data: preview, isLoading } = useQuery({
    queryKey: ['backup-preview', backupId],
    queryFn: () => (backupId ? backupApi.previewBackup(backupId) : null),
    enabled: open && !!backupId,
  });

  const [restoreOptions, setRestoreOptions] = useState<CreateRestoreRequest>({
    backup_id: backupId || '',
    mode: 'full',
    conflict_resolution: 'skip',
  });

  const restoreMutation = useMutation({
    mutationFn: (request: CreateRestoreRequest) =>
      backupApi.createRestore(request),
    onSuccess: (response) => {
      toast.success(response.message || 'Restore started successfully');
      onRestore?.(backupId!);
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
    if (!backupId) return;
    restoreMutation.mutate({ ...restoreOptions, backup_id: backupId });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Backup Preview
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loading />
          </div>
        ) : preview ? (
          <div className="space-y-6">
            {/* Backup Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardContent className="p-4">
                  <h4 className="font-medium mb-2">Backup Information</h4>
                  <div className="space-y-1 text-sm">
                    <p>
                      <span className="font-medium">Name:</span> {preview.name}
                    </p>
                    <p>
                      <span className="font-medium">Type:</span> {preview.type}
                    </p>
                    <p>
                      <span className="font-medium">Size:</span>{' '}
                      {(preview.size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </p>
                    <p>
                      <span className="font-medium">Created:</span>{' '}
                      {new Date(preview.created_at).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <h4 className="font-medium mb-2">Contents</h4>
                  <div className="space-y-1 text-sm">
                    <p>
                      <span className="font-medium">Projects:</span>{' '}
                      {preview.contents.projects_count}
                    </p>
                    <p>
                      <span className="font-medium">Sessions:</span>{' '}
                      {preview.contents.sessions_count}
                    </p>
                    <p>
                      <span className="font-medium">Messages:</span>{' '}
                      {preview.contents.messages_count}
                    </p>
                    <p>
                      <span className="font-medium">Prompts:</span>{' '}
                      {preview.contents.prompts_count}
                    </p>
                    <p>
                      <span className="font-medium">Total:</span>{' '}
                      {preview.contents.total_documents} documents
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Warnings */}
            {preview.warnings.length > 0 && (
              <Card>
                <CardContent className="p-4">
                  <h4 className="font-medium mb-2 text-yellow-600">Warnings</h4>
                  <ul className="space-y-1 text-sm">
                    {preview.warnings.map((warning, index) => (
                      <li key={index} className="text-yellow-600">
                        • {warning}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Restore Options */}
            <Card>
              <CardContent className="p-4">
                <h4 className="font-medium mb-4">Restore Options</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Restore Mode
                    </label>
                    <select
                      value={restoreOptions.mode}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          mode: e.target.value as typeof prev.mode,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800"
                    >
                      <option value="full">Full Restore</option>
                      <option value="selective">Selective Restore</option>
                      <option value="merge">Merge with Existing</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Conflict Resolution
                    </label>
                    <select
                      value={restoreOptions.conflict_resolution}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          conflict_resolution: e.target
                            .value as typeof prev.conflict_resolution,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800"
                    >
                      <option value="skip">Skip Conflicts</option>
                      <option value="overwrite">Overwrite Existing</option>
                      <option value="rename">Rename New Items</option>
                      <option value="merge">Merge Content</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3">
              <Button
                onClick={() => onOpenChange(false)}
                variant="outline"
                disabled={restoreMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={handleRestore}
                disabled={restoreMutation.isPending || !preview.can_restore}
                className="gap-2"
              >
                {restoreMutation.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Starting Restore...
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-4 h-4" />
                    Start Restore
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
};

export function BackupPage() {
  const [activeTab, setActiveTab] = useState<string>('backups');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedBackupId, setSelectedBackupId] = useState<string | null>(null);

  const handleCreateBackup = () => {
    setShowCreateDialog(true);
  };

  const handleBackupCreated = (jobId: string) => {
    // Could show a progress dialog or notification here
    console.log('Backup job created:', jobId);
  };

  const handleRestoreBackup = (backupId: string) => {
    setSelectedBackupId(backupId);
    setShowPreviewModal(true);
  };

  const handleRestoreStarted = (jobId: string) => {
    // Could show a progress dialog or notification here
    console.log('Restore job started:', jobId);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Backup & Restore</h1>
        <p className="text-muted-foreground">
          Create backups of your data and restore from previous backup points.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b mb-6">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'backups' && (
          <div className="space-y-6">
            <BackupList
              onCreateBackup={handleCreateBackup}
              onRestoreBackup={handleRestoreBackup}
            />
          </div>
        )}

        {activeTab === 'restore' && (
          <div className="space-y-6">
            <RestoreFromFile onRestoreStarted={handleRestoreStarted} />
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Backup Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Backup Settings
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Backup scheduling and configuration options will be
                    available in Phase 2.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Create Backup Dialog */}
      <CreateBackupDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={handleBackupCreated}
      />

      {/* Backup Preview Modal */}
      <BackupPreviewModal
        open={showPreviewModal}
        onOpenChange={setShowPreviewModal}
        backupId={selectedBackupId}
        onRestore={handleRestoreStarted}
      />
    </div>
  );
}

// Default export for lazy loading
export default BackupPage;
