import { useState, useCallback, useEffect } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';

interface UseConversationSearchOptions {
  onNavigateToMessage?: (messageId: string) => void;
  containerRef?: React.RefObject<HTMLDivElement>;
}

export function useConversationSearch({
  onNavigateToMessage,
  containerRef,
}: UseConversationSearchOptions = {}) {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [highlightedMessageId, setHighlightedMessageId] = useState<
    string | null
  >(null);

  // Open search with Ctrl/Cmd + F
  useHotkeys(
    'ctrl+f, cmd+f',
    (e) => {
      e.preventDefault();
      setIsSearchOpen(true);
    },
    {
      enableOnFormTags: false,
    }
  );

  // Close search with Escape
  useHotkeys(
    'escape',
    () => {
      if (isSearchOpen) {
        setIsSearchOpen(false);
        setHighlightedMessageId(null);
      }
    },
    {
      enabled: isSearchOpen,
      enableOnFormTags: true,
    }
  );

  const navigateToMessage = useCallback(
    (messageId: string) => {
      setHighlightedMessageId(messageId);

      // Scroll to message if containerRef is provided
      if (containerRef?.current) {
        const messageElement = containerRef.current.querySelector(
          `[data-message-id="${messageId}"]`
        );

        if (messageElement) {
          messageElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
          });

          // Add highlight animation
          messageElement.classList.add('search-highlight');
          setTimeout(() => {
            messageElement.classList.remove('search-highlight');
          }, 2000);
        }
      }

      onNavigateToMessage?.(messageId);
    },
    [containerRef, onNavigateToMessage]
  );

  const openSearch = useCallback(() => {
    setIsSearchOpen(true);
  }, []);

  const closeSearch = useCallback(() => {
    setIsSearchOpen(false);
    setHighlightedMessageId(null);
  }, []);

  // Add CSS for highlight animation
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .search-highlight {
        animation: highlight-pulse 2s ease-out;
      }

      @keyframes highlight-pulse {
        0% {
          background-color: rgba(250, 204, 21, 0.3);
          box-shadow: 0 0 0 0 rgba(250, 204, 21, 0.4);
        }
        50% {
          background-color: rgba(250, 204, 21, 0.2);
          box-shadow: 0 0 0 10px rgba(250, 204, 21, 0);
        }
        100% {
          background-color: transparent;
          box-shadow: 0 0 0 10px rgba(250, 204, 21, 0);
        }
      }

      .dark .search-highlight {
        animation: highlight-pulse-dark 2s ease-out;
      }

      @keyframes highlight-pulse-dark {
        0% {
          background-color: rgba(250, 204, 21, 0.4);
          box-shadow: 0 0 0 0 rgba(250, 204, 21, 0.3);
        }
        50% {
          background-color: rgba(250, 204, 21, 0.3);
          box-shadow: 0 0 0 10px rgba(250, 204, 21, 0);
        }
        100% {
          background-color: transparent;
          box-shadow: 0 0 0 10px rgba(250, 204, 21, 0);
        }
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return {
    isSearchOpen,
    highlightedMessageId,
    openSearch,
    closeSearch,
    navigateToMessage,
  };
}
