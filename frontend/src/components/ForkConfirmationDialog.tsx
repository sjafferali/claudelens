import { useState } from 'react';
import { GitFork, X, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface ForkConfirmationDialogProps {
  isOpen: boolean;
  messagePreview: string;
  messageType: 'user' | 'assistant';
  onConfirm: (description?: string) => void;
  onCancel: () => void;
}

export function ForkConfirmationDialog({
  isOpen,
  messagePreview,
  messageType,
  onConfirm,
  onCancel,
}: ForkConfirmationDialogProps) {
  const [description, setDescription] = useState('');

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm(description || undefined);
    setDescription('');
  };

  const handleCancel = () => {
    onCancel();
    setDescription('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleCancel}
      />

      {/* Dialog */}
      <div className="relative bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-lg w-full mx-4 border border-slate-200 dark:border-slate-700">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
              <GitFork className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Fork Conversation
            </h2>
          </div>
          <button
            onClick={handleCancel}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5 text-slate-500 dark:text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4">
          {/* Info message */}
          <div className="flex gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-800 dark:text-amber-200">
              <p className="font-medium mb-1">
                This will create a new conversation branch
              </p>
              <p className="text-amber-700 dark:text-amber-300">
                A new session will be created with all messages up to and
                including the selected {messageType} message. You can continue
                the conversation in a different direction without affecting the
                original.
              </p>
            </div>
          </div>

          {/* Message preview */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Forking from {messageType === 'user' ? 'your' : "Claude's"}{' '}
              message:
            </label>
            <div
              className={cn(
                'p-3 rounded-lg border text-sm',
                messageType === 'user'
                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                  : 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'
              )}
            >
              <p className="text-slate-700 dark:text-slate-300 line-clamp-3">
                {messagePreview}
              </p>
            </div>
          </div>

          {/* Description input */}
          <div>
            <label
              htmlFor="fork-description"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
            >
              Fork description (optional)
            </label>
            <input
              id="fork-description"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., 'Trying a different approach'"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 dark:focus:ring-amber-400 focus:border-transparent"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 dark:bg-amber-500 dark:hover:bg-amber-600 rounded-lg transition-colors shadow-sm"
          >
            Create Fork
          </button>
        </div>
      </div>
    </div>
  );
}
