import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
import { useSessions, useSession } from '@/hooks/useSessions';
import { formatDistanceToNow } from 'date-fns';
import { Loader2 } from 'lucide-react';
import VirtualMessageList from '@/components/VirtualMessageList';
import MessageNavigator from '@/components/MessageNavigator';
import ConversationSearch from '@/components/ConversationSearch';
import KeyboardShortcuts from '@/components/KeyboardShortcuts';
import SearchBar from '@/components/SearchBar';
import SessionFilters from '@/components/SessionFilters';
import ActiveFilters from '@/components/ActiveFilters';
import { useSessionFilters } from '@/hooks/useSessionFilters';
import { useMessagePagination } from '@/hooks/useMessagePagination';
import { useConversationSearch } from '@/hooks/useConversationSearch';
import { useHotkeys } from 'react-hotkeys-hook';

export default function Sessions() {
  const { sessionId } = useParams();

  if (sessionId) {
    return <SessionDetail sessionId={sessionId} />;
  }

  return <SessionsList />;
}

function SessionsList() {
  const navigate = useNavigate();
  const {
    filters,
    updateFilters,
    removeFilter,
    clearAllFilters,
    hasActiveFilters,
  } = useSessionFilters();
  const [pageSize] = useState(20);

  // Calculate current page from skip/limit or default to 0
  const currentPage = filters.skip ? Math.floor(filters.skip / pageSize) : 0;

  // Use filters from URL with defaults
  const { data, isLoading, error } = useSessions({
    projectId: filters.projectId,
    search: filters.search,
    startDate: filters.startDate,
    endDate: filters.endDate,
    sortBy: filters.sortBy || 'started_at',
    sortOrder: filters.sortOrder || 'desc',
    skip: currentPage * pageSize,
    limit: pageSize,
  });

  // Handle search changes
  const handleSearchChange = useCallback(
    (search: string) => {
      updateFilters({ search });
    },
    [updateFilters]
  );

  // Handle filter changes
  const handleFilterChange = useCallback(
    (newFilters: Partial<typeof filters>) => {
      updateFilters(newFilters);
    },
    [updateFilters]
  );

  // Handle pagination
  const handlePageChange = useCallback(
    (newPage: number) => {
      updateFilters({ skip: newPage * pageSize });
    },
    [pageSize, updateFilters]
  );

  // Auto-focus search on "/" key press
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (
        e.key === '/' &&
        !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)
      ) {
        e.preventDefault();
        document.querySelector<HTMLInputElement>('input[type="text"]')?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
          <p className="text-muted-foreground">
            Browse all your Claude conversation sessions
          </p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Failed to load sessions</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
        <p className="text-muted-foreground">
          Browse all your Claude conversation sessions
        </p>
      </div>

      <div className="space-y-4">
        <SearchBar
          value={filters.search || ''}
          onChange={handleSearchChange}
          placeholder="Search sessions..."
          className="w-full"
        />

        <SessionFilters
          filters={filters}
          onChange={handleFilterChange}
          hideProjectFilter={!!filters.projectId}
        />

        {hasActiveFilters && (
          <ActiveFilters
            filters={filters}
            onRemoveFilter={removeFilter}
            onClearAll={clearAllFilters}
          />
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {hasActiveFilters ? 'Filtered Sessions' : 'Recent Sessions'}
          </CardTitle>
          <CardDescription>
            {data && (
              <span>
                Showing {data.items.length > 0 ? currentPage * pageSize + 1 : 0}{' '}
                - {Math.min((currentPage + 1) * pageSize, data.total)} of{' '}
                {data.total} sessions
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-4 border rounded-lg animate-pulse"
                >
                  <div className="space-y-2 flex-1">
                    <div className="h-4 w-3/4 bg-muted rounded"></div>
                    <div className="h-3 w-1/2 bg-muted rounded"></div>
                  </div>
                  <div className="h-4 w-16 bg-muted rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {data?.items.length === 0 ? (
                  <div className="text-center py-12 space-y-4">
                    <p className="text-muted-foreground">
                      {hasActiveFilters
                        ? 'No sessions found matching your filters'
                        : 'No sessions found'}
                    </p>
                    {hasActiveFilters && (
                      <button
                        onClick={clearAllFilters}
                        className="text-sm text-primary hover:underline"
                      >
                        Clear all filters
                      </button>
                    )}
                  </div>
                ) : (
                  data?.items.map((session) => (
                    <div
                      key={session._id}
                      onClick={() => navigate(`/sessions/${session._id}`)}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    >
                      <div className="space-y-1 flex-1">
                        <p className="font-medium">
                          {session.summary ||
                            `Session ${session.sessionId.slice(0, 8)}...`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {session.messageCount} messages •
                          {formatDistanceToNow(new Date(session.startedAt), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {session.totalCost
                          ? `$${session.totalCost.toFixed(2)}`
                          : 'N/A'}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {data && data.items.length > 0 && (
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-muted-foreground">
                    Page {currentPage + 1} of {Math.ceil(data.total / pageSize)}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 0}
                      className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent transition-colors"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={!data.has_more}
                      className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SessionDetail({ sessionId }: { sessionId: string }) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const { data: session, isLoading: sessionLoading } = useSession(sessionId);
  const {
    messages,
    totalMessages,
    loadedRange,
    isLoading: messagesLoading,
    hasNextPage,
    hasPreviousPage,
    isFetchingNextPage,
    isFetchingPreviousPage,
    loadMore,
  } = useMessagePagination({ sessionId });

  const { isSearchOpen, openSearch, closeSearch, navigateToMessage } =
    useConversationSearch({ containerRef });

  // Keyboard navigation
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  // Navigate with J/K keys
  useHotkeys(
    'j',
    () => {
      if (currentMessageIndex > 0) {
        setCurrentMessageIndex((prev) => prev - 1);
        navigateToMessage(messages[currentMessageIndex - 1]._id);
      }
    },
    { enableOnFormTags: false }
  );

  useHotkeys(
    'k',
    () => {
      if (currentMessageIndex < messages.length - 1) {
        setCurrentMessageIndex((prev) => prev + 1);
        navigateToMessage(messages[currentMessageIndex + 1]._id);
      }
    },
    { enableOnFormTags: false }
  );

  // Go to top with G G
  useHotkeys(
    'g g',
    () => {
      containerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
    },
    { enableOnFormTags: false }
  );

  // Go to bottom with Shift+G
  useHotkeys(
    'shift+g',
    () => {
      containerRef.current?.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    },
    { enableOnFormTags: false }
  );

  // Page navigation
  useHotkeys(
    'space',
    (e) => {
      e.preventDefault();
      containerRef.current?.scrollBy({
        top: window.innerHeight * 0.8,
        behavior: 'smooth',
      });
    },
    { enableOnFormTags: false }
  );

  useHotkeys(
    'shift+space',
    (e) => {
      e.preventDefault();
      containerRef.current?.scrollBy({
        top: -window.innerHeight * 0.8,
        behavior: 'smooth',
      });
    },
    { enableOnFormTags: false }
  );

  // Open search with /
  useHotkeys(
    '/',
    (e) => {
      e.preventDefault();
      openSearch();
    },
    { enableOnFormTags: false }
  );

  if (sessionLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Session Not Found
          </h2>
          <p className="text-muted-foreground">
            This session could not be found.
          </p>
        </div>
        <button
          onClick={() => navigate('/sessions')}
          className="text-sm text-primary hover:underline"
        >
          ← Back to sessions
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-muted-foreground hover:text-foreground mb-2 flex items-center gap-1"
          >
            ← Back to sessions
          </button>
          <h2 className="text-3xl font-bold tracking-tight">
            {session.summary || `Session ${session.sessionId.slice(0, 8)}...`}
          </h2>
          <p className="text-muted-foreground">
            {formatDistanceToNow(new Date(session.startedAt), {
              addSuffix: true,
            })}{' '}
            • {totalMessages || session.messageCount} messages •
            {session.totalCost
              ? ` $${session.totalCost.toFixed(2)}`
              : ' No cost data'}
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2 relative">
          <CardHeader>
            <CardTitle>Conversation</CardTitle>
            <CardDescription>
              {loadedRange.start > 0 || loadedRange.end < totalMessages ? (
                <span>
                  Showing messages {loadedRange.start}-{loadedRange.end} of{' '}
                  {totalMessages}
                </span>
              ) : (
                <span>All {messages.length} messages loaded</span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div
              ref={containerRef}
              className="h-[calc(100vh-300px)] overflow-hidden"
            >
              <VirtualMessageList
                messages={messages}
                isLoading={messagesLoading}
                hasNextPage={hasNextPage}
                hasPreviousPage={hasPreviousPage}
                isFetchingNextPage={isFetchingNextPage}
                isFetchingPreviousPage={isFetchingPreviousPage}
                onLoadMore={loadMore}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Session ID
              </p>
              <p className="text-sm font-mono">{session.sessionId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Started
              </p>
              <p className="text-sm">
                {new Date(session.startedAt).toLocaleString()}
              </p>
            </div>
            {session.endedAt && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Ended
                </p>
                <p className="text-sm">
                  {new Date(session.endedAt).toLocaleString()}
                </p>
              </div>
            )}
            {session.modelsUsed && session.modelsUsed.length > 0 && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Models Used
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {session.modelsUsed.map((model, i) => (
                    <span
                      key={i}
                      className="text-xs px-2 py-1 bg-secondary rounded-md"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Navigation Controls */}
      <MessageNavigator
        containerRef={containerRef}
        totalMessages={totalMessages}
        loadedRange={loadedRange}
      />

      {/* Search Interface */}
      <ConversationSearch
        messages={messages}
        isOpen={isSearchOpen}
        onClose={closeSearch}
        onNavigateToMessage={navigateToMessage}
      />

      {/* Keyboard Shortcuts Guide */}
      <KeyboardShortcuts />
    </div>
  );
}
