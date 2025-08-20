# React Query Patterns for ClaudeLens

## Overview
This document outlines React Query (TanStack Query) patterns used throughout the ClaudeLens frontend application, specifically for implementing import/export functionality.

## Configuration

### Query Client Setup
```typescript
// frontend/src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

## Query Patterns

### Basic Query Hook Pattern
```typescript
// frontend/src/hooks/useProjects.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export const useProjects = (filters?: ProjectFilters) => {
  return useQuery({
    queryKey: ['projects', filters],
    queryFn: () => apiClient.getProjects(filters),
    enabled: !!apiClient.isAuthenticated(),
  });
};
```

### Query with Pagination
```typescript
// frontend/src/hooks/useSessions.ts
export const useSessions = (page: number = 1, limit: number = 20) => {
  return useQuery({
    queryKey: ['sessions', { page, limit }],
    queryFn: () => apiClient.getSessions({
      skip: (page - 1) * limit,
      limit
    }),
    keepPreviousData: true, // Smooth pagination
  });
};
```

### Dependent Queries
```typescript
// frontend/src/hooks/useSessionMessages.ts
export const useSessionMessages = (sessionId: string | null) => {
  return useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => apiClient.getMessages(sessionId!),
    enabled: !!sessionId, // Only run when sessionId exists
  });
};
```

## Mutation Patterns

### Basic Mutation with Cache Invalidation
```typescript
// frontend/src/hooks/useDeleteProject.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => apiClient.deleteProject(projectId),
    onSuccess: () => {
      // Invalidate and refetch projects
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success('Project deleted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to delete project: ${error.message}`);
    },
  });
};
```

### Optimistic Updates Pattern
```typescript
// frontend/src/hooks/useUpdateSession.ts
export const useUpdateSession = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SessionUpdate }) =>
      apiClient.updateSession(id, data),

    // Optimistic update
    onMutate: async ({ id, data }) => {
      // Cancel in-flight queries
      await queryClient.cancelQueries({ queryKey: ['sessions', id] });

      // Snapshot previous value
      const previousSession = queryClient.getQueryData(['sessions', id]);

      // Optimistically update
      queryClient.setQueryData(['sessions', id], (old: Session) => ({
        ...old,
        ...data,
      }));

      // Return context with snapshot
      return { previousSession };
    },

    // Rollback on error
    onError: (err, variables, context) => {
      if (context?.previousSession) {
        queryClient.setQueryData(
          ['sessions', variables.id],
          context.previousSession
        );
      }
      toast.error('Failed to update session');
    },

    // Refetch after success
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sessions', variables.id] });
    },
  });
};
```

## Import/Export Specific Patterns

### Export Mutation with Progress Tracking
```typescript
// frontend/src/hooks/useExport.ts
export const useExport = () => {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);

  return useMutation({
    mutationFn: async (options: ExportOptions) => {
      // Start export job
      const { jobId } = await apiClient.startExport(options);

      // Track progress via WebSocket
      return new Promise((resolve, reject) => {
        const ws = new WebSocket(`ws://localhost:8000/ws/export/${jobId}`);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setProgress(data.progress);

          if (data.status === 'completed') {
            ws.close();
            resolve(data);
          } else if (data.status === 'failed') {
            ws.close();
            reject(new Error(data.error));
          }
        };

        ws.onerror = (error) => {
          ws.close();
          reject(error);
        };
      });
    },

    onSuccess: (data) => {
      // Add to export history
      queryClient.invalidateQueries({ queryKey: ['export-history'] });

      // Trigger download
      window.location.href = data.downloadUrl;
      toast.success('Export completed successfully');
    },

    onError: (error) => {
      toast.error(`Export failed: ${error.message}`);
    },
  });
};
```

### File Upload Mutation for Import
```typescript
// frontend/src/hooks/useImport.ts
export const useImport = () => {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState(0);

  return useMutation({
    mutationFn: async ({
      file,
      options
    }: {
      file: File;
      options: ImportOptions
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('options', JSON.stringify(options));

      return apiClient.post<ImportResponse>('/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });
    },

    onSuccess: (data) => {
      // Invalidate all affected queries
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['messages'] });

      toast.success(`Imported ${data.importedCount} conversations`);
    },

    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Import failed';
      toast.error(message);
    },
  });
};
```

### Infinite Query for Export History
```typescript
// frontend/src/hooks/useExportHistory.ts
import { useInfiniteQuery } from '@tanstack/react-query';

export const useExportHistory = () => {
  return useInfiniteQuery({
    queryKey: ['export-history'],
    queryFn: ({ pageParam = 0 }) =>
      apiClient.getExportHistory({
        skip: pageParam,
        limit: 20
      }),
    getNextPageParam: (lastPage, pages) => {
      if (lastPage.items.length < 20) return undefined;
      return pages.length * 20;
    },
  });
};

// Usage in component
const {
  data,
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage
} = useExportHistory();

