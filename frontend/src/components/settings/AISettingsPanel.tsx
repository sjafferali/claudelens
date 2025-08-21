import { useState, useEffect } from 'react';
import {
  Eye,
  EyeOff,
  TestTube,
  Save,
  RefreshCw,
  Settings,
  BarChart3,
  Info,
} from 'lucide-react';
import {
  useAISettings,
  useUpdateAISettings,
  useTestConnection,
  useAIStats,
  useAvailableModels,
} from '@/hooks/useAI';
import { cn } from '@/utils/cn';
import { formatDistanceToNow } from 'date-fns';

export function AISettingsPanel() {
  const { data: settings, isLoading } = useAISettings();
  const { data: stats } = useAIStats();
  const modelsQuery = useAvailableModels();
  const modelsData = modelsQuery.data;
  const updateSettings = useUpdateAISettings();
  const testConnection = useTestConnection();

  const [formData, setFormData] = useState({
    enabled: false,
    api_key: '',
    model: 'gpt-4',
    base_url: '',
    max_tokens: 4096,
    temperature: 0.7,
  });

  const [showApiKey, setShowApiKey] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Update form data when settings are loaded
  useEffect(() => {
    if (settings) {
      setFormData({
        enabled: settings.enabled ?? false,
        api_key: settings.api_key ?? '',
        model: settings.model ?? 'gpt-4',
        base_url: settings.base_url ?? '',
        max_tokens: settings.max_tokens ?? 4096,
        temperature: settings.temperature ?? 0.7,
      });
      setHasChanges(false);
    }
  }, [settings]);

  // Track changes
  useEffect(() => {
    if (settings) {
      const hasChanged =
        formData.enabled !== (settings.enabled ?? false) ||
        formData.api_key !== (settings.api_key ?? '') ||
        formData.model !== (settings.model ?? 'gpt-4') ||
        formData.base_url !== (settings.base_url ?? '') ||
        formData.max_tokens !== (settings.max_tokens ?? 4096) ||
        formData.temperature !== (settings.temperature ?? 0.7);

      setHasChanges(hasChanged);
    }
  }, [formData, settings]);

  const handleInputChange = (
    field: string,
    value: string | number | boolean
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save AI settings:', error);
    }
  };

  const handleTestConnection = async () => {
    try {
      await testConnection.mutateAsync({
        test_prompt: 'Hello, this is a connection test.',
      });
    } catch (error) {
      console.error('Connection test failed:', error);
    }
  };

  // Use fetched models or fallback to defaults
  const availableModels = modelsData?.models
    ? modelsData.models.map((model) => ({
        value: model.id,
        label: model.name,
      }))
    : [
        { value: 'gpt-4', label: 'GPT-4' },
        { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
        { value: 'gpt-3.5-turbo-16k', label: 'GPT-3.5 Turbo 16K' },
      ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
        <Settings className="h-5 w-5 text-purple-500" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          AI Assistant Settings
        </h2>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Enable AI Assistant
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Allow AI to assist with prompt generation and metadata creation
          </p>
        </div>
        <button
          onClick={() => handleInputChange('enabled', !formData.enabled)}
          className={cn(
            'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
            formData.enabled ? 'bg-purple-600' : 'bg-gray-200'
          )}
        >
          <span
            className={cn(
              'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
              formData.enabled ? 'translate-x-5' : 'translate-x-0'
            )}
          />
        </button>
      </div>

      {/* Configuration Form */}
      <div className={cn('space-y-4', !formData.enabled && 'opacity-50')}>
        {/* API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            API Key *
          </label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={formData.api_key}
              onChange={(e) => handleInputChange('api_key', e.target.value)}
              placeholder="Enter your API key..."
              disabled={!formData.enabled}
              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              disabled={!formData.enabled}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 disabled:cursor-not-allowed"
            >
              {showApiKey ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Model Selection */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Model
              </label>
              <div className="group relative">
                <Info className="h-3 w-3 text-gray-400" />
                <div className="absolute hidden group-hover:block z-10 w-64 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg -left-2 top-5">
                  Models are loaded from your configured API endpoint after
                  saving the API key. Use the refresh button to reload the list.
                </div>
              </div>
            </div>
            {settings?.api_key_configured && (
              <button
                type="button"
                onClick={() => modelsQuery.refetch()}
                disabled={!formData.enabled || modelsQuery.isFetching}
                className="text-xs text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <RefreshCw
                  className={cn(
                    'h-3 w-3',
                    modelsQuery.isFetching && 'animate-spin'
                  )}
                />
                Refresh Models
              </button>
            )}
          </div>
          <div className="relative">
            <select
              value={formData.model}
              onChange={(e) => handleInputChange('model', e.target.value)}
              disabled={!formData.enabled}
              className="w-full px-3 py-2 pr-8 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            >
              {availableModels.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
            {!settings?.api_key_configured && formData.enabled && (
              <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                Save your API key first to load available models
              </p>
            )}
            {modelsData?.is_fallback && settings?.api_key_configured && (
              <div className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                Using default model list (API unavailable)
              </div>
            )}
          </div>
        </div>

        {/* Base URL (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Base URL (Optional)
          </label>
          <input
            type="url"
            value={formData.base_url}
            onChange={(e) => handleInputChange('base_url', e.target.value)}
            placeholder="https://api.anthropic.com (leave empty for default)"
            disabled={!formData.enabled}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
          />
        </div>

        {/* Advanced Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              min="1"
              max="100000"
              value={formData.max_tokens}
              onChange={(e) =>
                handleInputChange(
                  'max_tokens',
                  parseInt(e.target.value) || 4096
                )
              }
              disabled={!formData.enabled}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Temperature
            </label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={formData.temperature}
              onChange={(e) =>
                handleInputChange(
                  'temperature',
                  parseFloat(e.target.value) || 0.7
                )
              }
              disabled={!formData.enabled}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={
            !hasChanges || updateSettings.isPending || !formData.enabled
          }
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors',
            hasChanges && formData.enabled
              ? 'bg-purple-600 text-white hover:bg-purple-700'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          )}
        >
          {updateSettings.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save Changes
        </button>

        <button
          onClick={handleTestConnection}
          disabled={
            !formData.api_key || !formData.enabled || testConnection.isPending
          }
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border rounded-md transition-colors',
            formData.api_key && formData.enabled
              ? 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 border-gray-300 dark:border-gray-600'
              : 'text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-900 cursor-not-allowed border-gray-200 dark:border-gray-700'
          )}
        >
          {testConnection.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <TestTube className="h-4 w-4" />
          )}
          Test Connection
        </button>
      </div>

      {/* Usage Statistics */}
      {stats && formData.enabled && (
        <div className="border-t pt-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-5 w-5 text-purple-500" />
            <h3 className="text-lg font-medium">Usage Statistics</h3>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Total Requests
              </div>
              <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {(stats.total_requests ?? 0).toLocaleString()}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Success Rate
              </div>
              <div className="text-2xl font-semibold text-green-600">
                {(stats.total_requests ?? 0) > 0
                  ? `${Math.round(((stats.successful_requests ?? 0) / (stats.total_requests ?? 1)) * 100)}%`
                  : '0%'}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Tokens Used
              </div>
              <div className="text-2xl font-semibold text-blue-600">
                {(stats.total_tokens_used ?? 0).toLocaleString()}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Est. Cost
              </div>
              <div className="text-2xl font-semibold text-purple-600">
                ${(stats.estimated_total_cost ?? 0).toFixed(2)}
              </div>
            </div>
          </div>

          {stats.last_request_at && (
            <div className="mt-4 text-sm text-gray-500">
              Last request:{' '}
              {formatDistanceToNow(new Date(stats.last_request_at), {
                addSuffix: true,
              })}
            </div>
          )}
        </div>
      )}

      {/* Information Panel */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-1">About AI Assistant</p>
            <p>
              The AI assistant helps generate prompt metadata (names,
              descriptions, tags) and content. It requires an API key from
              Anthropic, OpenAI, or compatible providers. Your API key is stored
              securely and only used for AI generation requests.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
