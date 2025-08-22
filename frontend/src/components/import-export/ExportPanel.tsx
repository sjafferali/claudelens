import * as React from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { useCreateExport } from '@/hooks/useExport';
import { useProjects } from '@/hooks/useProjects';
import { CreateExportRequest } from '@/api/import-export';
import { Calendar, Filter, Download } from 'lucide-react';

interface ExportPanelProps {
  className?: string;
  onExportStarted?: (jobId: string) => void;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({
  className,
  onExportStarted,
}) => {
  const createExport = useCreateExport();
  const { data: projectsData } = useProjects({ limit: 100 });

  // Form state
  const [format, setFormat] = React.useState<
    'json' | 'csv' | 'markdown' | 'pdf'
  >('json');
  const [dateRange, setDateRange] = React.useState({
    start: '',
    end: '',
  });
  const [selectedProjects, setSelectedProjects] = React.useState<string[]>([]);
  const [costRange, setCostRange] = React.useState({ min: 0, max: 1000 });
  const [useCostFilter, setUseCostFilter] = React.useState(false);
  const [options, setOptions] = React.useState({
    includeMessages: true,
    includeMetadata: true,
    includeToolCalls: true,
    compress: false,
  });

  const [compressionOptions, setCompressionOptions] = React.useState({
    enabled: false,
    format: 'tar.gz' as 'none' | 'zstd' | 'tar.gz',
    level: 3,
  });

  // Get projects from API
  const projects = React.useMemo(() => {
    if (!projectsData?.items) return [];
    return projectsData.items.map((project) => ({
      id: project._id,
      name: project.name,
    }));
  }, [projectsData]);

  const handleExport = async () => {
    // Build filters object - only include filters that have been explicitly set
    const filters: CreateExportRequest['filters'] = {};

    // Only include date range if both dates are set
    if (dateRange.start && dateRange.end) {
      filters.dateRange = {
        start: dateRange.start,
        end: dateRange.end,
      };
    }

    // Only include project IDs if any are selected
    if (selectedProjects.length > 0) {
      filters.projectIds = selectedProjects;
    }

    // Only include cost range if the user has explicitly enabled the cost filter
    if (useCostFilter) {
      filters.costRange = {
        min: costRange.min,
        max: costRange.max,
      };
    }

    const exportRequest: CreateExportRequest = {
      format,
      filters: Object.keys(filters).length > 0 ? filters : undefined,
      options: {
        includeMessages: options.includeMessages,
        includeMetadata: options.includeMetadata,
        includeToolCalls: options.includeToolCalls,
        compress: options.compress,
        compressionFormat: compressionOptions.enabled
          ? compressionOptions.format
          : 'none',
        compressionLevel: compressionOptions.level,
      },
    };

    const response = await createExport.mutateAsync(exportRequest);
    if (response && onExportStarted) {
      onExportStarted(response.jobId);
    }
  };

  return (
    <Card className={cn('p-6', className)}>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Export Data
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Configure and export your conversation data in various formats
          </p>
        </div>

        {/* Format Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Export Format
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {(['json', 'csv', 'markdown', 'pdf'] as const).map((fmt) => (
              <button
                key={fmt}
                onClick={() => setFormat(fmt)}
                className={cn(
                  'p-3 text-sm font-medium rounded-lg border-2 transition-all',
                  format === fmt
                    ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300'
                )}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Date Range Picker */}
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
                  setDateRange((prev) => ({ ...prev, start: e.target.value }))
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
                  setDateRange((prev) => ({ ...prev, end: e.target.value }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                placeholder="End date"
              />
            </div>
          </div>
        </div>

        {/* Project Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            <Filter className="w-4 h-4 inline mr-2" />
            Projects
          </label>
          <div className="relative">
            <select
              multiple
              value={selectedProjects}
              onChange={(e) => {
                const values = Array.from(
                  e.target.selectedOptions,
                  (option) => option.value
                );
                setSelectedProjects(values);
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
        </div>

        {/* Cost Range Slider */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Cost Range Filter
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={useCostFilter}
                onChange={(e) => setUseCostFilter(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Enable cost filter
              </span>
            </label>
          </div>
          {useCostFilter && (
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Filter sessions by cost (USD): ${costRange.min} - $
                {costRange.max}
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <input
                    type="range"
                    min="0"
                    max="1000"
                    value={costRange.min}
                    onChange={(e) =>
                      setCostRange((prev) => ({
                        ...prev,
                        min: parseInt(e.target.value),
                      }))
                    }
                    className="w-full"
                  />
                  <span className="text-xs text-gray-500">
                    Min: ${costRange.min}
                  </span>
                </div>
                <div>
                  <input
                    type="range"
                    min="0"
                    max="1000"
                    value={costRange.max}
                    onChange={(e) =>
                      setCostRange((prev) => ({
                        ...prev,
                        max: parseInt(e.target.value),
                      }))
                    }
                    className="w-full"
                  />
                  <span className="text-xs text-gray-500">
                    Max: ${costRange.max}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Export Options
          </label>
          <div className="space-y-2">
            {[
              { key: 'includeMessages', label: 'Include Messages' },
              { key: 'includeMetadata', label: 'Include Metadata' },
              { key: 'includeToolCalls', label: 'Include Tool Calls' },
            ].map(({ key, label }) => (
              <label key={key} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={options[key as keyof typeof options]}
                  onChange={(e) =>
                    setOptions((prev) => ({
                      ...prev,
                      [key]: e.target.checked,
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

        {/* Compression Options */}
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <input
              type="checkbox"
              checked={compressionOptions.enabled}
              onChange={(e) =>
                setCompressionOptions((prev) => ({
                  ...prev,
                  enabled: e.target.checked,
                  format: e.target.checked ? 'tar.gz' : 'none',
                }))
              }
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Enable Compression
            </label>
          </div>

          {compressionOptions.enabled && (
            <div className="ml-6 space-y-4">
              {/* Compression Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Compression Format
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setCompressionOptions((prev) => ({
                        ...prev,
                        format: 'tar.gz',
                      }))
                    }
                    className={cn(
                      'p-3 rounded-lg border-2 transition-all text-sm',
                      compressionOptions.format === 'tar.gz'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    )}
                  >
                    <div className="font-medium">tar.gz</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      Universal compatibility
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setCompressionOptions((prev) => ({
                        ...prev,
                        format: 'zstd',
                      }))
                    }
                    className={cn(
                      'p-3 rounded-lg border-2 transition-all text-sm',
                      compressionOptions.format === 'zstd'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    )}
                  >
                    <div className="font-medium">zstd</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      Better compression, faster
                    </div>
                  </button>
                </div>
              </div>

              {/* Compression Level */}
              <div>
                <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Compression Level: {compressionOptions.level}
                </label>
                <div className="flex items-center space-x-4">
                  <span className="text-xs text-gray-500">Faster</span>
                  <input
                    type="range"
                    min="1"
                    max="9"
                    value={compressionOptions.level}
                    onChange={(e) =>
                      setCompressionOptions((prev) => ({
                        ...prev,
                        level: parseInt(e.target.value),
                      }))
                    }
                    className="flex-1"
                  />
                  <span className="text-xs text-gray-500">Smaller</span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {compressionOptions.level <= 3 &&
                    'Fast compression, larger file'}
                  {compressionOptions.level > 3 &&
                    compressionOptions.level <= 6 &&
                    'Balanced speed and size'}
                  {compressionOptions.level > 6 &&
                    'Maximum compression, slower'}
                </p>
              </div>

              {/* Format Recommendation */}
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  {compressionOptions.format === 'tar.gz' && (
                    <>
                      <strong>tar.gz recommended for:</strong> Manual downloads,
                      sharing with others, archival storage. Works with all
                      operating systems and tools.
                    </>
                  )}
                  {compressionOptions.format === 'zstd' && (
                    <>
                      <strong>zstd recommended for:</strong> API consumption,
                      automated processing, frequent downloads. 30% better
                      compression than gzip.
                    </>
                  )}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Export Button */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            onClick={handleExport}
            disabled={createExport.isPending}
            className="px-6"
          >
            {createExport.isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                Creating Export...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Create Export
              </>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
};
