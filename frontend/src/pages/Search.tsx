import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Search as SearchIcon,
  Loader2,
  Calendar,
  Bot,
  ChevronRight,
  User,
  Code2,
  Filter,
  Regex,
  Type,
  AlertCircle,
  HelpCircle,
  Copy,
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
import {
  SearchResultSkeleton,
  ListSkeleton,
} from '@/components/common/LoadingSkeleton';

// Common regex patterns for quick access
const REGEX_PATTERNS = [
  {
    name: 'Function definitions',
    pattern: '\\b(function|def|func)\\s+\\w+',
    description: 'Match function declarations',
  },
  {
    name: 'Import statements',
    pattern: '^(import|from|require)\\s+.+',
    description: 'Match import/require statements',
  },
  {
    name: 'URLs',
    pattern: 'https?://[^\\s]+',
    description: 'Match HTTP/HTTPS URLs',
  },
  {
    name: 'Email addresses',
    pattern: '[\\w\\.]+@[\\w\\.]+',
    description: 'Match email addresses',
  },
  {
    name: 'Code comments',
    pattern: '(//.*|/\\*.*\\*/|#.*)',
    description: 'Match code comments',
  },
  {
    name: 'Error messages',
    pattern: '(error|exception|failed|failure)\\s*:?.*',
    description: 'Match error-related text',
  },
  {
    name: 'API endpoints',
    pattern: '/(api|v\\d+)/[\\w/]+',
    description: 'Match API endpoint paths',
  },
  {
    name: 'Variable declarations',
    pattern: '\\b(var|let|const|my|local)\\s+\\w+',
    description: 'Match variable declarations',
  },
  {
    name: 'Class definitions',
    pattern: '\\bclass\\s+\\w+',
    description: 'Match class declarations',
  },
  {
    name: 'Hex colors',
    pattern: '#[0-9a-fA-F]{3,6}\\b',
    description: 'Match hex color codes',
  },
];

