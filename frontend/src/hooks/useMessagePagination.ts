import { useState, useCallback, useMemo } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { sessionsApi } from '@/api/sessions';
import { Message } from '@/api/types';

interface UseMessagePaginationOptions {
  sessionId: string;
  initialLimit?: number;
}

interface MessagePage {
  messages: Message[];
  skip: number;
  limit: number;
  hasMore: boolean;
}

export function useMessagePagination({
  sessionId,
  initialLimit = 50,
}: UseMessagePaginationOptions) {
  const [searchQuery, setSearchQuery] = useState('');

  const {
    data,
    fetchNextPage,
    fetchPreviousPage,
    hasNextPage,
    hasPreviousPage,
    isFetchingNextPage,
    isFetchingPreviousPage,
    isLoading,
    isError,
    error,
    refetch,
  } = useInfiniteQuery<MessagePage, Error>({
    queryKey: ['session-messages-infinite', sessionId],
    queryFn: async ({ pageParam }) => {
      const skip = typeof pageParam === 'number' ? pageParam : 0;
      const response = await sessionsApi.getSessionMessages(
        sessionId,
        skip,
        initialLimit
      );

      // Transform the response to match our expected format
      return {
        messages: response.messages,
        skip: skip,
        limit: initialLimit,
        hasMore: response.messages.length === initialLimit,
      } as MessagePage;
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage: MessagePage) => {
      if (!lastPage.hasMore) return undefined;
      return lastPage.skip + lastPage.limit;
    },
    getPreviousPageParam: (firstPage: MessagePage) => {
      if (firstPage.skip === 0) return undefined;
      return Math.max(0, firstPage.skip - initialLimit);
    },
    enabled: !!sessionId,
    staleTime: 30000,
  });

  // Flatten all messages from all pages
  const allMessages = useMemo(() => {
    if (!data?.pages) return [];
    return data.pages.flatMap((page) => page.messages);
  }, [data]);

  // Total message count (estimated based on loaded messages)
  const totalMessages = useMemo(() => {
    if (!data?.pages || data.pages.length === 0) return 0;
    // If we have all messages, return the actual count
    const lastPage = data.pages[data.pages.length - 1];
    if (!lastPage.hasMore) {
      return allMessages.length;
    }
    // Otherwise, estimate based on current load
    return Math.max(allMessages.length, lastPage.skip + lastPage.limit + 50);
  }, [data, allMessages]);

  const loadedRange = useMemo(() => {
    if (!data?.pages || data.pages.length === 0) {
      return { start: 0, end: 0 };
    }
    const firstPage = data.pages[0];
    const lastPage = data.pages[data.pages.length - 1];
    return {
      start: firstPage.skip + 1,
      end: lastPage.skip + lastPage.messages.length,
    };
  }, [data]);

  const loadMore = useCallback(
    async (direction: 'next' | 'previous' = 'next') => {
      if (direction === 'next' && hasNextPage) {
        await fetchNextPage();
      } else if (direction === 'previous' && hasPreviousPage) {
        await fetchPreviousPage();
      }
    },
    [fetchNextPage, fetchPreviousPage, hasNextPage, hasPreviousPage]
  );

  const resetPagination = useCallback(() => {
    refetch();
  }, [refetch]);

  return {
    messages: allMessages,
    totalMessages,
    loadedRange,
    isLoading,
    isError,
    error,
    hasNextPage,
    hasPreviousPage,
    isFetchingNextPage,
    isFetchingPreviousPage,
    loadMore,
    resetPagination,
    searchQuery,
    setSearchQuery,
  };
}
