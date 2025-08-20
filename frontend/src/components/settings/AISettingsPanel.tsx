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
} from '@/hooks/useAI';
import { cn } from '@/utils/cn';
import { formatDistanceToNow } from 'date-fns';

export function AISettingsPanel() {
  const { data: settings, isLoading } = useAISettings();
  const { data: stats } = useAIStats();
  const updateSettings = useUpdateAISettings();
  const testConnection = useTestConnection();

  const [formData, setFormData] = useState({
    enabled: false,
    api_key: '',
    model: 'claude-3-sonnet-20240229',
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
        model: settings.model ?? 'claude-3-sonnet-20240229',
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
        formData.model !== (settings.model ?? 'claude-3-sonnet-20240229') ||
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
        api_key: formData.api_key,
        model: formData.model,
        base_url: formData.base_url || undefined,
      });
    } catch (error) {
      console.error('Connection test failed:', error);
    }
  };

  const availableModels = [
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
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
      <div className="flex items-center gap-2 pb-4 border-b">
        <Settings className="h-5 w-5 text-purple-500" />
        <h2 className="text-xl font-semibold">AI Assistant Settings</h2>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <h3 className="text-sm font-medium text-gray-900">
            Enable AI Assistant
          </h3>
          <p className="text-sm text-gray-500">
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
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Key *
          </label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={formData.api_key}
              onChange={(e) => handleInputChange('api_key', e.target.value)}
              placeholder="Enter your API key..."
              disabled={!formData.enabled}
              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              disabled={!formData.enabled}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 disabled:cursor-not-allowed"
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
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Model
          </label>
          <select
            value={formData.model}
            onChange={(e) => handleInputChange('model', e.target.value)}
            disabled={!formData.enabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {availableModels.map((model) => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))}
          </select>
        </div>

        {/* Base URL (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Base URL (Optional)
          </label>
          <input
            type="url"
            value={formData.base_url}
            onChange={(e) => handleInputChange('base_url', e.target.value)}
            placeholder="https://api.anthropic.com (leave empty for default)"
            disabled={!formData.enabled}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>

        {/* Advanced Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
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
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border border-gray-300 rounded-md transition-colors',
            formData.api_key && formData.enabled
              ? 'text-gray-700 bg-white hover:bg-gray-50'
              : 'text-gray-400 bg-gray-50 cursor-not-allowed'
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
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">Total Requests</div>
              <div className="text-2xl font-semibold text-gray-900">
                {stats.total_requests.toLocaleString()}
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">Success Rate</div>
              <div className="text-2xl font-semibold text-green-600">
                {stats.total_requests > 0
                  ? `${Math.round((stats.successful_requests / stats.total_requests) * 100)}%`
                  : '0%'}
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">Tokens Used</div>
              <div className="text-2xl font-semibold text-blue-600">
                {stats.total_tokens_used.toLocaleString()}
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-500">Est. Cost</div>
              <div className="text-2xl font-semibold text-purple-600">
                ${stats.estimated_total_cost.toFixed(2)}
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
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
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
