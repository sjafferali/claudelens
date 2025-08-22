import * as React from 'react';
import { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import {
  backupApi,
  CreateRestoreRequest,
  CreateRestoreResponse,
} from '@/api/backupApi';
import {
  RotateCcw,
  Database,
  Folder,
  MessageSquare,
  ChevronRight,
  ChevronDown,
  Square,
  CheckSquare,
  MinusSquare,
  Search,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '@/utils/cn';

interface SelectiveRestoreDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  backupId: string;
  onRestoreStarted?: (jobId: string) => void;
}

interface TreeNode {
  id: string;
  name: string;
  type: 'project' | 'session' | 'message';
  children?: TreeNode[];
  metadata?: Record<string, unknown>;
  count?: number;
  selected?: boolean;
  expanded?: boolean;
  partiallySelected?: boolean;
}

export const SelectiveRestoreDialog: React.FC<SelectiveRestoreDialogProps> = ({
  open,
  onOpenChange,
  backupId,
  onRestoreStarted,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [conflictResolution, setConflictResolution] = useState<
    'skip' | 'overwrite' | 'rename' | 'merge'
  >('skip');

  // Load backup preview
  const {
    data: preview,
    isLoading: previewLoading,
    error: previewError,
  } = useQuery({
    queryKey: ['backup-preview-selective', backupId],
    queryFn: () => backupApi.previewBackup(backupId),
    enabled: open && !!backupId,
  });

  // Build tree structure from preview data
  useEffect(() => {
    if (preview?.preview_data) {
      const tree: TreeNode[] = [];

      // Process collections from preview
      Object.entries(preview.preview_data.collections).forEach(
        ([collection, data]) => {
          if (collection === 'projects' && data.sample_data) {
            // Add projects as top-level nodes
            (data.sample_data as Array<Record<string, unknown>>).forEach(
              (project) => {
                const projectNode: TreeNode = {
                  id: `project_${project._id}`,
                  name: (project.name as string) || 'Unnamed Project',
                  type: 'project',
                  metadata: project,
                  children: [],
                };
                tree.push(projectNode);
              }
            );
          }
        }
      );

      // Add sessions under projects
      if (preview.preview_data.collections.sessions?.sample_data) {
        (
          preview.preview_data.collections.sessions.sample_data as Array<
            Record<string, unknown>
          >
        ).forEach((session) => {
          const projectId = session.projectId;
          const projectNode = tree.find((n) => n.id === `project_${projectId}`);

          const sessionNode: TreeNode = {
            id: `session_${session._id}`,
            name:
              (session.title as string) ||
              (session.summary as string) ||
              'Unnamed Session',
            type: 'session',
            metadata: session,
            count: (session.messageCount as number) || 0,
          };

          if (projectNode) {
            if (!projectNode.children) projectNode.children = [];
            projectNode.children.push(sessionNode);
          } else {
            // Orphaned session - add to root
            tree.push(sessionNode);
          }
        });
      }

      setTreeData(tree);
    }
  }, [preview]);

  // Restore mutation
  const restoreMutation = useMutation({
    mutationFn: (request: CreateRestoreRequest) =>
      backupApi.createRestore(request),
    onSuccess: (response: CreateRestoreResponse) => {
      toast.success(
        response.message || 'Selective restore started successfully'
      );
      onRestoreStarted?.(response.job_id);
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      const errorMessage =
        (error as Error & { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail || 'Failed to start selective restore';
      toast.error(errorMessage);
    },
  });

  const toggleNodeExpansion = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const toggleNodeSelection = (node: TreeNode, checked: boolean) => {
    const newSelected = new Set(selectedItems);

    const updateSelection = (n: TreeNode, selected: boolean) => {
      if (selected) {
        newSelected.add(n.id);
      } else {
        newSelected.delete(n.id);
      }

      // Update children recursively
      if (n.children) {
        n.children.forEach((child) => updateSelection(child, selected));
      }
    };

    updateSelection(node, checked);
    setSelectedItems(newSelected);
  };

  const isNodeSelected = (node: TreeNode): boolean => {
    return selectedItems.has(node.id);
  };

  const isNodePartiallySelected = (node: TreeNode): boolean => {
    if (!node.children || node.children.length === 0) return false;

    const childrenSelected = node.children.filter(
      (child) => isNodeSelected(child) || isNodePartiallySelected(child)
    );

    return (
      childrenSelected.length > 0 &&
      childrenSelected.length < node.children.length
    );
  };

  const renderTreeNode = (node: TreeNode, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const isSelected = isNodeSelected(node);
    const isPartiallySelected = isNodePartiallySelected(node);
    const hasChildren = node.children && node.children.length > 0;

    // Filter by search term
    if (
      searchTerm &&
      !node.name.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      // Check if any children match
      if (
        !hasChildren ||
        !node.children?.some((child) =>
          child.name.toLowerCase().includes(searchTerm.toLowerCase())
        )
      ) {
        return null;
      }
    }

    const getIcon = () => {
      switch (node.type) {
        case 'project':
          return <Folder className="w-4 h-4" />;
        case 'session':
          return <MessageSquare className="w-4 h-4" />;
        default:
          return <Database className="w-4 h-4" />;
      }
    };

    const getCheckbox = () => {
      if (isPartiallySelected) {
        return <MinusSquare className="w-4 h-4 text-blue-600" />;
      } else if (isSelected) {
        return <CheckSquare className="w-4 h-4 text-blue-600" />;
      } else {
        return <Square className="w-4 h-4 text-gray-400" />;
      }
    };

    return (
      <div key={node.id}>
        <div
          className={cn(
            'flex items-center gap-2 py-1.5 px-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer',
            isSelected && 'bg-blue-50 dark:bg-blue-900/20'
          )}
          style={{ paddingLeft: `${level * 24 + 8}px` }}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleNodeExpansion(node.id);
              }}
              className="p-0.5"
            >
              {isExpanded ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronRight className="w-3 h-3" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-4" />}

          <button
            onClick={() => toggleNodeSelection(node, !isSelected)}
            className="p-0.5"
          >
            {getCheckbox()}
          </button>

          <div className="flex items-center gap-2 flex-1">
            {getIcon()}
            <span className="text-sm">{node.name}</span>
            {node.count !== undefined && (
              <span className="text-xs text-gray-500">({node.count})</span>
            )}
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children?.map((child) => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const handleRestore = () => {
    if (!preview?.can_restore) {
      toast.error('This backup cannot be restored');
      return;
    }

    if (selectedItems.size === 0) {
      toast.error('Please select at least one item to restore');
      return;
    }

    // Extract selected projects and sessions
    const selectedProjects: string[] = [];
    const selectedSessions: string[] = [];

    selectedItems.forEach((id) => {
      if (id.startsWith('project_')) {
        selectedProjects.push(id.replace('project_', ''));
      } else if (id.startsWith('session_')) {
        selectedSessions.push(id.replace('session_', ''));
      }
    });

    const request: CreateRestoreRequest = {
      backup_id: backupId,
      mode: 'selective',
      conflict_resolution: conflictResolution,
      selections: {
        collections: [],
        criteria: {
          project_ids: selectedProjects,
          session_ids: selectedSessions,
        },
      },
    };

    restoreMutation.mutate(request);
  };

  const selectAll = () => {
    const allIds = new Set<string>();
    const collectIds = (nodes: TreeNode[]) => {
      nodes.forEach((node) => {
        allIds.add(node.id);
        if (node.children) {
          collectIds(node.children);
        }
      });
    };
    collectIds(treeData);
    setSelectedItems(allIds);
  };

  const deselectAll = () => {
    setSelectedItems(new Set());
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5" />
            Selective Restore
          </DialogTitle>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Select specific projects and sessions to restore from the backup
          </p>
        </DialogHeader>

        {previewLoading ? (
          <div className="py-8">
            <Loading />
          </div>
        ) : previewError ? (
          <div className="text-center text-red-500 py-8">
            Failed to load backup preview
          </div>
        ) : preview ? (
          <div className="flex-1 flex flex-col gap-4 min-h-0">
            {/* Search and filters */}
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search items..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800"
                />
              </div>
              <Button onClick={selectAll} variant="outline" size="sm">
                Select All
              </Button>
              <Button onClick={deselectAll} variant="outline" size="sm">
                Deselect All
              </Button>
            </div>

            {/* Selected count */}
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''}{' '}
              selected
            </div>

            {/* Tree view */}
            <div className="flex-1 border rounded-lg p-2 overflow-y-auto min-h-[300px]">
              {treeData.length > 0 ? (
                treeData.map((node) => renderTreeNode(node))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Database className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No items available in this backup</p>
                </div>
              )}
            </div>

            {/* Conflict resolution */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Conflict Resolution
              </label>
              <select
                value={conflictResolution}
                onChange={(e) =>
                  setConflictResolution(
                    e.target.value as 'skip' | 'overwrite' | 'rename' | 'merge'
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
              >
                <option value="skip">Skip Existing</option>
                <option value="overwrite">Overwrite Existing</option>
                <option value="rename">Rename Duplicates</option>
                <option value="merge">Merge Data</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                How to handle conflicts when restoring data that already exists
              </p>
            </div>
          </div>
        ) : null}

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleRestore}
            disabled={
              previewLoading ||
              !preview?.can_restore ||
              restoreMutation.isPending ||
              selectedItems.size === 0
            }
          >
            {restoreMutation.isPending ? (
              <>
                <Loading className="mr-2 h-4 w-4" />
                Starting Restore...
              </>
            ) : (
              <>
                <RotateCcw className="mr-2 h-4 w-4" />
                Restore Selected Items
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
