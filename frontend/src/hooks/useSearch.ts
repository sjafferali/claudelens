import { useQuery, useMutation } from '@tanstack/react-query';
import { searchApi, SearchRequest, SearchResponse } from '@/api/search';

export function useSearch() {
  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: (request) => searchApi.search(request),
  });
}

export function useSearchCode() {
  return useMutation<
    SearchResponse,
    Error,
    { request: SearchRequest; language?: string }
  >({
    mutationFn: ({ request, language }) =>
      searchApi.searchCode(request, language),
  });
}

export function useSearchSuggestions(query: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['search-suggestions', query],
    queryFn: () => searchApi.getSuggestions(query),
    enabled: enabled && query.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useRecentSearches() {
  return useQuery({
    queryKey: ['recent-searches'],
    queryFn: () => searchApi.getRecentSearches(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useSearchStats() {
  return useQuery({
    queryKey: ['search-stats'],
    queryFn: () => searchApi.getSearchStats(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
