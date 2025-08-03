import { X } from 'lucide-react';
import { format } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';

interface ActiveFiltersProps {
  filters: {
    search?: string;
    startDate?: string;
    endDate?: string;
    sortBy?: string;
    sortOrder?: string;
    projectId?: string;
  };
  onRemoveFilter: (filterKey: string) => void;
  onClearAll: () => void;
}

const SORT_LABELS: Record<string, string> = {
  'started_at-desc': 'Most Recent',
  'started_at-asc': 'Oldest First',
  'message_count-desc': 'Most Messages',
  'total_cost-desc': 'Highest Cost',
};

export default function ActiveFilters({
  filters,
  onRemoveFilter,
  onClearAll,
}: ActiveFiltersProps) {
  const { data: projectsData } = useQuery({
    queryKey: ['projects', { limit: 100 }],
    queryFn: () => projectsApi.listProjects({ limit: 100 }),
    enabled: !!filters.projectId,
  });

  const activeFilters: Array<{ key: string; label: string; value: string }> =
    [];

  if (filters.search) {
    activeFilters.push({
      key: 'search',
      label: 'Search',
      value: filters.search,
    });
  }

  if (filters.startDate && filters.endDate) {
    activeFilters.push({
      key: 'dateRange',
      label: 'Date',
      value: `${format(new Date(filters.startDate), 'MMM d, yyyy')} - ${format(
        new Date(filters.endDate),
        'MMM d, yyyy'
      )}`,
    });
  } else if (filters.startDate) {
    activeFilters.push({
      key: 'startDate',
      label: 'After',
      value: format(new Date(filters.startDate), 'MMM d, yyyy'),
    });
  } else if (filters.endDate) {
    activeFilters.push({
      key: 'endDate',
      label: 'Before',
      value: format(new Date(filters.endDate), 'MMM d, yyyy'),
    });
  }

  if (filters.sortBy && filters.sortOrder) {
    const sortKey = `${filters.sortBy}-${filters.sortOrder}`;
    if (sortKey !== 'started_at-desc') {
      activeFilters.push({
        key: 'sort',
        label: 'Sort',
        value: SORT_LABELS[sortKey] || sortKey,
      });
    }
  }

  if (filters.projectId && projectsData) {
    const project = projectsData.items.find((p) => p._id === filters.projectId);
    if (project) {
      activeFilters.push({
        key: 'projectId',
        label: 'Project',
        value: project.name,
      });
    }
  }

  if (activeFilters.length === 0) {
    return null;
  }

  const handleRemove = (key: string) => {
    if (key === 'dateRange') {
      onRemoveFilter('startDate');
      onRemoveFilter('endDate');
    } else if (key === 'sort') {
      onRemoveFilter('sortBy');
      onRemoveFilter('sortOrder');
    } else {
      onRemoveFilter(key);
    }
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {activeFilters.map((filter) => (
        <div
          key={filter.key}
          className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-accent rounded-full"
        >
          <span className="text-muted-foreground">{filter.label}:</span>
          <span className="font-medium">{filter.value}</span>
          <button
            onClick={() => handleRemove(filter.key)}
            className="ml-1 hover:text-destructive transition-colors"
            aria-label={`Remove ${filter.label} filter`}
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
      {activeFilters.length > 1 && (
        <button
          onClick={onClearAll}
          className="text-sm text-muted-foreground hover:text-foreground underline"
        >
          Clear all filters
        </button>
      )}
    </div>
  );
}
