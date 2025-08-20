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
  useUpdatePrompt,
} from '@/hooks/usePrompts';
import { Folder as FolderType } from '@/api/types';
import { toast } from 'react-hot-toast';

interface FolderTreeProps {
  selectedFolderId?: string;
  onFolderSelect: (folderId?: string) => void;
  className?: string;
  onPromptDrop?: (promptId: string, folderId?: string) => void;
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
  expandedFolders: Set<string>;
  newFolderParentId?: string;
  newFolderName?: string;
  onNewFolderNameChange?: (name: string) => void;
  onNewFolderSubmit?: () => void;
  onNewFolderCancel?: () => void;
  dragOverFolderId?: string | null;
  onDragOver?: (e: React.DragEvent, folderId: string) => void;
  onDragLeave?: (e: React.DragEvent) => void;
  onDrop?: (e: React.DragEvent, folderId: string) => void;
}

export function FolderTree({
  selectedFolderId,
  onFolderSelect,
  className,
  onPromptDrop,
}: FolderTreeProps) {
  const { data: folders, isLoading } = useFolders();
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set()
  );
  const [newFolderParentId, setNewFolderParentId] = useState<
    string | undefined
  >(undefined);
  const [newFolderName, setNewFolderName] = useState('');

  const createFolder = useCreateFolder();
  const deleteFolder = useDeleteFolder();
  const updateFolder = useUpdateFolder();
  const updatePrompt = useUpdatePrompt();
  const [dragOverFolderId, setDragOverFolderId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className={cn('space-y-1', className)}>
        <div className="h-8 bg-muted rounded animate-pulse" />
        <div className="h-8 bg-muted rounded animate-pulse ml-4" />
        <div className="h-8 bg-muted rounded animate-pulse ml-4" />
        <div className="h-8 bg-muted rounded animate-pulse ml-8" />
      </div>
    );
  }

  if (!folders || folders.length === 0) {
    return (
      <div className={cn('space-y-1', className)}>
        {/* All Prompts */}
        <div
          onClick={() => onFolderSelect(undefined)}
          className={cn(
            'flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent transition-colors',
            !selectedFolderId && 'bg-accent text-accent-foreground'
          )}
        >
          <Folder className="h-4 w-4" />
          <span>All Prompts</span>
        </div>

        {/* Create First Folder */}
        <button
          onClick={() => handleCreateFolder()}
          className="flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent text-muted-foreground hover:text-foreground w-full text-left"
        >
          <FolderPlus className="h-4 w-4" />
          <span>Create your first folder</span>
        </button>
      </div>
    );
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

  const handleCreateFolder = (parentId?: string) => {
    setNewFolderParentId(parentId || 'root');
    setNewFolderName('New Folder');
    if (parentId) {
      setExpandedFolders((prev) => new Set([...prev, parentId]));
    }
  };

  const handleCreateFolderSubmit = async () => {
    const name = newFolderName.trim();
    if (!name) {
      setNewFolderParentId(undefined);
      setNewFolderName('');
      return;
    }

    try {
      const result = await createFolder.mutateAsync({
        name,
        parent_id:
          newFolderParentId === 'root'
            ? undefined
            : newFolderParentId || undefined,
      });
      setNewFolderParentId(undefined);
      setNewFolderName('');

      // Auto-select the new folder
      if (result && result._id) {
        onFolderSelect(result._id);
      }
    } catch (error) {
      console.error('Failed to create folder:', error);
      toast.error('Failed to create folder');
    }
  };

  const handleCancelNewFolder = () => {
    setNewFolderParentId(undefined);
    setNewFolderName('');
  };

  const handleRenameFolder = async (folderId: string, name: string) => {
    if (!name.trim()) return;

    try {
      await updateFolder.mutateAsync({
        folderId,
        folderData: { name: name.trim() },
      });
      toast.success('Folder renamed successfully');
    } catch (error) {
      console.error('Failed to rename folder:', error);
      toast.error('Failed to rename folder');
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    const folder = folders?.find((f) => f._id === folderId);
    const folderName = folder?.name || 'this folder';
    const promptCount = folder?.prompt_count || 0;

    const message =
      promptCount > 0
        ? `Are you sure you want to delete "${folderName}"? ${promptCount} prompt${promptCount === 1 ? '' : 's'} will be moved to the root folder.`
        : `Are you sure you want to delete "${folderName}"?`;

    if (window.confirm(message)) {
      try {
        await deleteFolder.mutateAsync({ folderId });
        if (selectedFolderId === folderId) {
          onFolderSelect(undefined);
        }
        toast.success(`Folder "${folderName}" deleted`);
      } catch (error) {
        console.error('Failed to delete folder:', error);
        toast.error('Failed to delete folder');
      }
    }
  };

  // Build folder tree structure
  const buildFolderTree = (parentId?: string): FolderType[] => {
    return folders.filter((folder) => folder.parent_id === parentId);
  };

  const rootFolders = buildFolderTree();

  const handleDragOver = (e: React.DragEvent, folderId?: string) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverFolderId(folderId || 'root');
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only clear if we're leaving the element entirely
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragOverFolderId(null);
    }
  };

  const handleDrop = async (e: React.DragEvent, folderId?: string) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverFolderId(null);

    const promptId = e.dataTransfer.getData('promptId');
    if (!promptId) return;

    if (onPromptDrop) {
      onPromptDrop(promptId, folderId);
    } else {
      // Default implementation: update prompt's folder
      try {
        await updatePrompt.mutateAsync({
          promptId,
          promptData: { folder_id: folderId },
        });
        toast.success(`Prompt moved to ${folderId ? 'folder' : 'root'}`);
      } catch (error) {
        console.error('Failed to move prompt:', error);
        toast.error('Failed to move prompt');
      }
    }
  };

  return (
    <div className={cn('space-y-1', className)}>
      {/* All Prompts */}
      <div
        onClick={() => onFolderSelect(undefined)}
        onDragOver={(e) => handleDragOver(e, undefined)}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(e, undefined)}
        className={cn(
          'flex items-center gap-2 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent transition-colors',
          !selectedFolderId && 'bg-accent text-accent-foreground',
          dragOverFolderId === 'root' && 'ring-2 ring-primary bg-primary/10'
        )}
      >
        <Folder className="h-4 w-4" />
        <span>All Prompts</span>
      </div>

      {/* Root level new folder (above existing folders) */}
      {newFolderParentId === 'root' && (
        <div className="flex items-center gap-2 px-2 py-1.5 text-sm rounded-md bg-accent">
          <Folder className="h-4 w-4" />
          <input
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onBlur={handleCreateFolderSubmit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleCreateFolderSubmit();
              } else if (e.key === 'Escape') {
                handleCancelNewFolder();
              }
            }}
            className="flex-1 bg-background border rounded px-1 py-0.5 text-xs"
            autoFocus
            placeholder="Enter folder name"
          />
        </div>
      )}

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
          expandedFolders={expandedFolders}
          newFolderParentId={newFolderParentId}
          newFolderName={newFolderName}
          onNewFolderNameChange={setNewFolderName}
          onNewFolderSubmit={handleCreateFolderSubmit}
          onNewFolderCancel={handleCancelNewFolder}
          dragOverFolderId={dragOverFolderId}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
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
  expandedFolders,
  newFolderParentId,
  newFolderName,
  onNewFolderNameChange,
  onNewFolderSubmit,
  onNewFolderCancel,
  dragOverFolderId,
  onDragOver,
  onDragLeave,
  onDrop,
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
          'flex items-center gap-1 px-2 py-1.5 text-sm rounded-md cursor-pointer hover:bg-accent relative group transition-colors',
          selectedFolderId === folder._id && 'bg-accent text-accent-foreground',
          dragOverFolderId === folder._id && 'ring-2 ring-primary bg-primary/10'
        )}
        style={{ paddingLeft: `${(level + 1) * 12 + 8}px` }}
        onDragOver={(e) => onDragOver?.(e, folder._id)}
        onDragLeave={(e) => onDragLeave?.(e)}
        onDrop={(e) => onDrop?.(e, folder._id)}
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
          {folder.prompt_count > 0 && (
            <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
              {folder.prompt_count}
            </span>
          )}
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
      {isExpanded && (
        <div>
          {/* New folder input for this folder */}
          {newFolderParentId === folder._id && (
            <div
              className="flex items-center gap-1 px-2 py-1.5 text-sm rounded-md bg-accent"
              style={{ paddingLeft: `${(level + 2) * 12 + 8}px` }}
            >
              <Folder className="h-4 w-4 flex-shrink-0" />
              <input
                value={newFolderName}
                onChange={(e) => onNewFolderNameChange?.(e.target.value)}
                onBlur={() => onNewFolderSubmit?.()}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    onNewFolderSubmit?.();
                  } else if (e.key === 'Escape') {
                    onNewFolderCancel?.();
                  }
                }}
                className="flex-1 bg-background border rounded px-1 py-0.5 text-xs"
                autoFocus
                placeholder="Enter folder name"
              />
            </div>
          )}

          {childFolders.map((childFolder) => {
            const isChildExpanded = expandedFolders.has(childFolder._id);
            return (
              <FolderNode
                key={childFolder._id}
                folder={childFolder}
                allFolders={allFolders}
                selectedFolderId={selectedFolderId}
                onFolderSelect={onFolderSelect}
                level={level + 1}
                isExpanded={isChildExpanded}
                onToggleExpand={onToggleExpand}
                onCreateFolder={onCreateFolder}
                onRenameFolder={onRenameFolder}
                onDeleteFolder={onDeleteFolder}
                expandedFolders={expandedFolders}
                newFolderParentId={newFolderParentId}
                newFolderName={newFolderName}
                onNewFolderNameChange={onNewFolderNameChange}
                onNewFolderSubmit={onNewFolderSubmit}
                onNewFolderCancel={onNewFolderCancel}
                dragOverFolderId={dragOverFolderId}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
              />
            );
          })}
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