const allExports = data?.pages.flatMap(page => page.items) ?? [];
```

## Cache Management Patterns

### Selective Cache Invalidation
```typescript
// Invalidate specific queries after import
const handleImportSuccess = () => {
  // Invalidate only affected data
  queryClient.invalidateQueries({
    queryKey: ['sessions'],
    exact: false, // Invalidate all session-related queries
  });

  // Keep export history cache valid
  queryClient.invalidateQueries({
    queryKey: ['export-history'],
    refetchType: 'none', // Don't refetch, just mark as stale
  });
};
```

### Manual Cache Updates
```typescript
// Update cache after successful export
const updateExportHistoryCache = (newExport: ExportJob) => {
  queryClient.setQueryData(
    ['export-history'],
    (old: { pages: ExportHistoryPage[] }) => {
      if (!old) return { pages: [{ items: [newExport] }] };

      return {
        ...old,
        pages: [
          {
            ...old.pages[0],
            items: [newExport, ...old.pages[0].items],
          },
          ...old.pages.slice(1),
        ],
      };
    }
  );
};
```

### Prefetching Pattern
```typescript
// Prefetch export formats on page load
export const useExportFormats = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Prefetch available export formats
    queryClient.prefetchQuery({
      queryKey: ['export-formats'],
      queryFn: () => apiClient.getExportFormats(),
      staleTime: Infinity, // Formats don't change
    });
  }, [queryClient]);
};
```

## Error Handling Patterns

### Global Error Handler
```typescript
// frontend/src/utils/queryErrorHandler.ts
export const queryErrorHandler = (error: unknown) => {
  if (error instanceof Error) {
    // Handle network errors
    if (error.message === 'Network Error') {
      toast.error('Connection lost. Please check your internet connection.');
      return;
    }

    // Handle API errors
    if ('response' in error) {
      const apiError = error as any;
      const status = apiError.response?.status;

      switch (status) {
        case 401:
          // Handle unauthorized
          window.location.href = '/login';
          break;
        case 429:
          toast.error('Too many requests. Please try again later.');
          break;
        case 500:
          toast.error('Server error. Please try again.');
          break;
        default:
          toast.error(apiError.response?.data?.detail || 'An error occurred');
      }
    }
  }
};

// Apply to query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      onError: queryErrorHandler,
    },
    mutations: {
      onError: queryErrorHandler,
    },
  },
});
```

## Testing Patterns

### Testing Queries
```typescript
// frontend/src/hooks/__tests__/useExport.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useExport } from '../useExport';

describe('useExport', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('should export data successfully', async () => {
    const { result } = renderHook(() => useExport(), { wrapper });

    act(() => {
      result.current.mutate({
        format: 'json',
        sessionIds: ['session-1'],
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toMatchObject({
      jobId: expect.any(String),
      downloadUrl: expect.any(String),
    });
  });
});
```

### Mocking React Query
```typescript
// frontend/src/__mocks__/react-query.ts
import { vi } from 'vitest';

export const mockUseQuery = vi.fn();
export const mockUseMutation = vi.fn();

vi.mock('@tanstack/react-query', () => ({
  useQuery: mockUseQuery,
  useMutation: mockUseMutation,
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
  }),
}));
```

## Performance Optimizations

### Query Key Factory
```typescript
// frontend/src/utils/queryKeys.ts
export const queryKeys = {
  all: ['claudelens'] as const,
  sessions: () => [...queryKeys.all, 'sessions'] as const,
  session: (id: string) => [...queryKeys.sessions(), id] as const,
  sessionMessages: (id: string) => [...queryKeys.session(id), 'messages'] as const,

  exports: () => [...queryKeys.all, 'exports'] as const,
  exportHistory: () => [...queryKeys.exports(), 'history'] as const,
  exportJob: (id: string) => [...queryKeys.exports(), 'job', id] as const,

  imports: () => [...queryKeys.all, 'imports'] as const,
  importValidation: (fileHash: string) =>
    [...queryKeys.imports(), 'validation', fileHash] as const,
};

// Usage
const query = useQuery({
  queryKey: queryKeys.sessionMessages(sessionId),
  // ...
});
```

### Suspense Integration
```typescript
// frontend/src/hooks/useSuspenseExportHistory.ts
import { useSuspenseQuery } from '@tanstack/react-query';

export const useSuspenseExportHistory = () => {
  return useSuspenseQuery({
    queryKey: ['export-history'],
    queryFn: () => apiClient.getExportHistory(),
  });
};

// Usage in component with React Suspense
<Suspense fallback={<ExportHistorySkeleton />}>
  <ExportHistoryTable />
</Suspense>
```

## Best Practices for ClaudeLens

1. **Always invalidate related queries after mutations**
```typescript
// After importing data, invalidate all affected queries
queryClient.invalidateQueries({ queryKey: ['sessions'] });
queryClient.invalidateQueries({ queryKey: ['projects'] });
```

2. **Use query key factories for consistency**
```typescript
// Consistent query keys prevent cache misses
queryKey: queryKeys.sessionMessages(sessionId)
```

3. **Handle loading and error states explicitly**
```typescript
if (query.isLoading) return <Skeleton />;
if (query.isError) return <ErrorMessage error={query.error} />;
```

4. **Use optimistic updates for better UX**
```typescript
// Update UI immediately, rollback on error
onMutate: async (newData) => {
  // Optimistic update logic
}
```

5. **Leverage React Query DevTools in development**
```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// In App.tsx
{import.meta.env.DEV && <ReactQueryDevtools />}
```

This guide provides comprehensive React Query patterns tailored for ClaudeLens's architecture and requirements.
