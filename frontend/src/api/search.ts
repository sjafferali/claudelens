import { apiClient } from './client';

export interface SearchFilters {
  project_ids?: string[];
  session_ids?: string[];
  message_types?: string[];
  models?: string[];
  start_date?: string;
  end_date?: string;
  has_code?: boolean;
  code_language?: string;
  min_cost?: number;
  max_cost?: number;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  skip?: number;
  limit?: number;
  highlight?: boolean;
  is_regex?: boolean;
  continue_token?: string;
}

export interface SearchHighlight {
  field: string;
  snippet: string;
  score: number;
}

export interface SearchResult {
  message_id: string;
  session_id: string;
  session_mongo_id?: string;
  project_id: string;
  project_name: string;
  message_type: string;
  timestamp: string;
  content_preview: string;
  highlights: SearchHighlight[];
  score: number;
  session_summary?: string;
  model?: string;
  cost_usd?: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  skip: number;
  limit: number;
  results: SearchResult[];
  took_ms: number;
  filters_applied: SearchFilters;
  search_status?: string;
  months_searched?: string[];
  has_more_months?: boolean;
  continue_token?: string;
}

export interface SearchSuggestion {
  text: string;
  type: string;
  count?: number;
}

export interface RecentSearch {
  query: string;
  timestamp: string;
  filters?: SearchFilters;
  result_count: number;
}

export interface SearchStats {
  total_searches: number;
  searches_today: number;
  searches_this_week: number;
  searches_this_month: number;
  popular_queries: Array<{
    query: string;
    count: number;
  }>;
  popular_filters: Array<{
    filter: string;
    count: number;
  }>;
}

export const searchApi = {
  async search(request: SearchRequest): Promise<SearchResponse> {
    return apiClient.post<SearchResponse>('/search/', request);
  },

  async searchCode(
    request: SearchRequest,
    language?: string
  ): Promise<SearchResponse> {
    const params = language ? `?language=${encodeURIComponent(language)}` : '';
    return apiClient.post<SearchResponse>(`/search/code${params}`, request);
  },

  async getSuggestions(
    query: string,
    limit: number = 10
  ): Promise<SearchSuggestion[]> {
    const params = new URLSearchParams({ query, limit: limit.toString() });
    return apiClient.get<SearchSuggestion[]>(`/search/suggestions?${params}`);
  },

  async getRecentSearches(limit: number = 10): Promise<RecentSearch[]> {
    return apiClient.get<RecentSearch[]>(`/search/recent?limit=${limit}`);
  },

  async getSearchStats(): Promise<SearchStats> {
    return apiClient.get<SearchStats>('/search/stats');
  },
};
