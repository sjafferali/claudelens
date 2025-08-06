import { ArrowUp, ArrowDown, ChevronUp, ChevronDown } from 'lucide-react';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';

interface NavigationButtonsProps {
  message: Message;
  hasParent: boolean;
  hasChildren: boolean;
  childrenCount?: number;
  onNavigateToParent: () => void;
  onNavigateToChildren: () => void;
  className?: string;
}

export function MessageNavigationButtons({
  hasParent,
  hasChildren,
  childrenCount = 0,
  onNavigateToParent,
  onNavigateToChildren,
  className,
}: NavigationButtonsProps) {
  return (
    <div className={cn('flex items-center gap-1', className)}>
      {hasParent && (
        <button
          onClick={onNavigateToParent}
          className="group inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-md transition-all duration-200 border border-slate-200 dark:border-slate-700"
          title="Jump to parent message"
        >
          <ArrowUp className="h-3 w-3 group-hover:-translate-y-0.5 transition-transform" />
          <span>Parent</span>
        </button>
      )}

      {hasChildren && (
        <button
          onClick={onNavigateToChildren}
          className="group inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-md transition-all duration-200 border border-slate-200 dark:border-slate-700"
          title={`View ${childrenCount} ${childrenCount === 1 ? 'reply' : 'replies'}`}
        >
          <ArrowDown className="h-3 w-3 group-hover:translate-y-0.5 transition-transform" />
          <span>
            {childrenCount > 0
              ? `${childrenCount} ${childrenCount === 1 ? 'Reply' : 'Replies'}`
              : 'Replies'}
          </span>
        </button>
      )}
    </div>
  );
}

interface CompactNavigationButtonsProps {
  hasParent: boolean;
  hasChildren: boolean;
  onNavigateToParent: () => void;
  onNavigateToChildren: () => void;
  className?: string;
}

export function CompactNavigationButtons({
  hasParent,
  hasChildren,
  onNavigateToParent,
  onNavigateToChildren,
  className,
}: CompactNavigationButtonsProps) {
  return (
    <div className={cn('flex items-center', className)}>
      {hasParent && (
        <button
          onClick={onNavigateToParent}
          className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Jump to parent"
        >
          <ChevronUp className="h-4 w-4 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" />
        </button>
      )}

      {hasChildren && (
        <button
          onClick={onNavigateToChildren}
          className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="View replies"
        >
          <ChevronDown className="h-4 w-4 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" />
        </button>
      )}
    </div>
  );
}
