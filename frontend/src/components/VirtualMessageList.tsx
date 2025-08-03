import { useRef, useEffect, useCallback, useState, memo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Message } from '@/api/types';
import MessageItem from './MessageItem';
import MessageSkeleton from './MessageSkeleton';
import { useInView } from 'react-intersection-observer';
import { Loader2 } from 'lucide-react';

interface VirtualMessageListProps {
  messages: Message[];
  isLoading?: boolean;
  hasNextPage?: boolean;
  hasPreviousPage?: boolean;
  isFetchingNextPage?: boolean;
  isFetchingPreviousPage?: boolean;
  onLoadMore?: (direction: 'next' | 'previous') => void;
  estimatedMessageHeight?: number;
}

const VirtualMessageList = memo(function VirtualMessageList({
  messages,
  isLoading,
  hasNextPage,
  hasPreviousPage,
  isFetchingNextPage,
  isFetchingPreviousPage,
  onLoadMore,
  estimatedMessageHeight = 200,
}: VirtualMessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const scrollPositionRef = useRef<number>(0);
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Intersection observers for infinite scroll
  const { ref: topRef } = useInView({
    threshold: 0,
    onChange: (inView) => {
      if (inView && hasPreviousPage && !isFetchingPreviousPage && onLoadMore) {
        onLoadMore('previous');
      }
    },
  });

  const { ref: bottomRef } = useInView({
    threshold: 0,
    onChange: (inView) => {
      if (inView && hasNextPage && !isFetchingNextPage && onLoadMore) {
        onLoadMore('next');
      }
    },
  });

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: useCallback(
      () => estimatedMessageHeight,
      [estimatedMessageHeight]
    ),
    overscan: 5,
    measureElement: (element) => {
      if (element) {
        const height = element.getBoundingClientRect().height;
        return height;
      }
      return estimatedMessageHeight;
    },
  });

  const items = virtualizer.getVirtualItems();

  // Save scroll position before re-render
  useEffect(() => {
    const scrollElement = parentRef.current;
    if (!scrollElement) return;

    const handleScroll = () => {
      scrollPositionRef.current = scrollElement.scrollTop;
    };

    scrollElement.addEventListener('scroll', handleScroll);
    return () => scrollElement.removeEventListener('scroll', handleScroll);
  }, []);

  // Restore scroll position after loading previous messages
  useEffect(() => {
    if (isFetchingPreviousPage === false && scrollPositionRef.current > 0) {
      const scrollElement = parentRef.current;
      if (scrollElement) {
        // Calculate the height difference and adjust scroll
        const currentHeight = scrollElement.scrollHeight;
        requestAnimationFrame(() => {
          const newHeight = scrollElement.scrollHeight;
          const heightDiff = newHeight - currentHeight;
          if (heightDiff > 0) {
            scrollElement.scrollTop = scrollPositionRef.current + heightDiff;
          }
        });
      }
    }
  }, [isFetchingPreviousPage]);

  const toggleExpanded = useCallback((messageId: string) => {
    setExpandedMessages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  }, []);

  const handleCopy = useCallback((text: string, messageId: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    });
  }, []);

  if (isLoading) {
    return <MessageSkeleton count={5} />;
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
          No messages yet
        </h3>
        <p className="text-slate-600 dark:text-slate-400 text-center max-w-sm">
          This conversation session doesn't contain any messages yet.
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-full">
      <div
        ref={parentRef}
        className="h-full overflow-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600"
        style={{
          contain: 'strict',
        }}
      >
        {/* Load previous messages trigger */}
        {hasPreviousPage && (
          <div ref={topRef} className="py-4 text-center">
            {isFetchingPreviousPage ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">
                  Loading earlier messages...
                </span>
              </div>
            ) : (
              <button
                onClick={() => onLoadMore?.('previous')}
                className="text-sm text-primary hover:underline"
              >
                Load earlier messages
              </button>
            )}
          </div>
        )}

        {/* Virtual list container */}
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {items.map((virtualItem) => {
            const message = messages[virtualItem.index];
            const isExpanded = expandedMessages.has(message._id);
            const isFirstMessage = virtualItem.index === 0;
            const previousMessage =
              virtualItem.index > 0 ? messages[virtualItem.index - 1] : null;
            const isDifferentSender = previousMessage?.type !== message.type;

            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                <MessageItem
                  message={message}
                  isExpanded={isExpanded}
                  isFirstMessage={isFirstMessage}
                  isDifferentSender={isDifferentSender}
                  copiedId={copiedId}
                  onToggleExpanded={toggleExpanded}
                  onCopy={handleCopy}
                />
              </div>
            );
          })}
        </div>

        {/* Load more messages trigger */}
        {hasNextPage && (
          <div ref={bottomRef} className="py-4 text-center">
            {isFetchingNextPage ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">
                  Loading more messages...
                </span>
              </div>
            ) : (
              <button
                onClick={() => onLoadMore?.('next')}
                className="text-sm text-primary hover:underline"
              >
                Load more messages
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export default VirtualMessageList;
