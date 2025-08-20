import * as React from 'react';
import { cn } from '@/utils/cn';
import { Button } from '@/components/common/Button';
import { Card } from '@/components/common/Card';
import { useCreateExport } from '@/hooks/useExport';
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

  // Form state
  const [format, setFormat] = React.useState<
    'json' | 'csv' | 'markdown' | 'pdf'
  >('json');
  const [dateRange, setDateRange] = React.useState({
    start: '',
    end: '',
  });
  const [selectedProjects, setSelectedProjects] = React.useState<string[]>([]);
  const [costRange, setCostRange] = React.useState({ min: 0, max: 100 });
  const [options, setOptions] = React.useState({
    includeMessages: true,
    includeMetadata: true,
    includeToolCalls: true,
    compress: false,
    redactPii: false,
    anonymizeUsers: false,
    removeApiKeys: true,
  });

  // Mock data for demo - in real app, these would come from API
  const projects = [
    { id: '1', name: 'Project Alpha' },
    { id: '2', name: 'Project Beta' },
    { id: '3', name: 'Project Gamma' },
  ];

  const handleExport = async () => {
    const exportRequest: CreateExportRequest = {
      format,
      filters: {
        ...(dateRange.start &&
          dateRange.end && {
            dateRange: {
              start: dateRange.start,
              end: dateRange.end,
            },
          }),
        ...(selectedProjects.length > 0 && { projectIds: selectedProjects }),
        costRange: {
          min: costRange.min,
          max: costRange.max,
        },
      },
      options: {
        includeMessages: options.includeMessages,
        includeMetadata: options.includeMetadata,
        includeToolCalls: options.includeToolCalls,
        compress: options.compress,
        privacy: {
          redactPii: options.redactPii,
          anonymizeUsers: options.anonymizeUsers,
          removeApiKeys: options.removeApiKeys,
        },
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
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Cost Range Slider */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Cost Range (USD): ${costRange.min} - ${costRange.max}
          </label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <input
                type="range"
                min="0"
                max="100"
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
                max="100"
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

        {/* Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Export Options
          </label>
          <div className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Content Options */}
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">
                  Content
                </h4>
                {[
                  { key: 'includeMessages', label: 'Include Messages' },
                  { key: 'includeMetadata', label: 'Include Metadata' },
                  { key: 'includeToolCalls', label: 'Include Tool Calls' },
                  { key: 'compress', label: 'Compress Output' },
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

              {/* Privacy Options */}
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">
                  Privacy
                </h4>
                {[
                  { key: 'redactPii', label: 'Redact PII' },
                  { key: 'anonymizeUsers', label: 'Anonymize Users' },
                  { key: 'removeApiKeys', label: 'Remove API Keys' },
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
          </div>
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
