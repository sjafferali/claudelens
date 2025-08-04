import { useState, useEffect, useMemo } from 'react';
import {
  Search as SearchIcon,
  Loader2,
  Calendar,
  Bot,
  ChevronRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { debounce } from 'lodash';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
import { useProjects } from '@/hooks/useProjects';
import {
  useSearch,
  useSearchSuggestions,
  useRecentSearches,
} from '@/hooks/useSearch';
import { SearchFilters, SearchResult } from '@/api/search';
import { formatDistanceToNow } from 'date-fns';

export default function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});

  const { data: projects } = useProjects({ limit: 100 });
  const searchMutation = useSearch();
  const { data: suggestions } = useSearchSuggestions(
    debouncedQuery,
    showSuggestions
  );
  const { data: recentSearches } = useRecentSearches();

  // Debounce search query for suggestions
  const debouncedSetQuery = useMemo(
    () =>
      debounce((value: string) => {
        setDebouncedQuery(value);
      }, 300),
    []
  );

  useEffect(() => {
    debouncedSetQuery(query);
  }, [query, debouncedSetQuery]);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setShowSuggestions(false);
    searchMutation.mutate({
      query: query.trim(),
      filters,
      limit: 20,
      highlight: true,
    });
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    searchMutation.mutate({
      query: suggestion,
      filters,
      limit: 20,
      highlight: true,
    });
  };

  const handleResultClick = (result: SearchResult) => {
    // Navigate to the session detail page using MongoDB _id if available, otherwise sessionId
    const sessionIdForNav = result.session_mongo_id || result.session_id;
    // Include the message ID as a query parameter to scroll to it
    navigate(`/sessions/${sessionIdForNav}?messageId=${result.message_id}`);
  };

  const formatHighlights = (highlights: SearchResult['highlights']) => {
    if (!highlights || highlights.length === 0) return null;

    // Take the best highlight
    const bestHighlight = highlights.reduce((prev, current) =>
      current.score > prev.score ? current : prev
    );

    return (
      <div className="mt-2 text-sm text-muted-foreground">
        <span
          dangerouslySetInnerHTML={{
            __html: bestHighlight.snippet.replace(
              /<mark>/g,
              '<mark class="bg-yellow-200 dark:bg-yellow-800">'
            ),
          }}
        />
      </div>
    );
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <span className="text-blue-600">User</span>;
      case 'assistant':
        return <span className="text-green-600">Assistant</span>;
      default:
        return <span className="text-gray-600">{type}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Search</h2>
        <p className="text-muted-foreground">
          Search through all your Claude conversations
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Conversations</CardTitle>
          <CardDescription>
            Find messages, code snippets, or specific topics across all your
            sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="relative">
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setShowSuggestions(true);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    placeholder="Search for messages, code, or topics..."
                    className="pl-10 pr-4 py-2 w-full bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  />

                  {/* Suggestions dropdown */}
                  {showSuggestions &&
                    ((suggestions && suggestions.length > 0) ||
                      (recentSearches &&
                        recentSearches.length > 0 &&
                        !query)) && (
                      <div className="absolute top-full left-0 right-0 mt-1 bg-background border border-input rounded-md shadow-lg z-10 max-h-64 overflow-auto">
                        {!query &&
                          recentSearches &&
                          recentSearches.length > 0 && (
                            <>
                              <div className="px-3 py-2 text-xs font-semibold text-muted-foreground">
                                Recent Searches
                              </div>
                              {recentSearches.map((search, index) => (
                                <button
                                  key={index}
                                  type="button"
                                  onClick={() =>
                                    handleSuggestionClick(search.query)
                                  }
                                  className="w-full px-3 py-2 text-left hover:bg-accent hover:text-accent-foreground"
                                >
                                  <div className="flex items-center gap-2">
                                    <SearchIcon className="h-3 w-3" />
                                    {search.query}
                                  </div>
                                </button>
                              ))}
                            </>
                          )}

                        {query &&
                          suggestions?.map((suggestion, index) => (
                            <button
                              key={index}
                              type="button"
                              onClick={() =>
                                handleSuggestionClick(suggestion.text)
                              }
                              className="w-full px-3 py-2 text-left hover:bg-accent hover:text-accent-foreground"
                            >
                              <div className="flex items-center justify-between">
                                <span>{suggestion.text}</span>
                                <span className="text-xs text-muted-foreground">
                                  {suggestion.type}
                                </span>
                              </div>
                            </button>
                          ))}
                      </div>
                    )}
                </div>
                <Button
                  type="submit"
                  disabled={searchMutation.isPending || !query.trim()}
                >
                  {searchMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Search'
                  )}
                </Button>
              </div>

              {/* Click outside to close suggestions */}
              {showSuggestions && (
                <div
                  className="fixed inset-0 z-0"
                  onClick={() => setShowSuggestions(false)}
                />
              )}
            </div>

            <div className="flex gap-4 flex-wrap">
              <select
                className="px-3 py-2 bg-background border border-input rounded-md"
                value={filters.project_ids?.[0] || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    project_ids: e.target.value ? [e.target.value] : undefined,
                  })
                }
              >
                <option value="">All Projects</option>
                {projects?.items.map((project) => (
                  <option key={project._id} value={project._id}>
                    {project.name}
                  </option>
                ))}
              </select>

              <select
                className="px-3 py-2 bg-background border border-input rounded-md"
                onChange={(e) => {
                  const value = e.target.value;
                  if (!value) {
                    setFilters({ ...filters, start_date: undefined });
                    return;
                  }

                  const date = new Date();
                  switch (value) {
                    case 'today':
                      date.setHours(0, 0, 0, 0);
                      break;
                    case 'week':
                      date.setDate(date.getDate() - 7);
                      break;
                    case 'month':
                      date.setMonth(date.getMonth() - 1);
                      break;
                  }
                  setFilters({ ...filters, start_date: date.toISOString() });
                }}
              >
                <option value="">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
              </select>

              <select
                className="px-3 py-2 bg-background border border-input rounded-md"
                value={filters.models?.[0] || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    models: e.target.value ? [e.target.value] : undefined,
                  })
                }
              >
                <option value="">All Models</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                <option value="claude-3-haiku">Claude 3 Haiku</option>
              </select>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.has_code || false}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      has_code: e.target.checked || undefined,
                    })
                  }
                  className="rounded border-gray-300"
                />
                <span className="text-sm">Code only</span>
              </label>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Search Results
            {searchMutation.data && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({searchMutation.data.total} results in{' '}
                {searchMutation.data.took_ms}ms)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {searchMutation.isIdle && !searchMutation.data && (
            <p className="text-muted-foreground text-center py-8">
              Enter a search query to find conversations
            </p>
          )}

          {searchMutation.isPending && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {searchMutation.isError && (
            <p className="text-destructive text-center py-8">
              Error: {searchMutation.error?.message || 'Search failed'}
            </p>
          )}

          {searchMutation.data && searchMutation.data.results.length === 0 && (
            <p className="text-muted-foreground text-center py-8">
              No results found for "{searchMutation.data.query}"
            </p>
          )}

          {searchMutation.data && searchMutation.data.results.length > 0 && (
            <div className="space-y-4">
              {searchMutation.data.results.map((result) => (
                <div
                  key={result.message_id}
                  onClick={() => handleResultClick(result)}
                  className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-4">
                      <div className="font-medium">{result.project_name}</div>
                      <div className="text-sm text-muted-foreground flex items-center gap-2">
                        {getMessageTypeIcon(result.message_type)}
                        {result.model && (
                          <>
                            <Bot className="h-3 w-3" />
                            <span>{result.model.split('/').pop()}</span>
                          </>
                        )}
                        {result.cost_usd && (
                          <span className="text-green-600">
                            ${result.cost_usd.toFixed(4)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground flex items-center gap-2">
                      <Calendar className="h-3 w-3" />
                      {formatDistanceToNow(new Date(result.timestamp), {
                        addSuffix: true,
                      })}
                    </div>
                  </div>

                  {result.session_summary && (
                    <p className="text-sm text-muted-foreground mb-2">
                      Session: {result.session_summary}
                    </p>
                  )}

                  <p className="text-sm">{result.content_preview}</p>

                  {formatHighlights(result.highlights)}

                  <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Relevance: {(result.score * 100).toFixed(0)}%</span>
                    <ChevronRight className="h-3 w-3" />
                  </div>
                </div>
              ))}

              {searchMutation.data.total >
                searchMutation.data.results.length && (
                <div className="text-center py-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      searchMutation.mutate({
                        query: searchMutation.data!.query,
                        filters,
                        skip:
                          searchMutation.data!.skip +
                          searchMutation.data!.limit,
                        limit: 20,
                        highlight: true,
                      });
                    }}
                  >
                    Load More
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