export default function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [allResults, setAllResults] = useState<SearchResult[]>([]);
  const [isRegexMode, setIsRegexMode] = useState(false);
  const [searchMetadata, setSearchMetadata] = useState<{
    status?: string;
    monthsSearched?: string[];
    hasMoreMonths?: boolean;
    continueToken?: string;
  }>({});
  const [regexError, setRegexError] = useState<string | null>(null);
  const [showRegexHelper, setShowRegexHelper] = useState(false);
  const [regexHistory, setRegexHistory] = useState<string[]>([]);
  const [showRegexTester, setShowRegexTester] = useState(false);
  const [testText, setTestText] = useState(
    'Sample text to test your regex pattern.\nYou can include function definitions, import statements,\nerror messages, or any other text you want to search for.'
  );

  // Load regex history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('regexSearchHistory');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        if (Array.isArray(parsed)) {
          setRegexHistory(parsed.slice(0, 10)); // Keep only last 10 patterns
        }
      } catch (e) {
        console.error('Failed to parse regex history:', e);
      }
    }
  }, []);

  // Save regex pattern to history
  const saveToRegexHistory = (pattern: string) => {
    if (!pattern || pattern.trim().length === 0) return;

    // Remove duplicates and add to beginning
    const newHistory = [
      pattern,
      ...regexHistory.filter((p) => p !== pattern),
    ].slice(0, 10);
    setRegexHistory(newHistory);
    localStorage.setItem('regexSearchHistory', JSON.stringify(newHistory));
  };

  // Clear regex history
  const clearRegexHistory = () => {
    setRegexHistory([]);
    localStorage.removeItem('regexSearchHistory');
  };

  // Test regex pattern and get highlighted result
  const getHighlightedTestText = () => {
    if (!query || !isRegexMode || regexError) {
      return testText;
    }

    try {
      const regex = new RegExp(query, 'gi');
      const matches = testText.match(regex);

      if (!matches) {
        return testText;
      }

      // Replace matches with highlighted version
      let highlightedText = testText;
      const uniqueMatches = [...new Set(matches)];

      uniqueMatches.forEach((match) => {
        const escapedMatch = match.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const matchRegex = new RegExp(escapedMatch, 'gi');
        highlightedText = highlightedText.replace(
          matchRegex,
          `<mark class="bg-yellow-400 dark:bg-yellow-600 text-black dark:text-black font-bold px-1 rounded">${match}</mark>`
        );
      });

      return highlightedText;
    } catch (e) {
      return testText;
    }
  };

  // Count regex matches in test text
  const countMatches = () => {
    if (!query || !isRegexMode || regexError) return 0;

    try {
      const regex = new RegExp(query, 'gi');
      const matches = testText.match(regex);
      return matches ? matches.length : 0;
    } catch (e) {
      return 0;
    }
  };

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

  // Update allResults and metadata when search mutation succeeds
  useEffect(() => {
    if (searchMutation.data) {
      if (!searchMutation.data.continue_token) {
        // New search, replace all results
        setAllResults(searchMutation.data.results);
      } else {
        // Continuing search, append results
        setAllResults((prev) => [...prev, ...searchMutation.data.results]);
      }

      // Update search metadata
      setSearchMetadata({
        status: searchMutation.data.search_status,
        monthsSearched: searchMutation.data.months_searched,
        hasMoreMonths: searchMutation.data.has_more_months,
        continueToken: searchMutation.data.continue_token,
      });
    }
  }, [searchMutation.data]);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;

    // Validate regex if in regex mode
    if (isRegexMode) {
      try {
        new RegExp(query);
        setRegexError(null);
        // Save valid regex pattern to history
        saveToRegexHistory(query.trim());
      } catch (error) {
        setRegexError('Invalid regex pattern: ' + (error as Error).message);
        return;
      }
    }

    setShowSuggestions(false);
    setAllResults([]); // Clear previous results
    setSearchMetadata({}); // Clear metadata
    searchMutation.mutate({
      query: query.trim(),
      filters,
      limit: 20,
      highlight: true,
      is_regex: isRegexMode,
    });
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    setAllResults([]); // Clear previous results
    setSearchMetadata({}); // Clear metadata
    searchMutation.mutate({
      query: suggestion,
      filters,
      limit: 20,
      highlight: true,
      is_regex: isRegexMode,
    });
  };

  // Handle searching more months
  const handleSearchMoreMonths = useCallback(() => {
    if (searchMetadata.continueToken && searchMutation.data) {
      searchMutation.mutate({
        query: searchMutation.data.query,
        filters,
        limit: 20,
        highlight: true,
        is_regex: isRegexMode,
        continue_token: searchMetadata.continueToken,
      });
    }
  }, [searchMetadata.continueToken, searchMutation, filters, isRegexMode]);

  const handleResultClick = (result: SearchResult) => {
    // Navigate to the session detail page using sessionId (UUID format)
    const sessionIdForNav = result.session_id;
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
            __html: bestHighlight.snippet
              .replace(
                /<mark>/g,
                '<mark class="bg-yellow-400 dark:bg-yellow-600 text-black dark:text-black font-bold px-1 rounded">'
              )
              .replace(/<\/mark>/g, '</mark>'),
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
              <div className="flex gap-2 mb-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsRegexMode(false);
                    setRegexError(null);
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                    !isRegexMode
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-accent'
                  }`}
                  title="Text search mode"
                >
                  <Type className="h-4 w-4" />
                  <span className="text-sm">Text</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsRegexMode(true);
                    setShowSuggestions(false);
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                    isRegexMode
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-accent'
                  }`}
                  title="Regular expression mode"
                >
                  <Regex className="h-4 w-4" />
                  <span className="text-sm">Regex</span>
                </button>

                {/* Regex Helper Buttons */}
                {isRegexMode && (
                  <div className="flex gap-2 ml-auto">
                    <button
                      type="button"
                      onClick={() => {
                        setShowRegexHelper(!showRegexHelper);
                        setShowRegexTester(false);
                      }}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                        showRegexHelper
                          ? 'bg-accent'
                          : 'bg-muted hover:bg-accent'
                      }`}
                      title="Regex pattern help"
                    >
                      <HelpCircle className="h-4 w-4" />
                      <span className="text-sm">Pattern Help</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowRegexTester(!showRegexTester);
                        setShowRegexHelper(false);
                      }}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors ${
                        showRegexTester
                          ? 'bg-accent'
                          : 'bg-muted hover:bg-accent'
                      }`}
                      title="Test regex pattern"
                    >
                      <Code2 className="h-4 w-4" />
                      <span className="text-sm">Test Pattern</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Regex Helper Dropdown */}
              {isRegexMode && showRegexHelper && (
                <div className="mb-4 p-4 bg-muted/50 rounded-lg border border-border">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold text-sm">
                      Regex Pattern Helper
                    </h4>
                    <button
                      type="button"
                      onClick={() => setShowRegexHelper(false)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      ×
                    </button>
                  </div>

                  {/* Recent Regex Patterns */}
                  {regexHistory.length > 0 && (
                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <h5 className="font-medium text-sm text-muted-foreground">
                          Recent Patterns
                        </h5>
                        <button
                          type="button"
                          onClick={clearRegexHistory}
                          className="text-xs text-muted-foreground hover:text-foreground"
                        >
                          Clear
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {regexHistory.map((pattern, index) => (
                          <button
                            key={index}
                            type="button"
                            onClick={() => {
                              setQuery(pattern);
                              setRegexError(null);
                            }}
                            className="px-2 py-1 bg-background hover:bg-accent rounded text-xs font-mono truncate max-w-[200px] border border-border"
                            title={pattern}
                          >
                            {pattern}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <h5 className="font-medium text-sm text-muted-foreground mb-2">
                    Common Patterns
                  </h5>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
                    {REGEX_PATTERNS.map((pattern) => (
                      <div
                        key={pattern.name}
                        className="flex items-center justify-between p-2 bg-background rounded hover:bg-accent group cursor-pointer"
                        onClick={() => {
                          setQuery(pattern.pattern);
                          setRegexError(null);
                        }}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm">
                            {pattern.name}
                          </div>
                          <div className="text-xs text-muted-foreground truncate">
                            {pattern.description}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(pattern.pattern);
                          }}
                          className="ml-2 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Copy pattern"
                        >
                          <Copy className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="text-xs text-muted-foreground">
                    <div className="font-semibold mb-1">Quick Reference:</div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                      <div>
                        <code className="bg-background px-1 rounded">.</code> -
                        Any character
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">*</code> -
                        Zero or more
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">+</code> -
                        One or more
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">?</code> -
                        Zero or one
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">^</code> -
                        Start of line
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">$</code> -
                        End of line
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">\b</code> -
                        Word boundary
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">\w</code> -
                        Word character
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">\d</code> -
                        Digit
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">\s</code> -
                        Whitespace
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">
                          [abc]
                        </code>{' '}
                        - Character set
                      </div>
                      <div>
                        <code className="bg-background px-1 rounded">
                          (a|b)
                        </code>{' '}
                        - Alternation
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Regex Tester */}
              {isRegexMode && showRegexTester && (
                <div className="mb-4 p-4 bg-muted/50 rounded-lg border border-border">
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-sm">
                        Test Your Pattern
                      </h4>
                      {query && !regexError && (
                        <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                          {countMatches()} match
                          {countMatches() !== 1 ? 'es' : ''}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowRegexTester(false)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      ×
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1">
                        Test Text (editable)
                      </label>
                      <textarea
                        value={testText}
                        onChange={(e) => setTestText(e.target.value)}
                        className="w-full h-32 p-2 bg-background border border-input rounded text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                        placeholder="Enter text to test your regex pattern..."
                      />
                    </div>

                    {query && !regexError && (
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1">
                          Preview with Highlights
                        </label>
                        <div
                          className="p-2 bg-background border border-input rounded text-sm font-mono whitespace-pre-wrap break-words max-h-32 overflow-auto"
                          dangerouslySetInnerHTML={{
                            __html: getHighlightedTestText(),
                          }}
                        />
                      </div>
                    )}

                    {!query && (
                      <div className="text-sm text-muted-foreground text-center py-4">
                        Enter a regex pattern above to see matches highlighted
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-4">
                <div className="relative flex-1">
                  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      if (!isRegexMode) {
                        setShowSuggestions(true);
                      }
                      // Validate regex on change
                      if (isRegexMode && e.target.value) {
                        try {
                          new RegExp(e.target.value);
                          setRegexError(null);
                        } catch (error) {
                          setRegexError(
                            'Invalid pattern: ' + (error as Error).message
                          );
                        }
                      } else {
                        setRegexError(null);
                      }
                    }}
                    onFocus={() => !isRegexMode && setShowSuggestions(true)}
                    placeholder={
                      isRegexMode
                        ? 'Enter regex pattern...'
                        : 'Search for messages, code, or topics...'
                    }
                    className={`pl-10 pr-4 py-2 w-full bg-background border rounded-md focus:outline-none focus:ring-2 ${
                      regexError
                        ? 'border-destructive focus:ring-destructive'
                        : 'border-input focus:ring-ring'
                    }`}
                  />

                  {/* Error message for invalid regex */}
                  {regexError && (
                    <div className="absolute top-full left-0 mt-1 flex items-center gap-2 text-sm text-destructive">
                      <AlertCircle className="h-4 w-4" />
                      <span>{regexError}</span>
                    </div>
                  )}

                  {/* Suggestions dropdown (not shown in regex mode) */}
                  {!isRegexMode &&
                    showSuggestions &&
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
          {searchMetadata.status && (
            <CardDescription className="mt-2">
              <div className="flex items-center gap-2">
                {searchMutation.isPending && (
                  <Loader2 className="h-3 w-3 animate-spin" />
                )}
                <span>{searchMetadata.status}</span>
              </div>
              {searchMetadata.monthsSearched &&
                searchMetadata.monthsSearched.length > 0 && (
                  <div className="mt-1 text-xs">
                    Searched months: {searchMetadata.monthsSearched.join(', ')}
                  </div>
                )}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {searchMutation.isIdle && !searchMutation.data && (
            <p className="text-muted-foreground text-center py-8">
              Enter a search query to find conversations
            </p>
          )}

          {searchMutation.isPending && (
            <ListSkeleton
              items={5}
              component={SearchResultSkeleton}
              className="py-4"
            />
          )}

          {searchMutation.isError && (
            <p className="text-destructive text-center py-8">
              Error: {searchMutation.error?.message || 'Search failed'}
            </p>
          )}

          {searchMutation.data && allResults.length === 0 && (
            <p className="text-muted-foreground text-center py-8">
              No results found for "{searchMutation.data.query}"
            </p>
          )}

          {allResults.length > 0 && (
            <div className="space-y-4">
              {allResults.map((result) => (
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
                    <div className="text-sm line-clamp-2">
                      <span
                        dangerouslySetInnerHTML={{
                          __html: result.content_preview
                            .replace(
                              /<mark>/g,
                              '<mark class="bg-yellow-400 dark:bg-yellow-600 text-black dark:text-black font-bold px-1 rounded">'
                            )
                            .replace(/<\/mark>/g, '</mark>'),
                        }}
                      />
                    </div>
                    {formatHighlights(result.highlights)}
                  </div>
                </div>
              ))}

              {/* Show "Load More" button for pagination within searched months */}
              {searchMutation.data &&
                searchMutation.data.total > allResults.length && (
                  <div className="text-center py-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        searchMutation.mutate({
                          query: searchMutation.data!.query,
                          filters,
                          skip: allResults.length,
                          limit: 20,
                          highlight: true,
                          is_regex: isRegexMode,
                        });
                      }}
                      disabled={searchMutation.isPending}
                    >
                      {searchMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        'Load More Results'
                      )}
                    </Button>
                  </div>
                )}

              {/* Show "Search More Months" button if there are more months to search */}
              {searchMetadata.hasMoreMonths && (
                <div className="text-center py-4 border-t mt-4">
                  <div className="text-sm text-muted-foreground mb-2">
                    Found {allResults.length} results so far. Search older
                    months for more results?
                  </div>
                  <Button
                    variant="default"
                    onClick={handleSearchMoreMonths}
                    disabled={searchMutation.isPending}
                  >
                    {searchMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Searching...
                      </>
                    ) : (
                      'Search Older Months'
                    )}
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
