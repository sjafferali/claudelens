import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Message } from '@/api/types';
import Fuse from 'fuse.js';

interface ConversationSearchProps {
  messages: Message[];
  isOpen: boolean;
  onClose: () => void;
  onNavigateToMessage: (messageId: string) => void;
}

export default function ConversationSearch({
  messages,
  isOpen,
  onClose,
  onNavigateToMessage,
}: ConversationSearchProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const [matches, setMatches] = useState<
    Array<{ item: Message; positions: number[] }>
  >([]);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Initialize Fuse.js for fuzzy search
  const fuse = useRef(
    new Fuse(messages, {
      keys: ['content'],
      includeMatches: true,
      threshold: 0.3,
      ignoreLocation: true,
      findAllMatches: true,
    })
  );

  // Update Fuse instance when messages change
  useEffect(() => {
    fuse.current = new Fuse(messages, {
      keys: ['content'],
      includeMatches: true,
      threshold: 0.3,
      ignoreLocation: true,
      findAllMatches: true,
    });
  }, [messages]);

  // Focus input when search opens
  useEffect(() => {
    if (isOpen) {
      searchInputRef.current?.focus();
    }
  }, [isOpen]);

  // Perform search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setMatches([]);
      setCurrentMatchIndex(0);
      return;
    }

    const searchResults = fuse.current.search(searchQuery);
    const formattedMatches = searchResults.map((result) => ({
      item: result.item,
      positions:
        result.matches?.[0]?.indices?.map(
          (range: [number, number]) => range[0]
        ) || [],
    }));

    setMatches(formattedMatches);
    setCurrentMatchIndex(0);
  }, [searchQuery]);

  const navigateToMatch = useCallback(
    (index: number) => {
      if (matches.length === 0) return;

      const normalizedIndex =
        ((index % matches.length) + matches.length) % matches.length;
      setCurrentMatchIndex(normalizedIndex);
      onNavigateToMessage(matches[normalizedIndex].item._id);
    },
    [matches, onNavigateToMessage]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'Enter':
          if (e.shiftKey) {
            navigateToMatch(currentMatchIndex - 1);
          } else {
            navigateToMatch(currentMatchIndex + 1);
          }
          e.preventDefault();
          break;
        case 'Escape':
          onClose();
          break;
        case 'ArrowUp':
          navigateToMatch(currentMatchIndex - 1);
          e.preventDefault();
          break;
        case 'ArrowDown':
          navigateToMatch(currentMatchIndex + 1);
          e.preventDefault();
          break;
      }
    },
    [currentMatchIndex, navigateToMatch, onClose]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed top-2 sm:top-4 left-1/2 -translate-x-1/2 w-[calc(100%-1rem)] sm:w-full max-w-2xl z-50 px-2 sm:px-4">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-2xl border border-gray-200 dark:border-slate-600 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
        <div className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 border-b border-gray-200 dark:border-slate-700">
          <Search className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 dark:text-gray-500 flex-shrink-0" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search in conversation..."
            className={cn(
              'flex-1 bg-transparent outline-none',
              'text-gray-900 dark:text-gray-100',
              'placeholder-gray-400 dark:placeholder-gray-500'
            )}
          />
          {matches.length > 0 && (
            <div className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
              <span className="font-medium hidden sm:inline">
                {currentMatchIndex + 1} of {matches.length}
              </span>
              <span className="font-medium sm:hidden">
                {currentMatchIndex + 1}/{matches.length}
              </span>
              <div className="flex items-center gap-0.5 sm:gap-1">
                <button
                  onClick={() => navigateToMatch(currentMatchIndex - 1)}
                  className="p-0.5 sm:p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition-colors"
                  title="Previous match (↑)"
                >
                  <ChevronUp className="h-3 w-3 sm:h-4 sm:w-4" />
                </button>
                <button
                  onClick={() => navigateToMatch(currentMatchIndex + 1)}
                  className="p-0.5 sm:p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition-colors"
                  title="Next match (↓)"
                >
                  <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4" />
                </button>
              </div>
            </div>
          )}
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
            title="Close search (Esc)"
          >
            <X className="h-4 w-4 sm:h-5 sm:w-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {searchQuery && matches.length === 0 && (
          <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 bg-gray-50/50 dark:bg-slate-900/50">
            No matches found for "{searchQuery}"
          </div>
        )}

        {matches.length > 0 && (
          <>
            <div className="max-h-48 overflow-y-auto border-t border-gray-200 dark:border-slate-700">
              {matches.slice(0, 5).map((match, idx) => {
                const messagePreview = match.item.content
                  .substring(0, 150)
                  .trim();
                const isCurrentMatch = idx === currentMatchIndex % 5;
                return (
                  <div
                    key={match.item._id}
                    onClick={() => navigateToMatch(idx)}
                    className={cn(
                      'px-4 py-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors',
                      isCurrentMatch && 'bg-[#FFF4B3] dark:bg-[#FFF4B3]/20'
                    )}
                  >
                    <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      {match.item.type === 'user'
                        ? 'You'
                        : match.item.type === 'assistant'
                          ? 'Claude'
                          : match.item.type}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {messagePreview}...
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-900/50 border-t border-gray-200 dark:border-slate-700">
              Press{' '}
              <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-slate-700 rounded text-xs">
                Enter
              </kbd>{' '}
              for next,{' '}
              <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-slate-700 rounded text-xs">
                Shift+Enter
              </kbd>{' '}
              for previous
            </div>
          </>
        )}
      </div>
    </div>
  );
}
