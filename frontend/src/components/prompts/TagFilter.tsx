import { useState } from 'react';
import { ChevronDown, ChevronUp, Hash, Check } from 'lucide-react';
import { cn } from '@/utils/cn';

interface TagFilterProps {
  availableTags: Array<{ name: string; count: number }>;
  selectedTags: string[];
  onChange: (tags: string[]) => void;
  isLoading?: boolean;
}

export function TagFilter({
  availableTags,
  selectedTags,
  onChange,
  isLoading = false,
}: TagFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter tags based on search
  const filteredTags = availableTags.filter((tag) =>
    tag.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleTagToggle = (tagName: string) => {
    if (selectedTags.includes(tagName)) {
      onChange(selectedTags.filter((t) => t !== tagName));
    } else {
      onChange([...selectedTags, tagName]);
    }
  };

  const handleSelectAll = () => {
    const visibleTagNames = filteredTags.map((t) => t.name);
    const allSelected = visibleTagNames.every((tag) =>
      selectedTags.includes(tag)
    );

    if (allSelected) {
      // Deselect all visible tags
      onChange(selectedTags.filter((t) => !visibleTagNames.includes(t)));
    } else {
      // Select all visible tags
      const newTags = new Set([...selectedTags, ...visibleTagNames]);
      onChange(Array.from(newTags));
    }
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const visibleSelectedCount = filteredTags.filter((tag) =>
    selectedTags.includes(tag.name)
  ).length;

  if (isLoading) {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Hash className="h-4 w-4" />
          <span className="text-sm font-medium">Tags</span>
        </div>
        <div className="text-xs text-muted-foreground">Loading tags...</div>
      </div>
    );
  }

  if (availableTags.length === 0) {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Hash className="h-4 w-4" />
          <span className="text-sm font-medium">Tags</span>
        </div>
        <div className="text-xs text-muted-foreground">No tags available</div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between hover:bg-accent/50 rounded-md p-2 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Hash className="h-4 w-4" />
          <span className="text-sm font-medium">Tags</span>
          {selectedTags.length > 0 && (
            <span className="text-xs bg-primary text-primary-foreground rounded-full px-2 py-0.5">
              {selectedTags.length}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {isExpanded && (
        <div className="space-y-2 pl-6">
          {/* Search */}
          {availableTags.length > 5 && (
            <input
              type="text"
              placeholder="Search tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-2 py-1 text-sm border rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-primary"
            />
          )}

          {/* Select/Clear All */}
          <div className="flex items-center gap-2 text-xs">
            <button
              onClick={handleSelectAll}
              className="text-primary hover:underline"
            >
              {visibleSelectedCount === filteredTags.length
                ? 'Deselect All'
                : 'Select All'}
            </button>
            {selectedTags.length > 0 && (
              <>
                <span className="text-muted-foreground">•</span>
                <button
                  onClick={handleClearAll}
                  className="text-muted-foreground hover:text-foreground hover:underline"
                >
                  Clear All
                </button>
              </>
            )}
          </div>

          {/* Tag List */}
          <div className="max-h-64 overflow-y-auto space-y-1">
            {filteredTags.length === 0 ? (
              <div className="text-xs text-muted-foreground py-2">
                No tags match "{searchQuery}"
              </div>
            ) : (
              filteredTags.map((tag) => {
                const isSelected = selectedTags.includes(tag.name);
                return (
                  <label
                    key={tag.name}
                    className={cn(
                      'flex items-center gap-2 px-2 py-1 rounded-md cursor-pointer transition-colors',
                      isSelected
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent/50'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleTagToggle(tag.name)}
                      className="sr-only"
                    />
                    <div
                      className={cn(
                        'w-4 h-4 rounded border flex items-center justify-center',
                        isSelected
                          ? 'bg-primary border-primary'
                          : 'border-input'
                      )}
                    >
                      {isSelected && (
                        <Check className="h-3 w-3 text-primary-foreground" />
                      )}
                    </div>
                    <span className="text-sm flex-1">{tag.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {tag.count}
                    </span>
                  </label>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
