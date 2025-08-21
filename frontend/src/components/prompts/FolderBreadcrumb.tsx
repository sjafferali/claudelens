import { ChevronRight, Home, Folder as FolderIcon } from 'lucide-react';
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
  const currentFolder = selectedFolderId
    ? folders.find((f) => f._id === selectedFolderId)
    : null;

  return (
    <div className={cn('space-y-2', className)}>
      {/* Breadcrumb Navigation */}
      <nav
        className="flex items-center gap-1 text-sm text-muted-foreground flex-wrap"
        aria-label="Folder breadcrumb"
      >
        {/* Home/All Prompts */}
        <button
          onClick={() => onFolderSelect(undefined)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-md hover:bg-accent hover:text-foreground transition-all',
            !selectedFolderId &&
              'bg-primary/10 text-primary font-medium shadow-sm'
          )}
        >
          <Home className="h-3.5 w-3.5" />
          <span>All Prompts</span>
        </button>

        {/* Folder path */}
        {breadcrumbPath.map((folder, index) => {
          if (!folder) return null;
          const isLast = index === breadcrumbPath.length - 1;
          return (
            <div key={folder._id} className="flex items-center gap-1">
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
              <button
                onClick={() => onFolderSelect(folder._id)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-md hover:bg-accent hover:text-foreground transition-all',
                  isLast && 'bg-primary/10 text-primary font-medium shadow-sm'
                )}
              >
                <FolderIcon className="h-3.5 w-3.5" />
                <span>{folder.name}</span>
                {isLast && folder.prompt_count > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 bg-primary/20 text-primary text-xs rounded-full">
                    {folder.prompt_count}
                  </span>
                )}
              </button>
            </div>
          );
        })}
      </nav>

      {/* Current Folder Info */}
      {currentFolder && (
        <div className="flex items-center gap-4 text-sm text-muted-foreground px-1">
          <span className="flex items-center gap-1">
            <span className="font-medium">{currentFolder.prompt_count}</span>
            <span>
              {currentFolder.prompt_count === 1 ? 'prompt' : 'prompts'} in this
              folder
            </span>
          </span>
          {currentFolder.createdAt && (
            <span className="text-xs">
              Created {new Date(currentFolder.createdAt).toLocaleDateString()}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
