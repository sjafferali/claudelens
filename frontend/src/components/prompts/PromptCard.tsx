import { forwardRef, HTMLAttributes } from 'react';
import { formatDistanceToNow } from 'date-fns';
import {
  Star,
  StarIcon,
  Edit3,
  Trash2,
  Copy,
  Share2,
  Play,
  Hash,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
import { cn } from '@/utils/cn';
import { Prompt } from '@/api/types';
import { VariableCountBadge } from './VariableChips';

interface PromptCardProps extends HTMLAttributes<HTMLDivElement> {
  prompt: Prompt;
  onEdit?: (prompt: Prompt) => void;
  onDelete?: (prompt: Prompt) => void;
  onTest?: (prompt: Prompt) => void;
  onShare?: (prompt: Prompt) => void;
  onToggleStar?: (prompt: Prompt, starred: boolean) => void;
  showVariables?: boolean;
  compact?: boolean;
}

export const PromptCard = forwardRef<HTMLDivElement, PromptCardProps>(
  (
    {
      prompt,
      onEdit,
      onDelete,
      onTest,
      onShare,
      onToggleStar,
      showVariables = true,
      compact = false,
      className,
      onClick,
      ...props
    },
    ref
  ) => {
    const handleStarClick = (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      onToggleStar?.(prompt, !prompt.is_starred);
    };

    const handleActionClick = (e: React.MouseEvent, action: () => void) => {
      e.preventDefault();
      e.stopPropagation();
      action();
    };

    return (
      <Card
        ref={ref}
        onClick={onClick}
        className={cn(
          'cursor-pointer hover:shadow-lg transition-shadow relative group',
          className
        )}
        {...props}
      >
        {/* Star button - always visible when starred, visible on hover otherwise */}
        <button
          onClick={handleStarClick}
          className={cn(
            'absolute top-2 right-2 p-1.5 rounded-full transition-opacity z-10',
            prompt.is_starred
              ? 'opacity-100 text-yellow-500 hover:text-yellow-600'
              : 'opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground hover:bg-accent'
          )}
          title={prompt.is_starred ? 'Remove from starred' : 'Add to starred'}
        >
          {prompt.is_starred ? (
            <Star className="h-4 w-4 fill-current" />
          ) : (
            <StarIcon className="h-4 w-4" />
          )}
        </button>

        <CardHeader className={cn(compact ? 'p-4 pb-2' : 'p-6 pb-3')}>
          <div className="space-y-2">
            <CardTitle
              className={cn(
                'flex items-start gap-2 pr-8 leading-tight',
                compact ? 'text-lg' : 'text-xl'
              )}
            >
              <span className="truncate">{prompt.name}</span>
            </CardTitle>

            {prompt.description && (
              <CardDescription className="line-clamp-2 text-sm">
                {prompt.description}
              </CardDescription>
            )}

            {/* Tags */}
            {prompt.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {prompt.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-secondary text-secondary-foreground rounded-md text-xs font-medium"
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
          </div>
        </CardHeader>

        <CardContent className={cn(compact ? 'p-4 pt-0' : 'p-6 pt-0')}>
          <div className="space-y-3">
            {/* Variables */}
            {showVariables && (
              <div className="flex items-center justify-between">
                <VariableCountBadge count={prompt.variables.length} />
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Play className="h-3 w-3" />
                    <span>{prompt.use_count} uses</span>
                  </div>
                </div>
              </div>
            )}

            {/* Updated timestamp */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Updated{' '}
                {formatDistanceToNow(new Date(prompt.updated_at), {
                  addSuffix: true,
                })}
              </span>
              <span className="text-xs font-mono">v{prompt.version}</span>
            </div>

            {/* Action buttons - visible on hover */}
            <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
              {onTest && (
                <button
                  onClick={(e) => handleActionClick(e, () => onTest(prompt))}
                  className="p-2 hover:bg-accent rounded-md transition-colors"
                  title="Test prompt"
                >
                  <Play className="h-4 w-4" />
                </button>
              )}
              {onEdit && (
                <button
                  onClick={(e) => handleActionClick(e, () => onEdit(prompt))}
                  className="p-2 hover:bg-accent rounded-md transition-colors"
                  title="Edit prompt"
                >
                  <Edit3 className="h-4 w-4" />
                </button>
              )}
              {onShare && (
                <button
                  onClick={(e) => handleActionClick(e, () => onShare(prompt))}
                  className="p-2 hover:bg-accent rounded-md transition-colors"
                  title="Share prompt"
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
                className="p-2 hover:bg-accent rounded-md transition-colors"
                title="Copy content"
              >
                <Copy className="h-4 w-4" />
              </button>
              {onDelete && (
                <button
                  onClick={(e) => handleActionClick(e, () => onDelete(prompt))}
                  className="p-2 hover:bg-accent rounded-md transition-colors text-destructive"
                  title="Delete prompt"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
);

PromptCard.displayName = 'PromptCard';
