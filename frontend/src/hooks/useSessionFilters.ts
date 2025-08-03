import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SessionsParams } from '@/api/sessions';

export interface SessionFilters extends SessionsParams {
  page?: number;
}

export function useSessionFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo<SessionFilters>(() => {
    const params: SessionFilters = {};

    const search = searchParams.get('search');
    if (search) params.search = search;

    const startDate = searchParams.get('start_date');
    if (startDate) params.startDate = startDate;

    const endDate = searchParams.get('end_date');
    if (endDate) params.endDate = endDate;

    const sortBy = searchParams.get('sort_by');
    if (sortBy) params.sortBy = sortBy as SessionFilters['sortBy'];

    const sortOrder = searchParams.get('sort_order');
    if (sortOrder) params.sortOrder = sortOrder as SessionFilters['sortOrder'];

    const projectId = searchParams.get('project_id');
    if (projectId) params.projectId = projectId;

    const page = searchParams.get('page');
    if (page) params.page = parseInt(page, 10);

    const skip = searchParams.get('skip');
    if (skip) params.skip = parseInt(skip, 10);

    const limit = searchParams.get('limit');
    if (limit) params.limit = parseInt(limit, 10);

    return params;
  }, [searchParams]);

  const updateFilters = useCallback(
    (updates: Partial<SessionFilters>) => {
      const newParams = new URLSearchParams(searchParams);

      Object.entries(updates).forEach(([key, value]) => {
        if (value === undefined || value === null || value === '') {
          newParams.delete(
            key === 'startDate'
              ? 'start_date'
              : key === 'endDate'
              ? 'end_date'
              : key === 'sortBy'
              ? 'sort_by'
              : key === 'sortOrder'
              ? 'sort_order'
              : key === 'projectId'
              ? 'project_id'
              : key
          );
        } else {
          const paramKey =
            key === 'startDate'
              ? 'start_date'
              : key === 'endDate'
              ? 'end_date'
              : key === 'sortBy'
              ? 'sort_by'
              : key === 'sortOrder'
              ? 'sort_order'
              : key === 'projectId'
              ? 'project_id'
              : key;
          newParams.set(paramKey, String(value));
        }
      });

      // Reset to page 1 when filters change (except when page itself is changing)
      if (!('page' in updates) && !('skip' in updates)) {
        newParams.delete('page');
        newParams.delete('skip');
      }

      setSearchParams(newParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  const removeFilter = useCallback(
    (filterKey: string) => {
      const newParams = new URLSearchParams(searchParams);
      const paramKey =
        filterKey === 'startDate'
          ? 'start_date'
          : filterKey === 'endDate'
          ? 'end_date'
          : filterKey === 'sortBy'
          ? 'sort_by'
          : filterKey === 'sortOrder'
          ? 'sort_order'
          : filterKey === 'projectId'
          ? 'project_id'
          : filterKey;

      newParams.delete(paramKey);

      // Reset to page 1 when filters change
      newParams.delete('page');
      newParams.delete('skip');

      setSearchParams(newParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  const clearAllFilters = useCallback(() => {
    const newParams = new URLSearchParams();

    // Preserve project_id if it was in the original URL (not added as a filter)
    const projectId = searchParams.get('project_id');
    if (projectId) {
      newParams.set('project_id', projectId);
    }

    setSearchParams(newParams, { replace: true });
  }, [searchParams, setSearchParams]);

  const hasActiveFilters = useMemo(() => {
    return !!(
      filters.search ||
      filters.startDate ||
      filters.endDate ||
      (filters.sortBy && filters.sortBy !== 'started_at') ||
      (filters.sortOrder && filters.sortOrder !== 'desc')
    );
  }, [filters]);

  return {
    filters,
    updateFilters,
    removeFilter,
    clearAllFilters,
    hasActiveFilters,
  };
}
