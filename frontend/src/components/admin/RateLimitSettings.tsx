import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Shield,
  Info,
  Save,
  RotateCcw,
  Clock,
  Globe,
  Cpu,
  Search,
  Upload,
  Download,
  HardDrive,
  MessageSquare,
  BarChart3,
  FileText,
} from 'lucide-react';
import { adminRateLimitsApi, RateLimitSettings } from '@/api/admin/rateLimits';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import Loading from '@/components/common/Loading';

interface RateLimitFieldProps {
  label: string;
  value: number | boolean;
  onChange: (value: number | boolean) => void;
  type: 'number' | 'boolean';
  min?: number;
  max?: number;
  unit?: string;
  tooltip: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

const RateLimitField: React.FC<RateLimitFieldProps> = ({
  label,
  value,
  onChange,
  type,
  min = 0,
  max,
  unit,
  tooltip,
  icon,
  disabled = false,
}) => {
  return (
    <div className="flex items-start space-x-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
      {icon && (
        <div className="mt-1 text-gray-500 dark:text-gray-400">{icon}</div>
      )}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
            <div className="group inline-block ml-2">
              <Info className="inline w-4 h-4 text-gray-400 cursor-help" />
              <div className="invisible group-hover:visible absolute z-10 mt-2 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                {tooltip}
              </div>
            </div>
          </label>
          <div className="flex items-center space-x-2">
            {type === 'boolean' ? (
              <button
                onClick={() => onChange(!value)}
                disabled={disabled}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  value ? 'bg-blue-600' : 'bg-gray-300'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    value ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            ) : (
              <>
                <input
                  type="number"
                  value={value as number}
                  onChange={(e) => onChange(parseInt(e.target.value, 10))}
                  min={min}
                  max={max}
                  disabled={disabled}
                  className="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 disabled:opacity-50"
                />
                {unit && (
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {unit}
                  </span>
                )}
                {value === 0 && (
                  <span className="text-xs text-yellow-600 dark:text-yellow-400">
                    (unlimited)
                  </span>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export const RateLimitSettingsPanel: React.FC = () => {
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<RateLimitSettings | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin', 'rate-limits'],
    queryFn: adminRateLimitsApi.getSettings,
  });

  React.useEffect(() => {
    if (data) {
      setSettings(data);
    }
  }, [data]);

  const updateMutation = useMutation({
    mutationFn: adminRateLimitsApi.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'rate-limits'] });
      setHasChanges(false);
      // Show success toast or notification
    },
  });

  const resetMutation = useMutation({
    mutationFn: adminRateLimitsApi.resetToDefaults,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'rate-limits'] });
      setHasChanges(false);
    },
  });

  const handleFieldChange = (
    field: keyof RateLimitSettings,
    value: string | number | boolean
  ) => {
    if (settings) {
      setSettings({ ...settings, [field]: value });
      setHasChanges(true);
    }
  };

  const handleSave = () => {
    if (settings) {
      updateMutation.mutate(settings);
    }
  };

  const handleReset = () => {
    if (
      confirm(
        'Are you sure you want to reset all rate limits to default values?'
      )
    ) {
      resetMutation.mutate();
    }
  };

  if (isLoading) return <Loading />;
  if (error) return <div>Error loading rate limit settings</div>;
  if (!settings) return null;

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Rate Limit Configuration
              </CardTitle>
              <CardDescription>
                Configure rate limits to protect your system from abuse and
                ensure fair usage
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={resetMutation.isPending}
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleSave}
                disabled={!hasChanges || updateMutation.isPending}
              >
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Global Enable/Disable */}
          <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <RateLimitField
              label="Enable Rate Limiting System"
              value={settings.rate_limiting_enabled}
              onChange={(v) => handleFieldChange('rate_limiting_enabled', v)}
              type="boolean"
              tooltip="Master switch to enable or disable all rate limiting features system-wide"
              icon={<Shield className="w-5 h-5" />}
            />
          </div>

          {/* HTTP Rate Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Globe className="w-5 h-5" />
              HTTP API Rate Limits
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Enable HTTP Rate Limiting"
                value={settings.http_rate_limit_enabled}
                onChange={(v) =>
                  handleFieldChange('http_rate_limit_enabled', v)
                }
                type="boolean"
                tooltip="Enable rate limiting for HTTP API endpoints"
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Requests Per Minute"
                value={settings.http_calls_per_minute}
                onChange={(v) => handleFieldChange('http_calls_per_minute', v)}
                type="number"
                min={0}
                max={10000}
                unit="req/min"
                tooltip="Maximum number of HTTP requests allowed per minute per client (IP or API key). Set to 0 for unlimited."
                disabled={
                  !settings.rate_limiting_enabled ||
                  !settings.http_rate_limit_enabled
                }
              />
              <RateLimitField
                label="Rate Limit Window"
                value={settings.http_rate_limit_window_seconds}
                onChange={(v) =>
                  handleFieldChange('http_rate_limit_window_seconds', v)
                }
                type="number"
                min={1}
                max={3600}
                unit="seconds"
                tooltip="Time window for HTTP rate limiting in seconds"
                disabled={
                  !settings.rate_limiting_enabled ||
                  !settings.http_rate_limit_enabled
                }
              />
            </div>
          </div>

          {/* CLI/Ingestion Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Upload className="w-5 h-5" />
              CLI & Data Ingestion
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Enable CLI Ingestion"
                value={settings.ingest_enabled}
                onChange={(v) => handleFieldChange('ingest_enabled', v)}
                type="boolean"
                tooltip="Allow data ingestion from the CLI tool"
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Ingestion Batches Per Hour"
                value={settings.ingest_rate_limit_per_hour}
                onChange={(v) =>
                  handleFieldChange('ingest_rate_limit_per_hour', v)
                }
                type="number"
                min={0}
                max={10000}
                unit="batches/hr"
                tooltip="Maximum number of ingestion batches allowed per hour from CLI. Set to 0 for unlimited."
                disabled={
                  !settings.rate_limiting_enabled || !settings.ingest_enabled
                }
              />
              <RateLimitField
                label="Max Batch Size"
                value={settings.ingest_max_batch_size}
                onChange={(v) => handleFieldChange('ingest_max_batch_size', v)}
                type="number"
                min={1}
                max={10000}
                unit="messages"
                tooltip="Maximum number of messages allowed per ingestion batch"
                disabled={
                  !settings.rate_limiting_enabled || !settings.ingest_enabled
                }
              />
              <RateLimitField
                label="Max File Size"
                value={settings.ingest_max_file_size_mb}
                onChange={(v) =>
                  handleFieldChange('ingest_max_file_size_mb', v)
                }
                type="number"
                min={1}
                max={500}
                unit="MB"
                tooltip="Maximum size of JSONL files that can be ingested"
                disabled={
                  !settings.rate_limiting_enabled || !settings.ingest_enabled
                }
              />
            </div>
          </div>

          {/* AI/LLM Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              AI & LLM Features
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Enable AI Rate Limiting"
                value={settings.ai_rate_limit_enabled}
                onChange={(v) => handleFieldChange('ai_rate_limit_enabled', v)}
                type="boolean"
                tooltip="Enable rate limiting for AI-powered features"
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="AI Requests Per Minute"
                value={settings.ai_rate_limit_per_minute}
                onChange={(v) =>
                  handleFieldChange('ai_rate_limit_per_minute', v)
                }
                type="number"
                min={0}
                max={100}
                unit="req/min"
                tooltip="Maximum number of AI requests per minute per user. Set to 0 for unlimited."
                disabled={
                  !settings.rate_limiting_enabled ||
                  !settings.ai_rate_limit_enabled
                }
              />
              <RateLimitField
                label="Max Tokens Per Request"
                value={settings.ai_max_tokens}
                onChange={(v) => handleFieldChange('ai_max_tokens', v)}
                type="number"
                min={100}
                max={32000}
                unit="tokens"
                tooltip="Maximum tokens allowed per AI request"
                disabled={
                  !settings.rate_limiting_enabled ||
                  !settings.ai_rate_limit_enabled
                }
              />
            </div>
          </div>

          {/* Export/Import Operations */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Download className="w-5 h-5" />
              Export & Import Operations
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Export Operations Per Hour"
                value={settings.export_limit_per_hour}
                onChange={(v) => handleFieldChange('export_limit_per_hour', v)}
                type="number"
                min={0}
                max={100}
                unit="ops/hr"
                tooltip="Maximum number of export operations per hour per user. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Import Operations Per Hour"
                value={settings.import_limit_per_hour}
                onChange={(v) => handleFieldChange('import_limit_per_hour', v)}
                type="number"
                min={0}
                max={100}
                unit="ops/hr"
                tooltip="Maximum number of import operations per hour per user. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Max Upload Size"
                value={settings.max_upload_size_mb}
                onChange={(v) => handleFieldChange('max_upload_size_mb', v)}
                type="number"
                min={0}
                max={1000}
                unit="MB"
                tooltip="Maximum file size for uploads. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Max Export Size"
                value={settings.max_export_size_mb}
                onChange={(v) => handleFieldChange('max_export_size_mb', v)}
                type="number"
                min={0}
                max={5000}
                unit="MB"
                tooltip="Maximum size of exported data. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
            </div>
          </div>

          {/* Backup/Restore Operations */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <HardDrive className="w-5 h-5" />
              Backup & Restore
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Backup Operations Per Hour"
                value={settings.backup_limit_per_hour}
                onChange={(v) => handleFieldChange('backup_limit_per_hour', v)}
                type="number"
                min={0}
                max={100}
                unit="ops/hr"
                tooltip="Maximum number of backup operations per hour per user. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Restore Operations Per Hour"
                value={settings.restore_limit_per_hour}
                onChange={(v) => handleFieldChange('restore_limit_per_hour', v)}
                type="number"
                min={0}
                max={100}
                unit="ops/hr"
                tooltip="Maximum number of restore operations per hour per user. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Max Backup Size"
                value={settings.max_backup_size_gb}
                onChange={(v) => handleFieldChange('max_backup_size_gb', v)}
                type="number"
                min={0}
                max={1000}
                unit="GB"
                tooltip="Maximum size of backup files. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
            </div>
          </div>

          {/* WebSocket Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              WebSocket Connections
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Enable WebSocket Connections"
                value={settings.websocket_enabled}
                onChange={(v) => handleFieldChange('websocket_enabled', v)}
                type="boolean"
                tooltip="Allow WebSocket connections for real-time features"
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Max Connections Per User"
                value={settings.websocket_max_connections_per_user}
                onChange={(v) =>
                  handleFieldChange('websocket_max_connections_per_user', v)
                }
                type="number"
                min={1}
                max={50}
                unit="connections"
                tooltip="Maximum concurrent WebSocket connections per user"
                disabled={
                  !settings.rate_limiting_enabled || !settings.websocket_enabled
                }
              />
              <RateLimitField
                label="Messages Per Second"
                value={settings.websocket_message_rate_per_second}
                onChange={(v) =>
                  handleFieldChange('websocket_message_rate_per_second', v)
                }
                type="number"
                min={1}
                max={100}
                unit="msg/sec"
                tooltip="Maximum WebSocket messages per second per connection"
                disabled={
                  !settings.rate_limiting_enabled || !settings.websocket_enabled
                }
              />
            </div>
          </div>

          {/* Search Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Search className="w-5 h-5" />
              Search Operations
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Search Requests Per Minute"
                value={settings.search_rate_limit_per_minute}
                onChange={(v) =>
                  handleFieldChange('search_rate_limit_per_minute', v)
                }
                type="number"
                min={0}
                max={1000}
                unit="req/min"
                tooltip="Maximum search requests per minute. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Max Search Results"
                value={settings.search_max_results}
                onChange={(v) => handleFieldChange('search_max_results', v)}
                type="number"
                min={10}
                max={10000}
                unit="results"
                tooltip="Maximum number of results returned in a single search"
                disabled={!settings.rate_limiting_enabled}
              />
            </div>
          </div>

          {/* Analytics Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Analytics & Reporting
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Analytics Queries Per Minute"
                value={settings.analytics_rate_limit_per_minute}
                onChange={(v) =>
                  handleFieldChange('analytics_rate_limit_per_minute', v)
                }
                type="number"
                min={0}
                max={100}
                unit="queries/min"
                tooltip="Maximum analytics queries per minute. Set to 0 for unlimited."
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Max Date Range"
                value={settings.analytics_max_date_range_days}
                onChange={(v) =>
                  handleFieldChange('analytics_max_date_range_days', v)
                }
                type="number"
                min={1}
                max={3650}
                unit="days"
                tooltip="Maximum date range allowed for analytics queries"
                disabled={!settings.rate_limiting_enabled}
              />
            </div>
          </div>

          {/* Pagination Limits */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              API Pagination
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Max Page Size"
                value={settings.max_page_size}
                onChange={(v) => handleFieldChange('max_page_size', v)}
                type="number"
                min={10}
                max={10000}
                unit="items"
                tooltip="Maximum number of items that can be requested per page in API responses"
                disabled={!settings.rate_limiting_enabled}
              />
              <RateLimitField
                label="Default Page Size"
                value={settings.default_page_size}
                onChange={(v) => handleFieldChange('default_page_size', v)}
                type="number"
                min={10}
                max={100}
                unit="items"
                tooltip="Default number of items per page when not specified in API requests"
                disabled={!settings.rate_limiting_enabled}
              />
            </div>
          </div>

          {/* General Settings */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              General Settings
            </h3>
            <div className="space-y-2">
              <RateLimitField
                label="Operation Rate Limit Window"
                value={settings.rate_limit_window_hours}
                onChange={(v) =>
                  handleFieldChange('rate_limit_window_hours', v)
                }
                type="number"
                min={1}
                max={24}
                unit="hours"
                tooltip="Time window for operation-based rate limits (export, import, backup, restore)"
                disabled={!settings.rate_limiting_enabled}
              />
            </div>
          </div>

          {/* Last Updated Info */}
          {settings.updated_at && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Last updated: {new Date(settings.updated_at).toLocaleString()}
                {settings.updated_by && ` by ${settings.updated_by}`}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
