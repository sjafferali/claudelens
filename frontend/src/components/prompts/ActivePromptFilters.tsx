import { X, Hash, Star, Folder } from 'lucide-react';

interface ActivePromptFiltersProps {
  filters: {
    search?: string;
    selectedTags?: string[];
    starredOnly?: boolean;
    folderId?: string;
    folderName?: string;
  };
  onRemoveFilter: (filterKey: string, value?: string) => void;
  onClearAll: () => void;
}

export function ActivePromptFilters({
  filters,
  onRemoveFilter,
  onClearAll,
}: ActivePromptFiltersProps) {
  const activeFilters: Array<{
    key: string;
    label: string;
    value: string;
    icon?: React.ReactNode;
  }> = [];

  // Search filter
  if (filters.search) {
    activeFilters.push({
      key: 'search',
      label: 'Search',
      value: filters.search,
    });
  }

  // Tag filters
  if (filters.selectedTags && filters.selectedTags.length > 0) {
    filters.selectedTags.forEach((tag) => {
      activeFilters.push({
        key: 'tag',
        label: 'Tag',
        value: tag,
        icon: <Hash className="h-3 w-3" />,
      });
    });
  }

  // Starred filter
  if (filters.starredOnly) {
    activeFilters.push({
      key: 'starredOnly',
      label: 'Starred',
      value: 'Yes',
      icon: <Star className="h-3 w-3" />,
    });
  }

  // Folder filter
  if (filters.folderId && filters.folderName) {
    activeFilters.push({
      key: 'folder',
      label: 'Folder',
      value: filters.folderName,
      icon: <Folder className="h-3 w-3" />,
    });
  }

  if (activeFilters.length === 0) {
    return null;
  }

  const handleRemove = (key: string, value?: string) => {
    if (key === 'tag' && value) {
      // Remove specific tag
      onRemoveFilter('tag', value);
    } else {
      onRemoveFilter(key);
    }
  };

  return (
    <div className="flex items-center gap-2 flex-wrap p-3 bg-accent/30 rounded-lg">
      <span className="text-sm text-muted-foreground">Active filters:</span>
      {activeFilters.map((filter, index) => (
        <div
          key={`${filter.key}-${filter.value}-${index}`}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-sm bg-background border rounded-full hover:bg-accent/50 transition-colors"
        >
          {filter.icon}
          <span className="text-muted-foreground">{filter.label}:</span>
          <span className="font-medium">{filter.value}</span>
          <button
            onClick={() => handleRemove(filter.key, filter.value)}
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
          className="text-sm text-muted-foreground hover:text-foreground underline ml-2"
        >
          Clear all
        </button>
      )}
    </div>
  );
}
