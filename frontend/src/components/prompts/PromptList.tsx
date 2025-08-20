import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  Star,
  StarIcon,
  MoreHorizontal,
  Edit3,
  Trash2,
  Copy,
  Share2,
  Play,
  Hash,
  ChevronUp,
  ChevronDown,
  Activity,
  HelpCircle,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { Prompt } from '@/api/types';
import { VariableCountBadge } from './VariableChips';
import { UsageTooltip } from './UsageTooltip';

interface PromptListProps {
  prompts: Prompt[];
  onPromptClick?: (prompt: Prompt) => void;
  onEdit?: (prompt: Prompt) => void;
  onDelete?: (prompt: Prompt) => void;
  onTest?: (prompt: Prompt) => void;
  onShare?: (prompt: Prompt) => void;
  onToggleStar?: (prompt: Prompt, starred: boolean) => void;
  sortBy?: SortField;
  sortOrder?: 'asc' | 'desc';
  onSort?: (field: SortField) => void;
  className?: string;
}

type SortField = 'name' | 'created_at' | 'updated_at' | 'use_count';

export function PromptList({
  prompts,
  onPromptClick,
  onEdit,
  onDelete,
  onTest,
  onShare,
  onToggleStar,
  sortBy,
  sortOrder,
  onSort,
  className,
}: PromptListProps) {
  const [selectedPrompts, setSelectedPrompts] = useState<Set<string>>(
    new Set()
  );
  const [showDropdownId, setShowDropdownId] = useState<string | null>(null);

  const handleStarClick = (e: React.MouseEvent, prompt: Prompt) => {
    e.preventDefault();
    e.stopPropagation();
    onToggleStar?.(prompt, !prompt.is_starred);
  };

  const handleActionClick = (e: React.MouseEvent, action: () => void) => {
    e.preventDefault();
    e.stopPropagation();
    action();
    setShowDropdownId(null);
  };

  const togglePromptSelection = (promptId: string) => {
    const newSelection = new Set(selectedPrompts);
    if (newSelection.has(promptId)) {
      newSelection.delete(promptId);
    } else {
      newSelection.add(promptId);
    }
    setSelectedPrompts(newSelection);
  };

  const selectAllPrompts = () => {
    if (selectedPrompts.size === prompts.length) {
      setSelectedPrompts(new Set());
    } else {
      setSelectedPrompts(new Set(prompts.map((p) => p._id)));
    }
  };

  const SortButton = ({
    field,
    label,
  }: {
    field: SortField;
    label: string;
  }) => (
    <button
      onClick={() => onSort?.(field)}
      className="flex items-center gap-1 hover:text-foreground transition-colors"
    >
      <span>{label}</span>
      {sortBy === field &&
        (sortOrder === 'asc' ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        ))}
    </button>
  );

  if (prompts.length === 0) {
    return (
      <div className={cn('text-center py-12 text-muted-foreground', className)}>
        No prompts found
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Bulk Actions */}
      {selectedPrompts.size > 0 && (
        <div className="flex items-center justify-between p-4 bg-accent/50 rounded-lg border">
          <span className="text-sm font-medium">
            {selectedPrompts.size} prompt{selectedPrompts.size > 1 ? 's' : ''}{' '}
            selected
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                /* TODO: Bulk share */
              }}
              className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Share
            </button>
            <button
              onClick={() => {
                /* TODO: Bulk delete */
              }}
              className="px-3 py-1 text-sm bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
            >
              Delete
            </button>
          </div>
        </div>
      )}

      {/* Table Header */}
      <div className="hidden md:grid grid-cols-12 gap-4 px-4 py-2 border-b text-sm font-medium text-muted-foreground">
        <div className="col-span-1 flex items-center">
          <input
            type="checkbox"
            checked={
              selectedPrompts.size === prompts.length && prompts.length > 0
            }
            onChange={selectAllPrompts}
            className="rounded"
          />
        </div>
        <div className="col-span-4">
          <SortButton field="name" label="Name" />
        </div>
        <div className="col-span-2">
          <div className="flex items-center gap-1">
            <span>Variables</span>
            <div className="group relative">
              <HelpCircle className="h-3 w-3 text-muted-foreground cursor-help" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
                <div className="bg-popover border rounded-lg shadow-lg p-2 w-48">
                  <p className="text-xs">
                    Variables make prompts reusable by replacing placeholders
                    with actual values
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-span-1">
          <SortButton field="use_count" label="Uses" />
        </div>
        <div className="col-span-2">
          <SortButton field="updated_at" label="Updated" />
        </div>
        <div className="col-span-2">Actions</div>
      </div>

      {/* Prompt Rows */}
      <div className="space-y-2">
        {prompts.map((prompt) => (
          <div
            key={prompt._id}
            onClick={() => onPromptClick?.(prompt)}
            className="group p-4 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
          >
            {/* Mobile Layout */}
            <div className="md:hidden space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <input
                    type="checkbox"
                    checked={selectedPrompts.has(prompt._id)}
                    onChange={() => togglePromptSelection(prompt._id)}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded mt-1"
                  />
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium truncate">{prompt.name}</h3>
                      <button
                        onClick={(e) => handleStarClick(e, prompt)}
                        className={cn(
                          'p-1',
                          prompt.is_starred
                            ? 'text-yellow-500'
                            : 'text-muted-foreground hover:text-foreground'
                        )}
                      >
                        {prompt.is_starred ? (
                          <Star className="h-4 w-4 fill-current" />
                        ) : (
                          <StarIcon className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {prompt.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {prompt.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <UsageTooltip
                        useCount={prompt.use_count}
                        lastUsedAt={undefined}
                        avgResponseTime={undefined}
                        successRate={undefined}
                      >
                        <span className="cursor-help">
                          {prompt.use_count} uses
                        </span>
                      </UsageTooltip>
                      <span>
                        {prompt.updated_at
                          ? formatDistanceToNow(new Date(prompt.updated_at), {
                              addSuffix: true,
                            })
                          : 'Never updated'}
                      </span>
                      <span>v{prompt.version}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDropdownId(
                          showDropdownId === prompt._id ? null : prompt._id
                        );
                      }}
                      className="p-2 hover:bg-accent rounded-md"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                    {showDropdownId === prompt._id && (
                      <ActionsDropdown
                        prompt={prompt}
                        onEdit={onEdit}
                        onTest={onTest}
                        onShare={onShare}
                        onDelete={onDelete}
                        onClose={() => setShowDropdownId(null)}
                        onAction={handleActionClick}
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Tags and Variables */}
              <div className="space-y-2">
                {prompt.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {prompt.tags.slice(0, 3).map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-secondary text-secondary-foreground rounded-md text-xs"
                      >
                        <Hash className="h-2.5 w-2.5" />
                        {tag}
                      </span>
                    ))}
                    {prompt.tags.length > 3 && (
                      <span className="text-xs text-muted-foreground">
                        +{prompt.tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}
                <VariableCountBadge count={prompt.variables.length} />
              </div>
            </div>

            {/* Desktop Layout */}
            <div className="hidden md:grid grid-cols-12 gap-4 items-center">
              <div className="col-span-1">
                <input
                  type="checkbox"
                  checked={selectedPrompts.has(prompt._id)}
                  onChange={() => togglePromptSelection(prompt._id)}
                  onClick={(e) => e.stopPropagation()}
                  className="rounded"
                />
              </div>

              <div className="col-span-4 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium truncate flex-1">{prompt.name}</h3>
                  <button
                    onClick={(e) => handleStarClick(e, prompt)}
                    className={cn(
                      'p-1',
                      prompt.is_starred
                        ? 'text-yellow-500'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {prompt.is_starred ? (
                      <Star className="h-4 w-4 fill-current" />
                    ) : (
                      <StarIcon className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {prompt.description && (
                  <p className="text-sm text-muted-foreground truncate">
                    {prompt.description}
                  </p>
                )}
                {prompt.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {prompt.tags.slice(0, 2).map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-secondary text-secondary-foreground rounded text-xs"
                      >
                        <Hash className="h-2 w-2" />
                        {tag}
                      </span>
                    ))}
                    {prompt.tags.length > 2 && (
                      <span className="text-xs text-muted-foreground">
                        +{prompt.tags.length - 2}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="col-span-2">
                <VariableCountBadge count={prompt.variables.length} />
              </div>

              <div className="col-span-1 text-sm">
                <UsageTooltip
                  useCount={prompt.use_count}
                  lastUsedAt={undefined}
                  avgResponseTime={undefined}
                  successRate={undefined}
                >
                  <div className="cursor-help flex items-center gap-1">
                    <Activity className="h-3 w-3 text-muted-foreground" />
                    <span>{prompt.use_count}</span>
                  </div>
                </UsageTooltip>
              </div>

              <div className="col-span-2 text-sm text-muted-foreground">
                <div>
                  {prompt.updated_at
                    ? formatDistanceToNow(new Date(prompt.updated_at), {
                        addSuffix: true,
                      })
                    : 'Never updated'}
                </div>
                <div className="text-xs">v{prompt.version}</div>
              </div>

              <div className="col-span-2">
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {onTest && (
                    <button
                      onClick={(e) =>
                        handleActionClick(e, () => onTest(prompt))
                      }
                      className="p-1 hover:bg-accent rounded"
                      title="Test"
                    >
                      <Play className="h-4 w-4" />
                    </button>
                  )}
                  {onEdit && (
                    <button
                      onClick={(e) =>
                        handleActionClick(e, () => onEdit(prompt))
                      }
                      className="p-1 hover:bg-accent rounded"
                      title="Edit"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>
                  )}
                  {onShare && (
                    <button
                      onClick={(e) =>
                        handleActionClick(e, () => onShare(prompt))
                      }
                      className="p-1 hover:bg-accent rounded"
                      title="Share"
                    >
                      <Share2 className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={(e) =>
                      handleActionClick(e, () => {
                        navigator.clipboard.writeText(prompt.content);
                      })
                    }
                    className="p-1 hover:bg-accent rounded"
                    title="Copy"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDropdownId(
                          showDropdownId === prompt._id ? null : prompt._id
                        );
                      }}
                      className="p-1 hover:bg-accent rounded"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                    {showDropdownId === prompt._id && (
                      <ActionsDropdown
                        prompt={prompt}
                        onEdit={onEdit}
                        onTest={onTest}
                        onShare={onShare}
                        onDelete={onDelete}
                        onClose={() => setShowDropdownId(null)}
                        onAction={handleActionClick}
                      />
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface ActionsDropdownProps {
  prompt: Prompt;
  onEdit?: (prompt: Prompt) => void;
  onTest?: (prompt: Prompt) => void;
  onShare?: (prompt: Prompt) => void;
  onDelete?: (prompt: Prompt) => void;
  onClose: () => void;
  onAction: (e: React.MouseEvent, action: () => void) => void;
}

function ActionsDropdown({
  prompt,
  onEdit,
  onTest,
  onShare,
  onDelete,
  onClose,
  onAction,
}: ActionsDropdownProps) {
  return (
    <>
      <div className="absolute right-0 top-8 z-50 min-w-32 bg-popover border rounded-md shadow-md py-1">
        {onTest && (
          <button
            onClick={(e) => onAction(e, () => onTest(prompt))}
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2"
          >
            <Play className="h-3 w-3" />
            Test
          </button>
        )}
        {onEdit && (
          <button
            onClick={(e) => onAction(e, () => onEdit(prompt))}
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2"
          >
            <Edit3 className="h-3 w-3" />
            Edit
          </button>
        )}
        {onShare && (
          <button
            onClick={(e) => onAction(e, () => onShare(prompt))}
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2"
          >
            <Share2 className="h-3 w-3" />
            Share
          </button>
        )}
        <button
          onClick={(e) =>
            onAction(e, () => {
              navigator.clipboard.writeText(prompt.content);
            })
          }
          className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2"
        >
          <Copy className="h-3 w-3" />
          Copy Content
        </button>
        {onDelete && (
          <button
            onClick={(e) => onAction(e, () => onDelete(prompt))}
            className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent flex items-center gap-2 text-destructive"
          >
            <Trash2 className="h-3 w-3" />
            Delete
          </button>
        )}
      </div>
      <div className="fixed inset-0 z-40" onClick={onClose} />
    </>
  );
}
