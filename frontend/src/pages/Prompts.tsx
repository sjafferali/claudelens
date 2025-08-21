import { useParams, useNavigate } from 'react-router-dom';
import { useState, useMemo, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  ConfirmDialog,
} from '@/components/common';
import {
  usePrompts,
  usePrompt,
  useDeletePrompt,
  useUpdatePrompt,
  usePromptTags,
} from '@/hooks/usePrompts';
import { formatDistanceToNow } from 'date-fns';
import {
  Loader2,
  Search,
  Grid3X3,
  List,
  Plus,
  Star,
  Filter,
  SortAsc,
  SortDesc,
  Play,
  Hash,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { Prompt } from '@/api/types';
import { FolderTree } from '@/components/prompts/FolderTree';
import { FolderBreadcrumb } from '@/components/prompts/FolderBreadcrumb';
import { PromptCard } from '@/components/prompts/PromptCard';
import { PromptList } from '@/components/prompts/PromptList';
import { PromptEditor } from '@/components/prompts/PromptEditor';
import { PromptPlayground } from '@/components/prompts/PromptPlayground';
import { TagFilter } from '@/components/prompts/TagFilter';
import { ActivePromptFilters } from '@/components/prompts/ActivePromptFilters';
import { cn } from '@/utils/cn';
import { useFolders } from '@/hooks/usePrompts';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

type ViewMode = 'grid' | 'list';
type SortField = 'name' | 'created_at' | 'updated_at' | 'use_count';

export default function Prompts() {
  const { promptId } = useParams();

  if (promptId) {
    return <PromptDetail promptId={promptId} />;
  }

  return <PromptsList />;
}

function PromptsList() {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFolderId, setSelectedFolderId] = useState<
    string | undefined
  >();
  const [starredOnly, setStarredOnly] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [sortBy, setSortBy] = useState<SortField>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fetch folders for breadcrumb
  const { data: folders = [] } = useFolders();

  // Fetch available tags
  const { data: availableTags = [], isLoading: tagsLoading } = usePromptTags();

  // Editor state
  const [showEditor, setShowEditor] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);

  // Playground state
  const [showPlayground, setShowPlayground] = useState(false);
  const [playgroundPrompt, setPlaygroundPrompt] = useState<Prompt | null>(null);

  // Delete state
  const [deletePromptId, setDeletePromptId] = useState<string | null>(null);
  const [deletePromptName, setDeletePromptName] = useState<string>('');

  const pageSize = 12;

  const { data, isLoading, error, refetch } = usePrompts({
    skip: 0, // Fetch all for client-side filtering
    limit: 100, // Maximum allowed by API
    search: searchQuery || undefined,
    folder_id: selectedFolderId,
    starred_only: starredOnly || undefined,
    tags: selectedTags.length > 0 ? selectedTags.join(',') : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const deletePrompt = useDeletePrompt();
  const updatePrompt = useUpdatePrompt();

  // Filter and sort prompts
  const processedPrompts = useMemo(() => {
    if (!data?.items) return [];
    return data.items;
  }, [data?.items]);

  // Paginate results
  const paginatedPrompts = useMemo(() => {
    const start = currentPage * pageSize;
    const end = start + pageSize;
    return processedPrompts.slice(start, end);
  }, [processedPrompts, currentPage, pageSize]);

  const totalPages = Math.ceil(processedPrompts.length / pageSize);
  const hasMore = currentPage < totalPages - 1;

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(0);
  }, [
    searchQuery,
    selectedFolderId,
    starredOnly,
    selectedTags,
    sortBy,
    sortOrder,
  ]);

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder(field === 'name' ? 'asc' : 'desc');
    }
  };

  const handlePromptClick = (prompt: Prompt) => {
    navigate(`/prompts/${prompt._id}`);
  };

  const handleEditPrompt = (prompt: Prompt) => {
    setEditingPrompt(prompt);
    setShowEditor(true);
  };

  const handleTestPrompt = (prompt: Prompt) => {
    setPlaygroundPrompt(prompt);
    setShowPlayground(true);
  };

  const handleToggleStar = async (prompt: Prompt, starred: boolean) => {
    try {
      await updatePrompt.mutateAsync({
        promptId: prompt._id,
        promptData: { is_starred: starred },
      });
      // Visual feedback for star toggle
      if (starred) {
        toast.success('Added to starred prompts', { duration: 2000 });
      } else {
        toast.success('Removed from starred prompts', { duration: 2000 });
      }
    } catch (error) {
      console.error('Failed to update star status:', error);
      toast.error('Failed to update star status');
    }
  };

  const handleDeleteClick = (prompt: Prompt) => {
    setDeletePromptId(prompt._id);
    setDeletePromptName(prompt.name);
  };

  const handleDeleteConfirm = async () => {
    if (!deletePromptId) return;

    try {
      await deletePrompt.mutateAsync({ promptId: deletePromptId });
      refetch();
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const errorMessage =
        apiError?.response?.data?.detail ||
        apiError?.message ||
        'Failed to delete prompt. Please try again.';
      toast.error(errorMessage);
      console.error('Delete prompt error:', error);
    }
    setDeletePromptId(null);
  };

  const handleCreateNew = () => {
    setEditingPrompt(null);
    setShowEditor(true);
  };

  const handleEditorClose = () => {
    setShowEditor(false);
    setEditingPrompt(null);
    refetch(); // Refresh the list
  };

  const handlePromptDrop = async (promptId: string, folderId?: string) => {
    try {
      await updatePrompt.mutateAsync({
        promptId,
        promptData: { folder_id: folderId },
      });
      refetch();

      // Get folder name for better feedback
      const folderName = folderId
        ? folders.find((f) => f._id === folderId)?.name || 'folder'
        : 'All Prompts';

      toast.success(
        <div className="flex items-center gap-2">
          <span>Prompt moved to</span>
          <span className="font-medium">{folderName}</span>
        </div>
      );
    } catch (error) {
      console.error('Failed to move prompt:', error);
      toast.error('Failed to move prompt');
    }
  };

  const handlePlaygroundClose = () => {
    setShowPlayground(false);
    setPlaygroundPrompt(null);
  };

  // Tag filter handlers
  const handleTagsChange = (tags: string[]) => {
    setSelectedTags(tags);
  };

  const handleRemoveFilter = (filterKey: string, value?: string) => {
    if (filterKey === 'search') {
      setSearchQuery('');
    } else if (filterKey === 'starredOnly') {
      setStarredOnly(false);
    } else if (filterKey === 'folder') {
      setSelectedFolderId(undefined);
    } else if (filterKey === 'tag' && value) {
      setSelectedTags((prev) => prev.filter((t) => t !== value));
    }
  };

  const handleClearAllFilters = () => {
    setSearchQuery('');
    setSelectedTags([]);
    setStarredOnly(false);
    setSelectedFolderId(undefined);
  };

  // Get current folder name for active filters
  const currentFolderName = selectedFolderId
    ? folders.find((f) => f._id === selectedFolderId)?.name
    : undefined;

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Prompts</h2>
          <p className="text-muted-foreground">
            Manage and test your AI prompts
          </p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Failed to load prompts</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Prompts</h2>
          <p className="text-muted-foreground">
            Manage and test your AI prompts
          </p>
        </div>
        <Button onClick={handleCreateNew}>
          <Plus className="h-4 w-4 mr-2" />
          New Prompt
        </Button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Sidebar */}
        <div className="col-span-3 space-y-6">
          {/* Folder Tree */}
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="text-lg flex items-center justify-between">
                <span>Folders</span>
                {folders.length > 0 && (
                  <span className="text-xs font-normal text-muted-foreground">
                    {folders.length} folder{folders.length !== 1 ? 's' : ''}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <FolderTree
                selectedFolderId={selectedFolderId}
                onFolderSelect={setSelectedFolderId}
                onPromptDrop={handlePromptDrop}
              />
            </CardContent>
          </Card>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Filters
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={starredOnly}
                    onChange={(e) => setStarredOnly(e.target.checked)}
                    className="rounded"
                  />
                  <Star className="h-4 w-4" />
                  Starred only
                </label>
              </div>

              {/* Tag Filter */}
              <TagFilter
                availableTags={availableTags}
                selectedTags={selectedTags}
                onChange={handleTagsChange}
                isLoading={tagsLoading}
              />
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="col-span-9 space-y-6">
          {/* Breadcrumb Navigation */}
          <FolderBreadcrumb
            folders={folders}
            selectedFolderId={selectedFolderId}
            onFolderSelect={setSelectedFolderId}
          />

          {/* Active Filters */}
          {(searchQuery ||
            selectedTags.length > 0 ||
            starredOnly ||
            selectedFolderId) && (
            <ActivePromptFilters
              filters={{
                search: searchQuery,
                selectedTags,
                starredOnly,
                folderId: selectedFolderId,
                folderName: currentFolderName,
              }}
              onRemoveFilter={handleRemoveFilter}
              onClearAll={handleClearAllFilters}
            />
          )}

          {/* Search and Controls */}
          <div className="flex items-center gap-4">
            {/* Search Bar */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search prompts by name, description, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Sort Controls */}
            <div className="flex items-center gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortField)}
                className="px-3 py-2 border rounded-lg bg-background text-sm"
              >
                <option value="updated_at">Updated</option>
                <option value="created_at">Created</option>
                <option value="name">Name</option>
                <option value="use_count">Usage</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
                }
              >
                {sortOrder === 'asc' ? (
                  <SortAsc className="h-4 w-4" />
                ) : (
                  <SortDesc className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center border rounded-lg">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'p-2 rounded-l-lg',
                  viewMode === 'grid'
                    ? 'bg-accent text-accent-foreground'
                    : 'hover:bg-accent'
                )}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'p-2 rounded-r-lg',
                  viewMode === 'list'
                    ? 'bg-accent text-accent-foreground'
                    : 'hover:bg-accent'
                )}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center p-12 space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Loading prompts...
              </p>
            </div>
          ) : (
            <>
              {viewMode === 'grid' ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 auto-rows-fr">
                  {processedPrompts.length === 0 ? (
                    <Card className="col-span-full">
                      <CardContent className="p-12 text-center">
                        <p className="text-muted-foreground">
                          {searchQuery
                            ? `No prompts found matching "${searchQuery}"`
                            : selectedFolderId
                              ? 'No prompts in this folder'
                              : starredOnly
                                ? 'No starred prompts found'
                                : 'No prompts found'}
                        </p>
                      </CardContent>
                    </Card>
                  ) : paginatedPrompts.length === 0 ? (
                    <Card className="col-span-full">
                      <CardContent className="p-12 text-center">
                        <p className="text-muted-foreground">
                          No prompts on this page
                        </p>
                      </CardContent>
                    </Card>
                  ) : (
                    paginatedPrompts.map((prompt) => (
                      <PromptCard
                        key={prompt._id}
                        prompt={prompt}
                        onClick={() => handlePromptClick(prompt)}
                        onEdit={handleEditPrompt}
                        onTest={handleTestPrompt}
                        onDelete={handleDeleteClick}
                        onToggleStar={handleToggleStar}
                      />
                    ))
                  )}
                </div>
              ) : (
                <PromptList
                  prompts={paginatedPrompts}
                  onPromptClick={handlePromptClick}
                  onEdit={handleEditPrompt}
                  onTest={handleTestPrompt}
                  onDelete={handleDeleteClick}
                  onToggleStar={handleToggleStar}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  onSort={handleSort}
                />
              )}

              {processedPrompts.length > 0 && (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Showing{' '}
                    {Math.min(
                      currentPage * pageSize + 1,
                      processedPrompts.length
                    )}{' '}
                    to{' '}
                    {Math.min(
                      (currentPage + 1) * pageSize,
                      processedPrompts.length
                    )}{' '}
                    of {processedPrompts.length}
                    {(searchQuery || selectedFolderId || starredOnly) &&
                      ` filtered`}{' '}
                    prompts
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 0}
                      className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={!hasMore}
                      className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Prompt Editor */}
      <PromptEditor
        isOpen={showEditor}
        onClose={handleEditorClose}
        prompt={editingPrompt || undefined}
        folderId={selectedFolderId}
      />

      {/* Prompt Playground */}
      {playgroundPrompt && (
        <PromptPlayground
          isOpen={showPlayground}
          onClose={handlePlaygroundClose}
          prompt={playgroundPrompt}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!deletePromptId}
        title="Delete Prompt"
        message={
          <div>
            <p>
              Are you sure you want to delete the prompt "{deletePromptName}"?
            </p>
            <p className="mt-2 text-sm font-semibold">
              This action cannot be undone.
            </p>
          </div>
        }
        confirmLabel="Delete Prompt"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeletePromptId(null)}
      />
    </div>
  );
}

