import { useState, useEffect, useCallback } from 'react';
import { ChevronDown, ChevronUp, Calendar, Filter } from 'lucide-react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { projectsApi } from '@/api/projects';
import { useQuery } from '@tanstack/react-query';

interface SessionFiltersProps {
  filters: {
    startDate?: string;
    endDate?: string;
    sortBy?: 'started_at' | 'ended_at' | 'message_count' | 'total_cost';
    sortOrder?: 'asc' | 'desc';
    projectId?: string;
  };
  onChange: (filters: Partial<SessionFiltersProps['filters']>) => void;
  hideProjectFilter?: boolean;
}

const DATE_PRESETS = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 3 months', value: 90 },
  { label: 'All time', value: null },
];

const SORT_OPTIONS: Array<{
  label: string;
  value: {
    sortBy: 'started_at' | 'ended_at' | 'message_count' | 'total_cost';
    sortOrder: 'asc' | 'desc';
  };
}> = [
  { label: 'Most Recent', value: { sortBy: 'started_at', sortOrder: 'desc' } },
  { label: 'Oldest First', value: { sortBy: 'started_at', sortOrder: 'asc' } },
  {
    label: 'Most Messages',
    value: { sortBy: 'message_count', sortOrder: 'desc' },
  },
  { label: 'Highest Cost', value: { sortBy: 'total_cost', sortOrder: 'desc' } },
];

export default function SessionFilters({
  filters,
  onChange,
  hideProjectFilter = false,
}: SessionFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState(filters);

  const { data: projectsData } = useQuery({
    queryKey: ['projects', { limit: 100 }],
    queryFn: () => projectsApi.listProjects({ limit: 100 }),
    enabled: !hideProjectFilter,
  });

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleDatePreset = useCallback(
    (days: number | null) => {
      if (days === null) {
        const newFilters = { ...localFilters };
        delete newFilters.startDate;
        delete newFilters.endDate;
        setLocalFilters(newFilters);
        onChange(newFilters);
      } else {
        const endDate = endOfDay(new Date());
        const startDate = startOfDay(subDays(endDate, days));
        const newFilters = {
          ...localFilters,
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString(),
        };
        setLocalFilters(newFilters);
        onChange(newFilters);
      }
    },
    [localFilters, onChange]
  );

  const handleSortChange = useCallback(
    (sortOption: {
      sortBy: SessionFiltersProps['filters']['sortBy'];
      sortOrder: SessionFiltersProps['filters']['sortOrder'];
    }) => {
      const newFilters = {
        ...localFilters,
        sortBy: sortOption.sortBy,
        sortOrder: sortOption.sortOrder,
      };
      setLocalFilters(newFilters);
      onChange(newFilters);
    },
    [localFilters, onChange]
  );

  const handleProjectChange = useCallback(
    (projectId: string) => {
      const newFilters = { ...localFilters };
      if (projectId === 'all') {
        delete newFilters.projectId;
      } else {
        newFilters.projectId = projectId;
      }
      setLocalFilters(newFilters);
      onChange(newFilters);
    },
    [localFilters, onChange]
  );

  const handleDateChange = useCallback(
    (field: 'startDate' | 'endDate', value: string) => {
      const newFilters = { ...localFilters };
      if (value) {
        const date =
          field === 'startDate'
            ? startOfDay(new Date(value))
            : endOfDay(new Date(value));
        newFilters[field] = date.toISOString();
      } else {
        delete newFilters[field];
      }
      setLocalFilters(newFilters);
      onChange(newFilters);
    },
    [localFilters, onChange]
  );

  const currentSort = SORT_OPTIONS.find(
    (opt) =>
      opt.value.sortBy === (localFilters.sortBy || 'started_at') &&
      opt.value.sortOrder === (localFilters.sortOrder || 'desc')
  );

  return (
    <div className="border rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-accent/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span className="font-medium">Filters</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Date Range</label>
            <div className="flex flex-wrap gap-2 mb-3">
              {DATE_PRESETS.map((preset) => (
                <button
                  key={preset.label}
                  onClick={() => handleDatePreset(preset.value)}
                  className="px-3 py-1 text-sm border rounded-md hover:bg-accent transition-colors"
                >
                  {preset.label}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Start Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
                  <input
                    type="date"
                    value={
                      localFilters.startDate
                        ? format(new Date(localFilters.startDate), 'yyyy-MM-dd')
                        : ''
                    }
                    onChange={(e) =>
                      handleDateChange('startDate', e.target.value)
                    }
                    className="w-full pl-8 pr-2 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  End Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
                  <input
                    type="date"
                    value={
                      localFilters.endDate
                        ? format(new Date(localFilters.endDate), 'yyyy-MM-dd')
                        : ''
                    }
                    onChange={(e) =>
                      handleDateChange('endDate', e.target.value)
                    }
                    className="w-full pl-8 pr-2 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Sort By</label>
            <select
              value={`${currentSort?.value.sortBy}-${currentSort?.value.sortOrder}`}
              onChange={(e) => {
                const option = SORT_OPTIONS.find(
                  (opt) =>
                    `${opt.value.sortBy}-${opt.value.sortOrder}` ===
                    e.target.value
                );
                if (option) {
                  handleSortChange(option.value);
                }
              }}
              className="w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              {SORT_OPTIONS.map((option) => (
                <option
                  key={`${option.value.sortBy}-${option.value.sortOrder}`}
                  value={`${option.value.sortBy}-${option.value.sortOrder}`}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {!hideProjectFilter && projectsData && (
            <div>
              <label className="block text-sm font-medium mb-2">Project</label>
              <select
                value={localFilters.projectId || 'all'}
                onChange={(e) => handleProjectChange(e.target.value)}
                className="w-full px-3 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="all">All Projects</option>
                {projectsData.items.map((project) => (
                  <option key={project._id} value={project._id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
