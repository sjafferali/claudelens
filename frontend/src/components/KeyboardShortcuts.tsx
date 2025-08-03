import { useEffect, useState } from 'react';
import { X, Keyboard } from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook';
import { cn } from '@/utils/cn';

interface KeyboardShortcutsProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const shortcuts = [
  {
    category: 'Navigation',
    items: [
      { keys: ['J'], description: 'Navigate to previous message' },
      { keys: ['K'], description: 'Navigate to next message' },
      { keys: ['G', 'G'], description: 'Go to top' },
      { keys: ['Shift', 'G'], description: 'Go to bottom' },
      { keys: ['Space'], description: 'Page down' },
      { keys: ['Shift', 'Space'], description: 'Page up' },
    ],
  },
  {
    category: 'Search',
    items: [
      { keys: ['Ctrl/Cmd', 'F'], description: 'Open search' },
      { keys: ['Enter'], description: 'Next search result' },
      { keys: ['Shift', 'Enter'], description: 'Previous search result' },
      { keys: ['Esc'], description: 'Close search' },
    ],
  },
  {
    category: 'General',
    items: [
      { keys: ['?'], description: 'Show keyboard shortcuts' },
      { keys: ['Esc'], description: 'Close dialogs' },
    ],
  },
];

export default function KeyboardShortcuts({
  isOpen: controlledIsOpen,
  onClose: controlledOnClose,
}: KeyboardShortcutsProps) {
  const [internalIsOpen, setInternalIsOpen] = useState(false);

  const isOpen =
    controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const handleClose = controlledOnClose || (() => setInternalIsOpen(false));

  // Toggle shortcuts dialog with "?"
  useHotkeys(
    '?',
    () => {
      if (controlledIsOpen === undefined) {
        setInternalIsOpen((prev) => !prev);
      }
    },
    {
      enableOnFormTags: false,
    }
  );

  // Close with Escape
  useHotkeys(
    'escape',
    () => {
      if (isOpen) {
        handleClose();
      }
    },
    {
      enabled: isOpen,
    }
  );

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Dialog */}
      <div className="relative bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Keyboard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
          <div className="space-y-6">
            {shortcuts.map((category) => (
              <div key={category.category}>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  {category.category}
                </h3>
                <div className="space-y-2">
                  {category.items.map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors"
                    >
                      <span className="text-sm text-gray-600 dark:text-gray-300">
                        {shortcut.description}
                      </span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <span
                            key={keyIndex}
                            className="flex items-center gap-1"
                          >
                            <kbd
                              className={cn(
                                'px-2 py-1 text-xs font-medium',
                                'bg-gray-100 dark:bg-slate-700',
                                'text-gray-700 dark:text-gray-300',
                                'border border-gray-300 dark:border-slate-600',
                                'rounded shadow-sm'
                              )}
                            >
                              {key}
                            </kbd>
                            {keyIndex < shortcut.keys.length - 1 && (
                              <span className="text-gray-400 dark:text-gray-500">
                                +
                              </span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Footer note */}
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              Press{' '}
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-slate-700 rounded text-xs">
                ?
              </kbd>{' '}
              at any time to show this help
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
