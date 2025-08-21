import { useState } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Lock,
  Database,
  Zap,
} from 'lucide-react';
import { AISettingsPanel } from '@/components/settings/AISettingsPanel';

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
function AccountSettings() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
        <User className="h-5 w-5 text-gray-500 dark:text-gray-400" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Account Settings
        </h2>
      </div>
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          Account settings coming soon...
        </p>
      </div>
    </div>
  );
}

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
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
        <Database className="h-5 w-5 text-gray-500 dark:text-gray-400" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Data Settings
        </h2>
      </div>
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          Data settings coming soon...
        </p>
      </div>
    </div>
  );
}
