import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderPlus,
  MoreHorizontal,
  Trash2,
  Edit3,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import {
  useFolders,
  useCreateFolder,
  useDeleteFolder,
  useUpdateFolder,
} from '@/hooks/usePrompts';
import { Folder as FolderType } from '@/api/types';

interface FolderTreeProps {
  selectedFolderId?: string;
  onFolderSelect: (folderId?: string) => void;
  className?: string;
}

interface FolderNodeProps {
  folder: FolderType;
  allFolders: FolderType[];
  selectedFolderId?: string;
  onFolderSelect: (folderId?: string) => void;
  level: number;
  isExpanded: boolean;
  onToggleExpand: (folderId: string) => void;
  onCreateFolder: (parentId: string) => void;
  onRenameFolder: (folderId: string, name: string) => void;
  onDeleteFolder: (folderId: string) => void;
}

export function FolderTree({
  selectedFolderId,
  onFolderSelect,
  className,
}: FolderTreeProps) {
  const { data: folders, isLoading } = useFolders();
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set()
  );

  const createFolder = useCreateFolder();
  const deleteFolder = useDeleteFolder();
  const updateFolder = useUpdateFolder();

  if (isLoading) {
    return (
      <div className={cn('space-y-1', className)}>
        <div className="h-6 bg-muted rounded animate-pulse" />
        <div className="h-6 bg-muted rounded animate-pulse ml-4" />
        <div className="h-6 bg-muted rounded animate-pulse ml-8" />
      </div>
    );
  }

  if (!folders) {
    return null;
  }

  const toggleExpand = (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  const handleCreateFolder = async (parentId?: string) => {
    try {
      await createFolder.mutateAsync({
        name: 'New Folder',
        parent_id: parentId,
      });
      if (parentId) {
        setExpandedFolders((prev) => new Set([...prev, parentId]));
      }
    } catch (error) {
      console.error('Failed to create folder:', error);
    }
  };

  const handleRenameFolder = async (folderId: string, name: string) => {
    if (!name.trim()) return;

    try {
      await updateFolder.mutateAsync({
        folderId,
        folderData: { name: name.trim() },
      });
    } catch (error) {
      console.error('Failed to rename folder:', error);
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (
      window.confirm(
        'Are you sure you want to delete this folder? All prompts in this folder will be moved to the root.'
      )
    ) {
      try {
        await deleteFolder.mutateAsync({ folderId });
        if (selectedFolderId === folderId) {
          onFolderSelect(undefined);
        }
      } catch (error) {
        console.error('Failed to delete folder:', error);
      }
    }
  };

  // Build folder tree structure
  const buildFolderTree = (parentId?: string): FolderType[] => {
    return folders.filter((folder) => folder.parent_id === parentId);
  };

  const rootFolders = buildFolderTree();

  return (
    <div className={cn('space-y-1', className)}>
      {/* All Prompts */}
      <div
        onClick={() => onFolderSelect(undefined)}
        className={cn(
          'flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent',
          !selectedFolderId && 'bg-accent text-accent-foreground'
        )}
      >
        <Folder className="h-4 w-4" />
        <span>All Prompts</span>
      </div>

      {/* Folder Tree */}
      {rootFolders.map((folder) => (
        <FolderNode
          key={folder._id}
          folder={folder}
          allFolders={folders}
          selectedFolderId={selectedFolderId}
          onFolderSelect={onFolderSelect}
          level={0}
          isExpanded={expandedFolders.has(folder._id)}
          onToggleExpand={toggleExpand}
          onCreateFolder={handleCreateFolder}
          onRenameFolder={handleRenameFolder}
          onDeleteFolder={handleDeleteFolder}
        />
      ))}

      {/* Create Root Folder */}
      <div
        onClick={() => handleCreateFolder()}
        className="flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent text-muted-foreground hover:text-foreground"
      >
        <FolderPlus className="h-4 w-4" />
        <span>New Folder</span>
      </div>
    </div>
  );
}

function FolderNode({
  folder,
  allFolders,
  selectedFolderId,
  onFolderSelect,
  level,
  isExpanded,
  onToggleExpand,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
}: FolderNodeProps) {
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [editingName, setEditingName] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const childFolders = allFolders.filter((f) => f.parent_id === folder._id);
  const hasChildren = childFolders.length > 0;

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowContextMenu(!showContextMenu);
  };

  const startEditing = () => {
    setEditingName(folder.name);
    setIsEditing(true);
    setShowContextMenu(false);
  };

  const handleSubmitEdit = () => {
    if (editingName.trim() && editingName.trim() !== folder.name) {
      onRenameFolder(folder._id, editingName.trim());
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmitEdit();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditingName('');
    }
  };

  return (
    <div>
      <div
        className={cn(
          'flex items-center gap-1 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent relative group',
          selectedFolderId === folder._id && 'bg-accent text-accent-foreground'
        )}
        style={{ paddingLeft: `${(level + 1) * 12 + 8}px` }}
      >
        {/* Expand/Collapse Button */}
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand(folder._id);
            }}
            className="p-0.5 hover:bg-accent-foreground/10 rounded"
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
        )}

        {/* Folder Icon and Name */}
        <div
          onClick={() => onFolderSelect(folder._id)}
          className="flex items-center gap-2 flex-1 min-w-0"
        >
          <Folder className="h-4 w-4 flex-shrink-0" />
          {isEditing ? (
            <input
              value={editingName}
              onChange={(e) => setEditingName(e.target.value)}
              onBlur={handleSubmitEdit}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-background border rounded px-1 py-0.5 text-xs"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span className="truncate flex-1">{folder.name}</span>
          )}
          <span className="text-xs text-muted-foreground">
            {folder.prompt_count}
          </span>
        </div>

        {/* Context Menu Button */}
        <button
          onClick={handleContextMenu}
          className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-accent-foreground/10 rounded"
        >
          <MoreHorizontal className="h-3 w-3" />
        </button>

        {/* Context Menu */}
        {showContextMenu && (
          <div className="absolute right-0 top-8 z-50 min-w-32 bg-popover border rounded-md shadow-md py-1">
            <button
              onClick={() => onCreateFolder(folder._id)}
              className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2"
            >
              <FolderPlus className="h-3 w-3" />
              New Subfolder
            </button>
            <button
              onClick={startEditing}
              className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2"
            >
              <Edit3 className="h-3 w-3" />
              Rename
            </button>
            <button
              onClick={() => {
                onDeleteFolder(folder._id);
                setShowContextMenu(false);
              }}
              className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2 text-destructive"
            >
              <Trash2 className="h-3 w-3" />
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Child Folders */}
      {isExpanded && hasChildren && (
        <div>
          {childFolders.map((childFolder) => (
            <FolderNode
              key={childFolder._id}
              folder={childFolder}
              allFolders={allFolders}
              selectedFolderId={selectedFolderId}
              onFolderSelect={onFolderSelect}
              level={level + 1}
              isExpanded={false}
              onToggleExpand={onToggleExpand}
              onCreateFolder={onCreateFolder}
              onRenameFolder={onRenameFolder}
              onDeleteFolder={onDeleteFolder}
            />
          ))}
        </div>
      )}

      {/* Click outside to close context menu */}
      {showContextMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowContextMenu(false)}
        />
      )}
    </div>
  );
}
