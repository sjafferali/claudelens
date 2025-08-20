import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Folder } from '@/api/types';

interface FolderBreadcrumbProps {
  folders: Folder[];
  selectedFolderId?: string;
  onFolderSelect: (folderId?: string) => void;
  className?: string;
}

export function FolderBreadcrumb({
  folders,
  selectedFolderId,
  onFolderSelect,
  className,
}: FolderBreadcrumbProps) {
  // Build breadcrumb path
  const getBreadcrumbPath = (): (Folder | null)[] => {
    if (!selectedFolderId) {
      return [];
    }

    const path: Folder[] = [];
    let currentFolderId: string | undefined = selectedFolderId;

    while (currentFolderId) {
      const folder = folders.find((f) => f._id === currentFolderId);
      if (folder) {
        path.unshift(folder);
        currentFolderId = folder.parent_id;
      } else {
        break;
      }
    }

    return path;
  };

  const breadcrumbPath = getBreadcrumbPath();

  return (
    <nav
      className={cn(
        'flex items-center gap-1 text-sm text-muted-foreground',
        className
      )}
      aria-label="Folder breadcrumb"
    >
      {/* Home/All Prompts */}
      <button
        onClick={() => onFolderSelect(undefined)}
        className={cn(
          'flex items-center gap-1 px-2 py-1 rounded-md hover:bg-accent hover:text-foreground transition-colors',
          !selectedFolderId && 'bg-accent text-foreground font-medium'
        )}
      >
        <Home className="h-3 w-3" />
        <span>All Prompts</span>
      </button>

      {/* Folder path */}
      {breadcrumbPath.map((folder) => {
        if (!folder) return null;
        return (
          <div key={folder._id} className="flex items-center gap-1">
            <ChevronRight className="h-3 w-3" />
            <button
              onClick={() => onFolderSelect(folder._id)}
              className={cn(
                'px-2 py-1 rounded-md hover:bg-accent hover:text-foreground transition-colors',
                folder._id === selectedFolderId &&
                  'bg-accent text-foreground font-medium'
              )}
            >
              {folder.name}
            </button>
          </div>
        );
      })}

      {/* Show prompt count for current folder */}
      {selectedFolderId && (
        <span className="ml-2 text-xs text-muted-foreground">
          {(() => {
            const currentFolder = folders.find(
              (f) => f._id === selectedFolderId
            );
            return currentFolder
              ? `(${currentFolder.prompt_count} ${
                  currentFolder.prompt_count === 1 ? 'prompt' : 'prompts'
                })`
              : '';
          })()}
        </span>
      )}
    </nav>
  );
}
