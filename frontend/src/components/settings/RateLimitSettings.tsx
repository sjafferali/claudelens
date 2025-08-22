import { useState, useEffect } from 'react';
import { Shield, Save, AlertCircle, RefreshCw } from 'lucide-react';
import {
  rateLimitSettingsApi,
  type RateLimitSettings,
} from '@/api/rateLimitSettings';
import { cn } from '@/utils/cn';

export function RateLimitSettingsPanel() {
  const [settings, setSettings] = useState<RateLimitSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await rateLimitSettingsApi.getSettings();
      setSettings(data);
    } catch (err) {
      setError('Failed to load rate limit settings');
      console.error('Error loading rate limit settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      setSaving(true);
      setSuccessMessage(null);
      const updatedSettings =
        await rateLimitSettingsApi.updateSettings(settings);
      setSettings(updatedSettings);
      setSuccessMessage('Rate limit settings have been updated successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save rate limit settings. Please try again.');
      console.error('Error saving rate limit settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (
    field: keyof RateLimitSettings,
    value: number | boolean
  ) => {
    if (!settings) return;
    setSettings({
      ...settings,
      [field]: value,
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !settings) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">{error}</p>
          <button
            onClick={loadSettings}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!settings) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Success Message */}
      {successMessage && (
        <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-green-800 dark:text-green-200 text-sm">
            {successMessage}
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && settings && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Enable/Disable Rate Limiting */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="h-5 w-5 text-purple-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Rate Limiting Control
            </h3>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Enable or disable rate limiting for all operations
          </p>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Enable Rate Limiting
            </label>
            <button
              onClick={() =>
                handleInputChange(
                  'rate_limiting_enabled',
                  !settings.rate_limiting_enabled
                )
              }
              className={cn(
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
                settings.rate_limiting_enabled ? 'bg-purple-600' : 'bg-gray-200'
              )}
            >
              <span
                className={cn(
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  settings.rate_limiting_enabled
                    ? 'translate-x-5'
                    : 'translate-x-0'
                )}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Operation Limits */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Operation Limits
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure rate limits for different operations (per hour)
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Export Limit
              </label>
              <input
                type="number"
                min="0"
                value={settings.export_limit_per_hour}
                onChange={(e) =>
                  handleInputChange(
                    'export_limit_per_hour',
                    parseInt(e.target.value) || 0
                  )
                }
                disabled={!settings.rate_limiting_enabled}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Import Limit
              </label>
              <input
                type="number"
                min="0"
                value={settings.import_limit_per_hour}
                onChange={(e) =>
                  handleInputChange(
                    'import_limit_per_hour',
                    parseInt(e.target.value) || 0
                  )
                }
                disabled={!settings.rate_limiting_enabled}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Backup Limit
              </label>
              <input
                type="number"
                min="0"
                value={settings.backup_limit_per_hour}
                onChange={(e) =>
                  handleInputChange(
                    'backup_limit_per_hour',
                    parseInt(e.target.value) || 0
                  )
                }
                disabled={!settings.rate_limiting_enabled}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Restore Limit
              </label>
              <input
                type="number"
                min="0"
                value={settings.restore_limit_per_hour}
                onChange={(e) =>
                  handleInputChange(
                    'restore_limit_per_hour',
                    parseInt(e.target.value) || 0
                  )
                }
                disabled={!settings.rate_limiting_enabled}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* File Size Limits */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            File Size Limits
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure maximum file sizes for uploads and exports
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Upload Size (MB)
              </label>
              <input
                type="number"
                min="0"
                value={settings.max_upload_size_mb}
                onChange={(e) =>
                  handleInputChange(
                    'max_upload_size_mb',
                    parseInt(e.target.value) || 0
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Export Size (MB)
              </label>
              <input
                type="number"
                min="0"
                value={settings.max_export_size_mb}
                onChange={(e) =>
                  handleInputChange(
                    'max_export_size_mb',
                    parseInt(e.target.value) || 0
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Max Backup Size (GB)
              </label>
              <input
                type="number"
                min="0"
                value={settings.max_backup_size_gb}
                onChange={(e) =>
                  handleInputChange(
                    'max_backup_size_gb',
                    parseInt(e.target.value) || 0
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                0 = unlimited
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Pagination Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Pagination Settings
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure default and maximum page sizes for lists
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Default Page Size
              </label>
              <input
                type="number"
                min="10"
                max="100"
                value={settings.default_page_size}
                onChange={(e) =>
                  handleInputChange(
                    'default_page_size',
                    parseInt(e.target.value) || 20
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Maximum Page Size
              </label>
              <input
                type="number"
                min="10"
                max="10000"
                value={settings.max_page_size}
                onChange={(e) =>
                  handleInputChange(
                    'max_page_size',
                    parseInt(e.target.value) || 100
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Rate Limit Window */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Rate Limit Window
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure the time window for rate limit calculations
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Window Duration (hours)
            </label>
            <input
              type="number"
              min="1"
              max="24"
              value={settings.rate_limit_window_hours}
              onChange={(e) =>
                handleInputChange(
                  'rate_limit_window_hours',
                  parseInt(e.target.value) || 1
                )
              }
              disabled={!settings.rate_limiting_enabled}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Rate limits apply within this rolling time window
            </p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Save className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
