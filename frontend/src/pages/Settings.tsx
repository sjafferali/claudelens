import { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Lock,
  Database,
  Zap,
  FolderOpen,
  Save,
} from 'lucide-react';
import { AISettingsPanel } from '@/components/settings/AISettingsPanel';
import AccountSettings from '@/components/settings/AccountSettings';

const SETTINGS_TABS = [
  { id: 'ai', label: 'AI Assistant', icon: Zap },
  { id: 'account', label: 'Account', icon: User },
  { id: 'privacy', label: 'Privacy', icon: Lock },
  { id: 'data', label: 'Data', icon: Database },
] as const;

type SettingsTab = (typeof SETTINGS_TABS)[number]['id'];

export default function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('ai');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'ai':
        return <AISettingsPanel />;
      case 'account':
        return <AccountSettings />;
      case 'privacy':
        return <PrivacySettings />;
      case 'data':
        return <DataSettings />;
      default:
        return <AISettingsPanel />;
    }
  };

  return (
    <div className="flex h-full bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-6">
            <SettingsIcon className="h-6 w-6 text-gray-600 dark:text-gray-400" />
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Settings
            </h1>
          </div>

          <nav className="space-y-1">
            {SETTINGS_TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-left rounded-md transition-colors ${
                    activeTab === tab.id
                      ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 border-l-2 border-purple-500'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-sm font-medium">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto">
          <div className="p-8">{renderTabContent()}</div>
        </div>
      </div>
    </div>
  );
}

// Placeholder components for other settings tabs
function PrivacySettings() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
        <Lock className="h-5 w-5 text-gray-500 dark:text-gray-400" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Privacy Settings
        </h2>
      </div>
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          Privacy settings coming soon...
        </p>
      </div>
    </div>
  );
}

function DataSettings() {
  const [backupDirectory, setBackupDirectory] = useState('/backups');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  const handleSaveBackupDirectory = async () => {
    setIsSaving(true);
    setSaveMessage('');

    try {
      // For now, we'll store this in localStorage
      // In production, this would be saved to the backend
      localStorage.setItem('backupDirectory', backupDirectory);
      setSaveMessage('Backup directory saved successfully');

      // Clear success message after 3 seconds
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      setSaveMessage('Failed to save backup directory');
    } finally {
      setIsSaving(false);
    }
  };

  // Load saved backup directory on component mount
  useEffect(() => {
    const savedDirectory = localStorage.getItem('backupDirectory');
    if (savedDirectory) {
      setBackupDirectory(savedDirectory);
    }
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
        <Database className="h-5 w-5 text-gray-500 dark:text-gray-400" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Data Settings
        </h2>
      </div>

      {/* Backup Directory Setting */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-start gap-3 mb-4">
          <FolderOpen className="h-5 w-5 text-gray-500 dark:text-gray-400 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
              Backup Directory
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Configure the directory where backups will be stored. The
              directory will be created automatically if it doesn't exist.
            </p>

            <div className="flex gap-3">
              <input
                type="text"
                value={backupDirectory}
                onChange={(e) => setBackupDirectory(e.target.value)}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="/backups"
              />
              <button
                onClick={handleSaveBackupDirectory}
                disabled={isSaving}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium transition-colors"
              >
                {isSaving ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save
                  </>
                )}
              </button>
            </div>

            {saveMessage && (
              <p
                className={`mt-2 text-sm ${
                  saveMessage.includes('success')
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {saveMessage}
              </p>
            )}

            <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-md">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                <strong>Note:</strong> Ensure the application has write
                permissions to this directory. The default directory is{' '}
                <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs">
                  /backups
                </code>
                .
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Other Data Settings (placeholder for future) */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
        <p className="text-gray-500 dark:text-gray-400 text-center">
          Additional data management settings will be available here in future
          updates.
        </p>
      </div>
    </div>
  );
}