function PromptDetail({ promptId }: { promptId: string }) {
  const navigate = useNavigate();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [showPlayground, setShowPlayground] = useState(false);

  const { data: prompt, isLoading: promptLoading } = usePrompt(promptId);
  const deletePrompt = useDeletePrompt();
  const updatePrompt = useUpdatePrompt();

  const handleDelete = async () => {
    try {
      await deletePrompt.mutateAsync({ promptId });
      toast.success('Prompt deleted successfully');
      navigate('/prompts');
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const errorMessage =
        apiError?.response?.data?.detail ||
        apiError?.message ||
        'Failed to delete prompt. Please try again.';
      toast.error(errorMessage);
      console.error('Delete prompt error:', error);
    }
    setShowDeleteDialog(false);
  };

  const handleToggleStar = async () => {
    if (!prompt) return;

    try {
      await updatePrompt.mutateAsync({
        promptId: prompt._id,
        promptData: { is_starred: !prompt.isStarred },
      });
      // Visual feedback for star toggle
      if (!prompt.isStarred) {
        toast.success('Added to starred prompts', { duration: 2000 });
      } else {
        toast.success('Removed from starred prompts', { duration: 2000 });
      }
    } catch (error) {
      console.error('Failed to update star status:', error);
      toast.error('Failed to update star status');
    }
  };

  if (promptLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!prompt) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Prompt Not Found
          </h2>
          <p className="text-muted-foreground">
            This prompt could not be found.
          </p>
        </div>
        <button
          onClick={() => navigate('/prompts')}
          className="text-sm text-primary hover:underline"
        >
          ← Back to prompts
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <button
          onClick={() => navigate('/prompts')}
          className="text-sm text-muted-foreground hover:text-foreground mb-2 flex items-center gap-1"
        >
          ← Back to prompts
        </button>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-bold tracking-tight">
                {prompt.name}
              </h2>
              <button
                onClick={handleToggleStar}
                className={cn(
                  'p-2 rounded-full transition-colors',
                  prompt.isStarred
                    ? 'text-yellow-500 hover:text-yellow-600'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
              >
                <Star
                  className={cn('h-5 w-5', prompt.isStarred && 'fill-current')}
                />
              </button>
            </div>
            {prompt.description && (
              <p className="mt-2 text-muted-foreground">{prompt.description}</p>
            )}
            {prompt.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {prompt.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
                  >
                    <Hash className="h-3 w-3" />
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setShowPlayground(true)}>
              <Play className="h-4 w-4 mr-2" />
              Test
            </Button>
            <Button variant="outline" onClick={() => setShowEditor(true)}>
              Edit
            </Button>
            <Button
              variant="destructive"
              onClick={() => setShowDeleteDialog(true)}
            >
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Variables</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{prompt.variables.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uses</CardTitle>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{prompt.useCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Version</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">v{prompt.version}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Updated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">
              {prompt.updatedAt
                ? formatDistanceToNow(new Date(prompt.updatedAt), {
                    addSuffix: true,
                  })
                : 'Never updated'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle>Content</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap font-mono text-sm bg-accent/30 p-4 rounded-lg overflow-auto">
            {prompt.content}
          </pre>
        </CardContent>
      </Card>

      {/* Prompt Editor */}
      <PromptEditor
        isOpen={showEditor}
        onClose={() => setShowEditor(false)}
        prompt={prompt}
      />

      {/* Prompt Playground */}
      <PromptPlayground
        isOpen={showPlayground}
        onClose={() => setShowPlayground(false)}
        prompt={prompt}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="Delete Prompt"
        message={
          <div>
            <p>Are you sure you want to delete the prompt "{prompt.name}"?</p>
            <p className="mt-2 text-sm font-semibold">
              This action cannot be undone.
            </p>
          </div>
        }
        confirmLabel="Delete Prompt"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteDialog(false)}
      />
    </div>
  );
}
