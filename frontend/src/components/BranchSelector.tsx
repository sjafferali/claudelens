import { cn } from '@/utils/cn';
import { ChevronLeft, ChevronRight, GitBranch } from 'lucide-react';
import { Message } from '@/api/types';

interface BranchSelectorProps {
  currentMessage: Message;
  branchMessages: Message[];
  onSelectBranch: (messageUuid: string) => void;
  className?: string;
}

export function BranchSelector({
  currentMessage,
  branchMessages,
  onSelectBranch,
  className,
}: BranchSelectorProps) {
  // Don't show selector if there's only one branch or no branch info
  if (!currentMessage.branchCount || currentMessage.branchCount <= 1) {
    return null;
  }

  const currentIndex = currentMessage.branchIndex || 1;
  const totalBranches = currentMessage.branchCount;

  // Find previous and next branch UUIDs
  const prevBranchUuid =
    currentIndex > 1
      ? branchMessages[currentIndex - 2]?.uuid ||
        branchMessages[currentIndex - 2]?.messageUuid
      : null;
  const nextBranchUuid =
    currentIndex < totalBranches
      ? branchMessages[currentIndex]?.uuid ||
        branchMessages[currentIndex]?.messageUuid
      : null;

  const handlePrevious = () => {
    if (prevBranchUuid) {
      onSelectBranch(prevBranchUuid);
    }
  };

  const handleNext = () => {
    if (nextBranchUuid) {
      onSelectBranch(nextBranchUuid);
    }
  };

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 px-1 py-0.5 rounded-full',
        'bg-amber-100 dark:bg-amber-900/30',
        'border border-amber-300 dark:border-amber-700',
        'shadow-sm',
        className
      )}
    >
      {/* Previous button */}
      <button
        onClick={handlePrevious}
        disabled={currentIndex <= 1}
        className={cn(
          'p-1 rounded-full transition-all duration-200',
          'hover:bg-amber-200 dark:hover:bg-amber-800/30',
          currentIndex <= 1
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:scale-110 active:scale-95'
        )}
        title="Previous version (Alt+←)"
        aria-label="Previous version"
      >
        <ChevronLeft className="h-3.5 w-3.5 text-amber-700 dark:text-amber-300" />
      </button>

      {/* Branch counter display */}
      <div className="flex items-center gap-1 px-2">
        <GitBranch className="h-3.5 w-3.5 text-amber-700 dark:text-amber-300" />
        <span className="text-xs font-medium text-amber-800 dark:text-amber-300">
          Branch {currentIndex} of {totalBranches}
        </span>
      </div>

      {/* Next button */}
      <button
        onClick={handleNext}
        disabled={currentIndex >= totalBranches}
        className={cn(
          'p-1 rounded-full transition-all duration-200',
          'hover:bg-amber-200 dark:hover:bg-amber-800/30',
          currentIndex >= totalBranches
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:scale-110 active:scale-95'
        )}
        title="Next version (Alt+→)"
        aria-label="Next version"
      >
        <ChevronRight className="h-3.5 w-3.5 text-amber-700 dark:text-amber-300" />
      </button>
    </div>
  );
}

export function BranchSelectorCompact({
  currentIndex,
  totalBranches,
  onNavigate,
  className,
}: {
  currentIndex: number;
  totalBranches: number;
  onNavigate: (direction: 'prev' | 'next') => void;
  className?: string;
}) {
  // Don't show selector if there's only one branch
  if (totalBranches <= 1) {
    return null;
  }

  return (
    <div
      className={cn('inline-flex items-center gap-0.5', 'text-xs', className)}
    >
      <button
        onClick={() => onNavigate('prev')}
        disabled={currentIndex <= 1}
        className={cn(
          'p-0.5 rounded transition-all duration-200',
          'hover:bg-amber-200/50 dark:hover:bg-amber-800/30',
          currentIndex <= 1
            ? 'opacity-30 cursor-not-allowed'
            : 'hover:scale-110'
        )}
        title="Previous version"
        aria-label="Previous version"
      >
        <ChevronLeft className="h-3 w-3 text-amber-600 dark:text-amber-400" />
      </button>

      <span className="px-1 text-amber-700 dark:text-amber-300 font-medium min-w-[3rem] text-center">
        {currentIndex}/{totalBranches}
      </span>

      <button
        onClick={() => onNavigate('next')}
        disabled={currentIndex >= totalBranches}
        className={cn(
          'p-0.5 rounded transition-all duration-200',
          'hover:bg-amber-200/50 dark:hover:bg-amber-800/30',
          currentIndex >= totalBranches
            ? 'opacity-30 cursor-not-allowed'
            : 'hover:scale-110'
        )}
        title="Next version"
        aria-label="Next version"
      >
        <ChevronRight className="h-3 w-3 text-amber-600 dark:text-amber-400" />
      </button>
    </div>
  );
}
