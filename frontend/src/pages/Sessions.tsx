import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useSessions } from '@/hooks/useSessions';
import { formatDistanceToNow } from 'date-fns';
import SearchBar from '@/components/SearchBar';
import SessionFilters from '@/components/SessionFilters';
import ActiveFilters from '@/components/ActiveFilters';
import { useSessionFilters } from '@/hooks/useSessionFilters';
import SessionDetail from './SessionDetail';

export default function Sessions() {
  const { sessionId } = useParams();

  if (sessionId) {
    return <SessionDetail />;
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
      <div className="flex flex-col h-screen bg-layer-primary">
        <div className="bg-layer-secondary border-b border-primary-c px-6 py-4">
          <h2 className="text-2xl font-semibold text-primary-c">Sessions</h2>
          <p className="text-tertiary-c mt-1">
            Browse all your Claude conversation sessions
          </p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="bg-layer-secondary border border-primary-c rounded-lg p-12 text-center">
            <p className="text-tertiary-c">Failed to load sessions</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-layer-primary">
      {/* Header */}
      <div className="bg-layer-secondary border-b border-primary-c px-6 py-4">
        <h2 className="text-2xl font-semibold text-primary-c">Sessions</h2>
        <p className="text-tertiary-c mt-1">
          Browse all your Claude conversation sessions
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
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

          <div className="bg-layer-secondary border border-primary-c rounded-lg">
            <div className="px-6 py-4 border-b border-primary-c">
              <h3 className="text-lg font-medium text-primary-c">
                {hasActiveFilters ? 'Filtered Sessions' : 'Recent Sessions'}
              </h3>
              {data && (
                <p className="text-sm text-tertiary-c mt-1">
                  Showing{' '}
                  {data.items.length > 0 ? currentPage * pageSize + 1 : 0} -{' '}
                  {Math.min((currentPage + 1) * pageSize, data.total)} of{' '}
                  {data.total} sessions
                </p>
              )}
            </div>
            <div className="p-6">
              {isLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-4 bg-layer-tertiary border border-secondary-c rounded-lg animate-pulse"
                    >
                      <div className="space-y-2 flex-1">
                        <div className="h-4 w-3/4 bg-border rounded"></div>
                        <div className="h-3 w-1/2 bg-border rounded"></div>
                      </div>
                      <div className="h-4 w-16 bg-border rounded"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    {data?.items.length === 0 ? (
                      <div className="text-center py-12 space-y-4">
                        <p className="text-tertiary-c">
                          {hasActiveFilters
                            ? 'No sessions found matching your filters'
                            : 'No sessions found'}
                        </p>
                        {hasActiveFilters && (
                          <button
                            onClick={clearAllFilters}
                            className="text-sm text-primary hover:text-primary-hover"
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
                          className="flex items-center justify-between p-4 bg-layer-tertiary border border-secondary-c rounded-lg hover:border-primary-c hover:bg-layer-tertiary/80 cursor-pointer transition-all"
                        >
                          <div className="space-y-1 flex-1">
                            <p className="font-medium text-primary-c">
                              {session.summary ||
                                `Session ${session.sessionId.slice(0, 8)}...`}
                            </p>
                            <p className="text-sm text-tertiary-c">
                              {session.messageCount} messages •{' '}
                              {formatDistanceToNow(
                                new Date(session.startedAt),
                                {
                                  addSuffix: true,
                                }
                              )}
                            </p>
                          </div>
                          <div className="text-sm text-muted-c">
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
                      <p className="text-sm text-tertiary-c">
                        Page {currentPage + 1} of{' '}
                        {Math.ceil(data.total / pageSize)}
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handlePageChange(currentPage - 1)}
                          disabled={currentPage === 0}
                          className="px-3 py-1.5 text-sm bg-layer-tertiary border border-primary-c rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-border hover:text-primary-c transition-all text-tertiary-c"
                        >
                          Previous
                        </button>
                        <button
                          onClick={() => handlePageChange(currentPage + 1)}
                          disabled={!data.has_more}
                          className="px-3 py-1.5 text-sm bg-layer-tertiary border border-primary-c rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-border hover:text-primary-c transition-all text-tertiary-c"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
