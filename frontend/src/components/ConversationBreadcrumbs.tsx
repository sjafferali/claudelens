import { ChevronRight, Home } from 'lucide-react';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';

interface ConversationBreadcrumbsProps {
  path: Message[];
  onNavigate: (messageId: string) => void;
  currentMessageId?: string;
  className?: string;
}

export function ConversationBreadcrumbs({
  path,
  onNavigate,
  currentMessageId,
  className,
}: ConversationBreadcrumbsProps) {
  if (path.length === 0) return null;

  const maxItemsToShow = 4;
  const shouldTruncate = path.length > maxItemsToShow;

  // If we need to truncate, show first item, ellipsis, and last 2 items
  let displayPath: (Message | null)[] = path;
  if (shouldTruncate) {
    displayPath = [
      path[0],
      null, // This will be the ellipsis
      ...path.slice(-2),
    ];
  }

  const getMessageLabel = (message: Message): string => {
    switch (message.type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Claude';
      case 'system':
        return 'System';
      case 'tool_use':
        return 'Tool';
      case 'tool_result':
        return 'Result';
      default:
        return message.type;
    }
  };

  const truncateContent = (content: string, maxLength = 30): string => {
    const cleanContent = content.replace(/\n/g, ' ').trim();
    if (cleanContent.length <= maxLength) return cleanContent;
    return cleanContent.substring(0, maxLength) + '...';
  };

  return (
    <nav
      className={cn(
        'flex items-center gap-1 px-4 py-2 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700',
        className
      )}
      aria-label="Message navigation breadcrumb"
    >
      {/* Home/Root icon */}
      <button
        onClick={() => {
          const firstMessage = path[0];
          const messageId =
            firstMessage.uuid || firstMessage.messageUuid || firstMessage._id;
          onNavigate(messageId);
        }}
        className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
        title="Go to conversation start"
      >
        <Home className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
      </button>

      <ChevronRight className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />

      {displayPath.map((message, index) => {
        // Handle ellipsis placeholder
        if (message === null) {
          return (
            <div key={`ellipsis-${index}`} className="flex items-center gap-1">
              <span className="px-2 py-1 text-sm text-slate-500 dark:text-slate-400">
                ...
              </span>
              <ChevronRight className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
            </div>
          );
        }

        const messageId = message.uuid || message.messageUuid || message._id;
        const isCurrentMessage = messageId === currentMessageId;
        const isLastItem = index === displayPath.length - 1;

        return (
          <div key={messageId} className="flex items-center gap-1">
            <button
              onClick={() => onNavigate(messageId)}
              disabled={isCurrentMessage}
              className={cn(
                'inline-flex items-center gap-1.5 px-2 py-1 text-sm rounded transition-all',
                isCurrentMessage
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium cursor-default'
                  : 'hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300'
              )}
              title={
                message.content
                  ? truncateContent(message.content, 100)
                  : undefined
              }
            >
              <span className="font-medium">{getMessageLabel(message)}</span>
              {message.branchCount && message.branchCount > 1 && (
                <span className="text-xs text-amber-600 dark:text-amber-400">
                  ({message.branchIndex}/{message.branchCount})
                </span>
              )}
              {message.content && (
                <span className="text-xs text-slate-500 dark:text-slate-400 max-w-[100px] truncate">
                  : {truncateContent(message.content, 20)}
                </span>
              )}
            </button>

            {!isLastItem && (
              <ChevronRight className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500" />
            )}
          </div>
        );
      })}
    </nav>
  );
}
