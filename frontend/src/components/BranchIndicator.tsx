import { cn } from '@/utils/cn';
import { GitBranch } from 'lucide-react';

interface BranchIndicatorProps {
  branchCount: number;
  branchIndex?: number;
  onClick?: () => void;
  className?: string;
}

export function BranchIndicator({
  branchCount,
  branchIndex,
  onClick,
  className,
}: BranchIndicatorProps) {
  // Don't show indicator if there's only one branch
  if (branchCount <= 1) {
    return null;
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
        'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
        'hover:bg-amber-200 dark:hover:bg-amber-800/30',
        'border border-amber-300 dark:border-amber-700',
        'transition-all duration-200 hover:scale-105',
        'shadow-sm hover:shadow-md',
        onClick && 'cursor-pointer',
        className
      )}
      title={`Click to see ${branchCount - 1} alternative${
        branchCount > 2 ? 's' : ''
      }`}
    >
      <GitBranch className="h-3.5 w-3.5" />
      <span>
        {branchIndex
          ? `${branchIndex}/${branchCount}`
          : `${branchCount} versions`}
      </span>
    </button>
  );
}

export function BranchIndicatorBadge({
  branchCount,
  className,
}: {
  branchCount: number;
  className?: string;
}) {
  // Don't show badge if there's only one branch
  if (branchCount <= 1) {
    return null;
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold',
        'bg-gradient-to-r from-amber-500 to-orange-500 text-white',
        'shadow-sm',
        className
      )}
      title={`${branchCount} versions available`}
    >
      <GitBranch className="h-3 w-3" />
      <span>{branchCount}</span>
    </div>
  );
}
