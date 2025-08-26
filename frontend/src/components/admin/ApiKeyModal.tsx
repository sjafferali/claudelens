import React, { useState } from 'react';
import { X, Key, Plus, Copy, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { adminApi } from '@/api/admin';
import { User } from '@/api/types';
import { Button } from '@/components/common/Button';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User;
  onApiKeyGenerated: () => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  user,
  onApiKeyGenerated,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [hasCopied, setHasCopied] = useState(false);
  const [keyToRevoke, setKeyToRevoke] = useState<string | null>(null);

  const handleGenerateKey = async () => {
    if (!keyName.trim()) {
      toast.error('Please enter a name for the API key');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await adminApi.generateApiKey(user.id, keyName);
      setGeneratedKey(response.api_key);
      setKeyName('');
      onApiKeyGenerated();
      toast.success('API key generated successfully');
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response
              ?.data?.detail || 'Failed to generate API key';
      toast.error(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyKey = async () => {
    if (!generatedKey) return;

    try {
      await navigator.clipboard.writeText(generatedKey);
      setHasCopied(true);
      toast.success('API key copied to clipboard');
      setTimeout(() => setHasCopied(false), 3000);
    } catch (error) {
      toast.error('Failed to copy API key');
    }
  };

  const handleRevokeKey = async (keyHash: string) => {
    try {
      await adminApi.revokeApiKey(user.id, keyHash);
      onApiKeyGenerated();
      toast.success('API key revoked successfully');
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : (error as { response?: { data?: { detail?: string } } })?.response
              ?.data?.detail || 'Failed to revoke API key';
      toast.error(errorMessage);
    }
    setKeyToRevoke(null);
  };

  const handleClose = () => {
    setGeneratedKey(null);
    setKeyName('');
    setHasCopied(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="relative w-full max-w-2xl rounded-lg bg-white dark:bg-gray-800 shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Key className="w-5 h-5" />
              API Keys for {user.username}
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Generated Key Display */}
            {generatedKey && (
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <p className="text-sm text-green-800 dark:text-green-200 mb-3">
                  New API key generated! Copy it now - it won't be shown again.
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={generatedKey}
                    readOnly
                    className="flex-1 px-3 py-2 text-sm font-mono border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                  />
                  <Button
                    onClick={handleCopyKey}
                    size="sm"
                    variant="outline"
                    className="flex items-center gap-1"
                  >
                    {hasCopied ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Generate New Key */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Generate New API Key
              </h3>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  placeholder="Enter key name (e.g., Production API)"
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <Button
                  onClick={handleGenerateKey}
                  disabled={isGenerating || !keyName.trim()}
                  className="flex items-center gap-2"
                >
                  {isGenerating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" />
                      Generate
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Existing Keys */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Existing API Keys ({user.api_key_count || 0})
              </h3>
              {user.api_key_count === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No API keys have been generated for this user yet.
                </p>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Note: For security reasons, only key metadata is shown. Keys
                    cannot be recovered.
                  </p>
                  {/* In production, this would show actual API keys from the user */}
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {user.api_key_count} active API key(s)
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <Button variant="outline" onClick={handleClose}>
              Close
            </Button>
          </div>
        </div>
      </div>

      {/* Revoke Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!keyToRevoke}
        onCancel={() => setKeyToRevoke(null)}
        onConfirm={() => keyToRevoke && handleRevokeKey(keyToRevoke)}
        title="Revoke API Key"
        message="Are you sure you want to revoke this API key? This action cannot be undone."
        variant="destructive"
      />
    </>
  );
};
