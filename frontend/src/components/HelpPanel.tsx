import React, { useState } from 'react';
import {
  X,
  HelpCircle,
  ChevronRight,
  Search,
  Keyboard,
  Info,
} from 'lucide-react';

interface HelpSection {
  id: string;
  title: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

interface HelpPanelProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

const HelpPanel: React.FC<HelpPanelProps> = ({
  isOpen,
  onClose,
  className = '',
}) => {
  const [activeSection, setActiveSection] = useState<string>('getting-started');
  const [searchQuery, setSearchQuery] = useState('');

  const helpSections: HelpSection[] = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      icon: <Info className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Welcome to ClaudeLens
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            ClaudeLens helps you visualize and navigate your Claude AI
            conversations with powerful features:
          </p>
          <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-1">•</span>
              <span>
                View conversation history in multiple formats (Timeline,
                Compact, Tree)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-1">•</span>
              <span>Navigate between alternative responses and branches</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-1">•</span>
              <span>Visualize tool operations and sidechains separately</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-500 mt-1">•</span>
              <span>Search across all conversations with regex support</span>
            </li>
          </ul>
        </div>
      ),
    },
    {
      id: 'navigation',
      title: 'Navigation Features',
      icon: <ChevronRight className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Navigating Conversations
          </h3>

          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Branch Navigation
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                When Claude provides multiple responses to the same prompt, use
                the branch selector to navigate between alternatives.
              </p>
              <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded-md">
                <code className="text-xs">Alt+← / Alt+→</code> - Navigate
                between branches
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Parent/Child Navigation
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Jump to parent or child messages to follow the conversation
                flow.
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Mini-Map
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Use the mini-map for a bird's eye view of the conversation
                structure. Click anywhere on the map to jump to that section.
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Tree View
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Switch to tree view to see the entire conversation structure as
                an interactive node graph. Zoom, pan, and click nodes to
                navigate.
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'view-modes',
      title: 'View Modes',
      icon: <Search className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Different Ways to View Conversations
          </h3>

          <div className="space-y-3">
            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-md">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">
                Timeline View
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Default chronological view with full message content, rich
                formatting, and tool operation details.
              </p>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-md">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">
                Compact View
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Condensed layout with less spacing, ideal for quickly scanning
                through long conversations.
              </p>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-md">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">
                Raw View
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Plain text format without any formatting or styling, useful for
                copying content.
              </p>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-md">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">
                Tree View
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Interactive node-based visualization showing conversation
                structure, branches, and relationships.
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'sidechains',
      title: 'Sidechains & Tools',
      icon: <ChevronRight className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Understanding Sidechains
          </h3>

          <p className="text-sm text-slate-600 dark:text-slate-400">
            Sidechains are auxiliary operations that Claude performs, such as:
          </p>

          <ul className="space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-purple-500 mt-1.5"></span>
              <div>
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  Tool Operations
                </span>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  File reading/writing, web searches, code execution
                </p>
              </div>
            </li>
            <li className="flex items-start gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-purple-500 mt-1.5"></span>
              <div>
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  System Operations
                </span>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Background tasks that don't directly appear in the main
                  conversation
                </p>
              </div>
            </li>
          </ul>

          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-md">
            <p className="text-xs text-purple-700 dark:text-purple-300">
              Toggle the Sidechains panel to view these operations separately
              from the main conversation flow.
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 'keyboard-shortcuts',
      title: 'Keyboard Shortcuts',
      icon: <Keyboard className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Keyboard Shortcuts
          </h3>

          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                <kbd className="font-mono bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded">
                  Alt+←
                </kbd>
              </div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                Previous branch
              </div>

              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                <kbd className="font-mono bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded">
                  Alt+→
                </kbd>
              </div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                Next branch
              </div>

              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                <kbd className="font-mono bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded">
                  Cmd/Ctrl+Shift+L
                </kbd>
              </div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                Copy message link
              </div>

              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                <kbd className="font-mono bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded">
                  Cmd/Ctrl+K
                </kbd>
              </div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                Quick search
              </div>

              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                <kbd className="font-mono bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded">
                  Esc
                </kbd>
              </div>
              <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded">
                Close dialogs/panels
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'search',
      title: 'Search Features',
      icon: <Search className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Powerful Search Capabilities
          </h3>

          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Text Search
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Search for exact text matches across all conversations.
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Regex Search
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Use regular expressions for complex pattern matching.
              </p>
              <div className="mt-2 p-2 bg-slate-50 dark:bg-slate-800 rounded">
                <code className="text-xs font-mono">error.*failed</code> - Find
                error messages
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Search History
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Your recent searches are saved for quick access.
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">
                Pattern Helper
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Use the pattern helper for common regex patterns and quick
                reference.
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'tips',
      title: 'Tips & Tricks',
      icon: <Info className="w-4 h-4" />,
      content: (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
            Pro Tips
          </h3>

          <ul className="space-y-3 text-sm">
            <li className="flex items-start gap-2">
              <span className="text-emerald-500">💡</span>
              <div>
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  Share specific messages
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Click the share icon next to any message to copy a direct link
                  to it.
                </p>
              </div>
            </li>

            <li className="flex items-start gap-2">
              <span className="text-emerald-500">💡</span>
              <div>
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  Debug mode
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Click the bug icon to view the complete JSON data for any
                  message.
                </p>
              </div>
            </li>

            <li className="flex items-start gap-2">
              <span className="text-emerald-500">💡</span>
              <div>
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  Message position
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Each message shows its position (#X of Y) for easy reference.
                </p>
              </div>
            </li>

            <li className="flex items-start gap-2">
              <span className="text-emerald-500">💡</span>
              <div>
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  Load more efficiently
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Messages are loaded in batches. Click "Load More" to see older
                  messages.
                </p>
              </div>
            </li>

            <li className="flex items-start gap-2">
              <span className="text-emerald-500">💡</span>
              <div>
                <p className="font-medium text-slate-700 dark:text-slate-200">
                  Tree view legend
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  In tree view, the legend shows what each color and symbol
                  means.
                </p>
              </div>
            </li>
          </ul>
        </div>
      ),
    },
  ];

  const filteredSections = helpSections.filter(
    (section) =>
      section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (typeof section.content === 'object' &&
        JSON.stringify(section.content)
          .toLowerCase()
          .includes(searchQuery.toLowerCase()))
  );

  const currentSection =
    filteredSections.find((s) => s.id === activeSection) || filteredSections[0];

  if (!isOpen) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 ${className}`}
    >
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-slate-50 dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col">
          <div className="p-4 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                <HelpCircle className="w-5 h-5" />
                Help & Documentation
              </h2>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search help..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-sm bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Section List */}
          <div className="flex-1 overflow-y-auto p-2">
            {filteredSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`
                  w-full text-left px-3 py-2 rounded-md mb-1 transition-colors
                  flex items-center gap-2
                  ${
                    activeSection === section.id
                      ? 'bg-blue-500 text-white'
                      : 'hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                  }
                `}
              >
                {section.icon}
                <span className="text-sm">{section.title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-200">
              {currentSection?.title}
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {currentSection?.content}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpPanel;
