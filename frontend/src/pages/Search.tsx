import { useState, useEffect, useMemo } from 'react';
import {
  Search as SearchIcon,
  Loader2,
  Calendar,
  Bot,
  ChevronRight,
  User,
  Code2,
  Filter,
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
import { useAvailableModels } from '@/hooks/useModels';
import { SearchFilters, SearchResult } from '@/api/search';
import { formatDistanceToNow } from 'date-fns';

export default function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.project_ids?.length) count++;
    if (filters.start_date) count++;
    if (filters.models?.length) count++;
    if (filters.has_code) count++;
    if (filters.message_types?.length) count++;
    return count;
  }, [filters]);

  const { data: projects } = useProjects({ limit: 100 });
  const { data: availableModels } = useAvailableModels();
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
              '<mark class="bg-yellow-300 dark:bg-yellow-700 font-semibold px-0.5 rounded">'
            ),
          }}
        />
      </div>
    );
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'user':
        return (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3 text-blue-600" />
            <span className="text-blue-600 font-medium">User</span>
          </div>
        );
      case 'assistant':
        return (
          <div className="flex items-center gap-1">
            <Bot className="h-3 w-3 text-green-600" />
            <span className="text-green-600 font-medium">Assistant</span>
          </div>
        );
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

            <div className="space-y-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Filter className="h-4 w-4" />
                  <span>Filters</span>
                  {activeFilterCount > 0 && (
                    <span className="bg-primary text-primary-foreground text-xs px-1.5 py-0.5 rounded-full">
                      {activeFilterCount}
                    </span>
                  )}
                </div>
                {activeFilterCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFilters({})}
                    className="text-xs"
                  >
                    Clear filters
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Project
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-background border border-input rounded-md hover:border-ring transition-colors"
                    value={filters.project_ids?.[0] || ''}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        project_ids: e.target.value
                          ? [e.target.value]
                          : undefined,
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
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Time Range
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-background border border-input rounded-md hover:border-ring transition-colors"
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
                      setFilters({
                        ...filters,
                        start_date: date.toISOString(),
                      });
                    }}
                  >
                    <option value="">All Time</option>
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Model
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-background border border-input rounded-md hover:border-ring transition-colors"
                    value={filters.models?.[0] || ''}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        models: e.target.value ? [e.target.value] : undefined,
                      })
                    }
                  >
                    <option value="">All Models</option>
                    {availableModels?.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={filters.has_code || false}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        has_code: e.target.checked || undefined,
                      })
                    }
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <Code2 className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  <span className="text-sm group-hover:text-foreground transition-colors">
                    Code only
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={filters.message_types?.includes('user') || false}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        message_types: e.target.checked ? ['user'] : undefined,
                      })
                    }
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <User className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  <span className="text-sm group-hover:text-foreground transition-colors">
                    User messages only
                  </span>
                </label>
              </div>
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
                  className="group relative p-4 border rounded-lg hover:bg-accent hover:border-ring cursor-pointer transition-all duration-200 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-semibold text-sm truncate">
                          {result.project_name}
                        </h4>
                        {getMessageTypeIcon(result.message_type)}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                        {result.model && (
                          <div className="flex items-center gap-1">
                            <Bot className="h-3 w-3" />
                            <span className="truncate max-w-[150px]">
                              {result.model.split('/').pop()}
                            </span>
                          </div>
                        )}
                        {result.cost_usd && (
                          <div className="flex items-center gap-1">
                            <span className="text-green-600 font-medium">
                              ${result.cost_usd.toFixed(4)}
                            </span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>
                            {formatDistanceToNow(new Date(result.timestamp), {
                              addSuffix: true,
                            })}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <div className="text-xs font-medium text-muted-foreground bg-muted px-2 py-1 rounded">
                        {(result.score * 100).toFixed(0)}% match
                      </div>
                      <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                    </div>
                  </div>

                  {result.session_summary && (
                    <div className="mb-2 p-2 bg-muted/50 rounded text-xs text-muted-foreground">
                      <span className="font-medium">Session:</span>{' '}
                      {result.session_summary}
                    </div>
                  )}

                  <div className="space-y-2">
                    <p className="text-sm line-clamp-2">
                      {result.content_preview}
                    </p>
                    {formatHighlights(result.highlights)}
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
