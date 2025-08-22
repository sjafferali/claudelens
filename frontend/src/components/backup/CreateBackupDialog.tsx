import * as React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Calendar, Filter, Archive, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useProjects } from '@/hooks/useProjects';
import { backupApi, CreateBackupRequest, BackupFilters } from '@/api/backupApi';
import toast from 'react-hot-toast';

interface CreateBackupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (jobId: string) => void;
}

export const CreateBackupDialog: React.FC<CreateBackupDialogProps> = ({
  open,
  onOpenChange,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const { data: projectsData } = useProjects({ limit: 100 });

  // Form state
  const [formData, setFormData] = React.useState<CreateBackupRequest>({
    name: '',
    description: '',
    type: 'full',
    filters: undefined,
    options: {
      compress: true,
      compression_level: 3,
      encrypt: false,
      include_metadata: true,
      include_analytics: false,
    },
  });

  const [selectiveFilters, setSelectiveFilters] = React.useState<BackupFilters>(
    {
      projects: [],
      sessions: [],
      date_range: undefined,
      include_patterns: [],
      exclude_patterns: [],
      min_message_count: undefined,
      max_message_count: undefined,
    }
  );

  const [dateRange, setDateRange] = React.useState({
    start: '',
    end: '',
  });

  const [errors, setErrors] = React.useState<Record<string, string>>({});

  // Get projects from API
  const projects = React.useMemo(() => {
    if (!projectsData?.items) return [];
    return projectsData.items.map((project) => ({
      id: project._id,
      name: project.name,
    }));
  }, [projectsData]);

  // Create backup mutation
  const createMutation = useMutation({
    mutationFn: (request: CreateBackupRequest) =>
      backupApi.createBackup(request),
    onSuccess: (response) => {
      toast.success(response.message || 'Backup creation started');
      queryClient.invalidateQueries({ queryKey: ['backups'] });
      onSuccess?.(response.job_id);
      handleClose();
    },
    onError: (error: unknown) => {
      const errorMessage =
        (error as Error & { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail || 'Failed to create backup';
      toast.error(errorMessage);
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Backup name is required';
    } else if (formData.name.length < 3) {
      newErrors.name = 'Name must be at least 3 characters';
    } else if (formData.name.length > 100) {
      newErrors.name = 'Name must be less than 100 characters';
    } else if (!/^[a-zA-Z0-9\s\-_]+$/.test(formData.name)) {
      newErrors.name =
        'Name can only contain letters, numbers, spaces, dashes, and underscores';
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    if (formData.type === 'selective') {
      const hasFilters =
        selectiveFilters.projects?.length ||
        selectiveFilters.sessions?.length ||
        (dateRange.start && dateRange.end) ||
        selectiveFilters.include_patterns?.length ||
        selectiveFilters.exclude_patterns?.length ||
        selectiveFilters.min_message_count ||
        selectiveFilters.max_message_count;

      if (!hasFilters) {
        newErrors.filters =
          'At least one filter is required for selective backup';
      }

      if (
        dateRange.start &&
        dateRange.end &&
        new Date(dateRange.start) >= new Date(dateRange.end)
      ) {
        newErrors.dateRange = 'Start date must be before end date';
      }

      if (
        selectiveFilters.min_message_count &&
        selectiveFilters.max_message_count &&
        selectiveFilters.min_message_count >= selectiveFilters.max_message_count
      ) {
        newErrors.messageCount =
          'Minimum message count must be less than maximum';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) return;

    // Build the final request
    const request: CreateBackupRequest = {
      ...formData,
      filters: undefined,
    };

    // Add filters for selective backup
    if (formData.type === 'selective') {
      const filters: BackupFilters = { ...selectiveFilters };

      if (dateRange.start && dateRange.end) {
        filters.date_range = {
          start: dateRange.start,
          end: dateRange.end,
        };
      }

      // Only include non-empty arrays and defined values
      if (filters.projects?.length === 0) delete filters.projects;
      if (filters.sessions?.length === 0) delete filters.sessions;
      if (filters.include_patterns?.length === 0)
        delete filters.include_patterns;
      if (filters.exclude_patterns?.length === 0)
        delete filters.exclude_patterns;
      if (!filters.min_message_count) delete filters.min_message_count;
      if (!filters.max_message_count) delete filters.max_message_count;

      request.filters = filters;
    }

    createMutation.mutate(request);
  };

  const handleClose = () => {
    if (createMutation.isPending) return;

    // Reset form
    setFormData({
      name: '',
      description: '',
      type: 'full',
      filters: undefined,
      options: {
        compress: true,
        compression_level: 3,
        encrypt: false,
        include_metadata: true,
        include_analytics: false,
      },
    });
    setSelectiveFilters({
      projects: [],
      sessions: [],
      date_range: undefined,
      include_patterns: [],
      exclude_patterns: [],
      min_message_count: undefined,
      max_message_count: undefined,
    });
    setDateRange({ start: '', end: '' });
    setErrors({});
    onOpenChange(false);
  };

  const handleTypeChange = (type: 'full' | 'selective') => {
    setFormData((prev) => ({ ...prev, type }));
    // Clear filters when switching away from selective
    if (type !== 'selective') {
      setSelectiveFilters({
        projects: [],
        sessions: [],
        date_range: undefined,
        include_patterns: [],
        exclude_patterns: [],
        min_message_count: undefined,
        max_message_count: undefined,
      });
      setDateRange({ start: '', end: '' });
    }
    setErrors({});
  };

  const generateDefaultName = () => {
    const now = new Date();
    const timestamp = format(now, 'yyyy-MM-dd-HHmm');
    const typePrefix =
      formData.type.charAt(0).toUpperCase() + formData.type.slice(1);
    return `${typePrefix} Backup ${timestamp}`;
  };

  const handleGenerateName = () => {
    setFormData((prev) => ({ ...prev, name: generateDefaultName() }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Archive className="w-5 h-5" />
            Create Backup
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Basic Information</h3>

            {/* Backup Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Backup Name *
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="Enter backup name"
                  className={cn(
                    'flex-1 px-3 py-2 border rounded-md text-sm dark:bg-gray-800 dark:text-gray-200',
                    errors.name
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
                  )}
                />
                <Button
                  type="button"
                  onClick={handleGenerateName}
                  variant="outline"
                  size="sm"
                >
                  Generate
                </Button>
              </div>
              {errors.name && (
                <p className="text-sm text-red-600 mt-1">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder="Optional description for this backup"
                rows={3}
                className={cn(
                  'w-full px-3 py-2 border rounded-md text-sm dark:bg-gray-800 dark:text-gray-200',
                  errors.description
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
                )}
              />
              {errors.description && (
                <p className="text-sm text-red-600 mt-1">
                  {errors.description}
                </p>
              )}
            </div>
          </div>

          {/* Backup Type */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Backup Type</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                {
                  type: 'full' as const,
                  title: 'Full Backup',
                  description: 'Complete backup of all data',
                },
                {
                  type: 'selective' as const,
                  title: 'Selective',
                  description: 'Custom filters and date ranges',
                },
              ].map(({ type, title, description }) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => handleTypeChange(type)}
                  className={cn(
                    'p-4 text-left border-2 rounded-lg transition-all',
                    formData.type === type
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  )}
                >
                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                    {title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Selective Backup Filters */}
          {formData.type === 'selective' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Filter className="w-4 h-4" />
                Filters
              </h3>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Calendar className="w-4 h-4 inline mr-2" />
                  Date Range
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) =>
                        setDateRange((prev) => ({
                          ...prev,
                          start: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                      placeholder="Start date"
                    />
                  </div>
                  <div>
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) =>
                        setDateRange((prev) => ({
                          ...prev,
                          end: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                      placeholder="End date"
                    />
                  </div>
                </div>
                {errors.dateRange && (
                  <p className="text-sm text-red-600 mt-1">
                    {errors.dateRange}
                  </p>
                )}
              </div>

              {/* Project Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Projects
                </label>
                <select
                  multiple
                  value={selectiveFilters.projects || []}
                  onChange={(e) => {
                    const values = Array.from(
                      e.target.selectedOptions,
                      (option) => option.value
                    );
                    setSelectiveFilters((prev) => ({
                      ...prev,
                      projects: values,
                    }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                  size={Math.min(5, Math.max(3, projects.length))}
                >
                  {projects.length === 0 ? (
                    <option disabled>No projects available</option>
                  ) : (
                    projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))
                  )}
                </select>
                {projects.length > 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    Hold Ctrl/Cmd to select multiple projects
                  </p>
                )}
              </div>

              {/* Message Count Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Message Count Range
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <input
                      type="number"
                      value={selectiveFilters.min_message_count || ''}
                      onChange={(e) =>
                        setSelectiveFilters((prev) => ({
                          ...prev,
                          min_message_count: e.target.value
                            ? parseInt(e.target.value)
                            : undefined,
                        }))
                      }
                      placeholder="Min messages"
                      min="1"
                      max="10000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                    />
                  </div>
                  <div>
                    <input
                      type="number"
                      value={selectiveFilters.max_message_count || ''}
                      onChange={(e) =>
                        setSelectiveFilters((prev) => ({
                          ...prev,
                          max_message_count: e.target.value
                            ? parseInt(e.target.value)
                            : undefined,
                        }))
                      }
                      placeholder="Max messages"
                      min="1"
                      max="10000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                    />
                  </div>
                </div>
                {errors.messageCount && (
                  <p className="text-sm text-red-600 mt-1">
                    {errors.messageCount}
                  </p>
                )}
              </div>

              {errors.filters && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800">
                  <AlertCircle className="w-4 h-4 text-red-500" />
                  <p className="text-sm text-red-600 dark:text-red-400">
                    {errors.filters}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Options */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Options</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Compression */}
              <div className="space-y-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.options?.compress || false}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        options: {
                          ...prev.options,
                          compress: e.target.checked,
                        },
                      }))
                    }
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Enable compression
                  </span>
                </label>
                {formData.options?.compress && (
                  <div className="ml-6">
                    <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Compression Level (1-9)
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="9"
                      value={formData.options?.compression_level || 3}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          options: {
                            ...prev.options,
                            compression_level: parseInt(e.target.value),
                          },
                        }))
                      }
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Fast</span>
                      <span>
                        Level {formData.options?.compression_level || 3}
                      </span>
                      <span>Best</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Other Options */}
              <div className="space-y-3">
                {[
                  { key: 'include_metadata', label: 'Include metadata' },
                  { key: 'include_analytics', label: 'Include analytics data' },
                  { key: 'encrypt', label: 'Encrypt backup' },
                ].map(({ key, label }) => (
                  <label key={key} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={Boolean(
                        formData.options?.[key as keyof typeof formData.options]
                      )}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          options: { ...prev.options, [key]: e.target.checked },
                        }))
                      }
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              onClick={handleClose}
              variant="outline"
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createMutation.isPending}
              className="gap-2"
            >
              {createMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating Backup...
                </>
              ) : (
                <>
                  <Archive className="w-4 h-4" />
                  Create Backup
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
