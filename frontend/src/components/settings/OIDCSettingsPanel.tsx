import { useState, useEffect } from 'react';
import {
  Eye,
  EyeOff,
  TestTube,
  Save,
  RefreshCw,
  Shield,
  Info,
  Users,
} from 'lucide-react';
import {
  getOIDCSettings,
  updateOIDCSettings,
  testOIDCConnection,
  type OIDCSettings,
} from '@/api/oidcApi';
import { cn } from '@/utils/cn';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

export function OIDCSettingsPanel() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['oidc-settings'],
    queryFn: getOIDCSettings,
  });

  const updateMutation = useMutation({
    mutationFn: updateOIDCSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oidc-settings'] });
      toast.success('OIDC settings saved successfully');
      setHasChanges(false);
    },
    onError: (error: unknown) => {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Failed to save OIDC settings');
    },
  });

  const testConnectionMutation = useMutation({
    mutationFn: testOIDCConnection,
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Successfully connected to OIDC provider');
      } else {
        toast.error(data.message || 'Connection test failed');
      }
    },
    onError: (error: unknown) => {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Connection test failed');
    },
  });

  const [formData, setFormData] = useState<Partial<OIDCSettings>>({
    enabled: false,
    client_id: '',
    client_secret: '',
    discovery_endpoint: '',
    redirect_uri: '',
    scopes: ['openid', 'email', 'profile'],
    auto_create_users: true,
    default_role: 'user',
  });

  const [showClientSecret, setShowClientSecret] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [scopeInput, setScopeInput] = useState('');

  // Update form data when settings are loaded
  useEffect(() => {
    if (settings) {
      setFormData({
        enabled: settings.enabled ?? false,
        client_id: settings.client_id ?? '',
        client_secret: '', // Never populate client secret for security
        discovery_endpoint: settings.discovery_endpoint ?? '',
        redirect_uri: settings.redirect_uri ?? '',
        scopes: settings.scopes ?? ['openid', 'email', 'profile'],
        auto_create_users: settings.auto_create_users ?? true,
        default_role: settings.default_role ?? 'user',
      });
      setHasChanges(false);
    }
  }, [settings]);

  // Track changes
  useEffect(() => {
    if (settings) {
      const hasChanged =
        formData.enabled !== (settings.enabled ?? false) ||
        formData.client_id !== (settings.client_id ?? '') ||
        formData.client_secret !== '' ||
        formData.discovery_endpoint !== (settings.discovery_endpoint ?? '') ||
        formData.redirect_uri !== (settings.redirect_uri ?? '') ||
        JSON.stringify(formData.scopes) !==
          JSON.stringify(settings.scopes ?? ['openid', 'email', 'profile']) ||
        formData.auto_create_users !== (settings.auto_create_users ?? true) ||
        formData.default_role !== (settings.default_role ?? 'user');

      setHasChanges(hasChanged);
    }
  }, [formData, settings]);

  const handleInputChange = (
    field: keyof OIDCSettings,
    value: string | boolean | string[]
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddScope = () => {
    if (scopeInput.trim() && !formData.scopes?.includes(scopeInput.trim())) {
      handleInputChange('scopes', [
        ...(formData.scopes || []),
        scopeInput.trim(),
      ]);
      setScopeInput('');
    }
  };

  const handleRemoveScope = (scope: string) => {
    handleInputChange(
      'scopes',
      formData.scopes?.filter((s) => s !== scope) || []
    );
  };

  const handleSave = async () => {
    await updateMutation.mutateAsync(formData);
  };

  const handleTestConnection = async () => {
    if (formData.discovery_endpoint) {
      await testConnectionMutation.mutateAsync({
        discovery_endpoint: formData.discovery_endpoint,
      });
    }
  };

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
        <Shield className="h-5 w-5 text-purple-500" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          OpenID Connect Settings
        </h2>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Enable OIDC Authentication
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Allow users to authenticate via OpenID Connect providers
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
        {/* Client ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Client ID *
          </label>
          <input
            type="text"
            value={formData.client_id}
            onChange={(e) => handleInputChange('client_id', e.target.value)}
            placeholder="your-oidc-client-id"
            disabled={!formData.enabled}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
          />
        </div>

        {/* Client Secret */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Client Secret {settings?.api_key_configured && '(configured)'}
          </label>
          <div className="relative">
            <input
              type={showClientSecret ? 'text' : 'password'}
              value={formData.client_secret}
              onChange={(e) =>
                handleInputChange('client_secret', e.target.value)
              }
              placeholder={
                settings?.api_key_configured
                  ? 'Enter to update...'
                  : 'Enter client secret...'
              }
              disabled={!formData.enabled}
              className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            />
            <button
              type="button"
              onClick={() => setShowClientSecret(!showClientSecret)}
              disabled={!formData.enabled}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 disabled:cursor-not-allowed"
            >
              {showClientSecret ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Discovery Endpoint */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Discovery Endpoint URL *
          </label>
          <input
            type="url"
            value={formData.discovery_endpoint}
            onChange={(e) =>
              handleInputChange('discovery_endpoint', e.target.value)
            }
            placeholder="https://auth.example.com/.well-known/openid-configuration"
            disabled={!formData.enabled}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
          />
        </div>

        {/* Redirect URI */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Redirect URI *
          </label>
          <input
            type="url"
            value={formData.redirect_uri}
            onChange={(e) => handleInputChange('redirect_uri', e.target.value)}
            placeholder={`${window.location.origin}/api/v1/auth/oidc/callback`}
            disabled={!formData.enabled}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
          />
        </div>

        {/* Scopes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            OIDC Scopes
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={scopeInput}
              onChange={(e) => setScopeInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddScope()}
              placeholder="Add scope..."
              disabled={!formData.enabled}
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            />
            <button
              onClick={handleAddScope}
              disabled={!formData.enabled || !scopeInput.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.scopes?.map((scope) => (
              <span
                key={scope}
                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-md"
              >
                {scope}
                <button
                  onClick={() => handleRemoveScope(scope)}
                  disabled={!formData.enabled}
                  className="hover:text-purple-900 dark:hover:text-purple-100"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* User Provisioning */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Users className="inline h-4 w-4 mr-1" />
              Auto-create Users
            </label>
            <button
              onClick={() =>
                handleInputChange(
                  'auto_create_users',
                  !formData.auto_create_users
                )
              }
              disabled={!formData.enabled}
              className={cn(
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
                formData.auto_create_users ? 'bg-purple-600' : 'bg-gray-200',
                !formData.enabled && 'cursor-not-allowed opacity-50'
              )}
            >
              <span
                className={cn(
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  formData.auto_create_users ? 'translate-x-5' : 'translate-x-0'
                )}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Role
            </label>
            <select
              value={formData.default_role}
              onChange={(e) =>
                handleInputChange('default_role', e.target.value)
              }
              disabled={!formData.enabled || !formData.auto_create_users}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 dark:disabled:bg-gray-700 disabled:cursor-not-allowed"
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={
            !hasChanges || updateMutation.isPending || !formData.enabled
          }
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors',
            hasChanges && formData.enabled
              ? 'bg-purple-600 text-white hover:bg-purple-700'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          )}
        >
          {updateMutation.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save Changes
        </button>

        <button
          onClick={handleTestConnection}
          disabled={
            !formData.discovery_endpoint ||
            !formData.enabled ||
            testConnectionMutation.isPending
          }
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium border rounded-md transition-colors',
            formData.discovery_endpoint && formData.enabled
              ? 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 border-gray-300 dark:border-gray-600'
              : 'text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-900 cursor-not-allowed border-gray-200 dark:border-gray-700'
          )}
        >
          {testConnectionMutation.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <TestTube className="h-4 w-4" />
          )}
          Test Connection
        </button>
      </div>

      {/* Information Panel */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-1">About OIDC Authentication</p>
            <p className="mb-2">
              OpenID Connect enables Single Sign-On (SSO) through external
              identity providers like Authelia, Keycloak, Auth0, or Okta. Users
              can authenticate using their enterprise credentials while API keys
              remain available for programmatic access.
            </p>
            <p className="font-medium mt-2">Configuration Notes:</p>
            <ul className="list-disc list-inside mt-1">
              <li>
                The redirect URI must be registered with your OIDC provider
              </li>
              <li>Client secrets are encrypted before storage</li>
              <li>
                Standard scopes: openid (required), email, profile, groups
              </li>
              <li>Auto-provisioning creates users on first successful login</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
