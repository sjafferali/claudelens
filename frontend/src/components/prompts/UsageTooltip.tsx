import { TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface UsageTooltipProps {
  useCount: number;
  lastUsedAt?: string;
  avgResponseTime?: number;
  successRate?: number;
  className?: string;
  children: React.ReactNode;
}

export function UsageTooltip({
  useCount,
  lastUsedAt,
  avgResponseTime,
  successRate,
  className,
  children,
}: UsageTooltipProps) {
  const getUsageLevel = (count: number) => {
    if (count === 0) return { label: 'Unused', color: 'text-muted-foreground' };
    if (count < 10) return { label: 'New', color: 'text-blue-500' };
    if (count < 50) return { label: 'Active', color: 'text-green-500' };
    if (count < 200) return { label: 'Popular', color: 'text-primary' };
    return { label: 'Highly Used', color: 'text-yellow-500' };
  };

  const usageLevel = getUsageLevel(useCount ?? 0);

  return (
    <div className={cn('group relative inline-block', className)}>
      {children}

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
        <div className="bg-popover border rounded-lg shadow-lg p-3 w-64">
          <div className="space-y-3">
            {/* Usage header */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Usage Statistics</span>
              <span className={cn('text-xs font-medium', usageLevel.color)}>
                {usageLevel.label}
              </span>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-1 text-muted-foreground">
                  <TrendingUp className="h-3 w-3" />
                  <span>Total Uses</span>
                </div>
                <p className="font-medium">
                  {(useCount ?? 0).toLocaleString()}
                </p>
              </div>

              {lastUsedAt && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>Last Used</span>
                  </div>
                  <p className="font-medium">
                    {new Date(lastUsedAt).toLocaleDateString()}
                  </p>
                </div>
              )}

              {avgResponseTime !== undefined && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>Avg Time</span>
                  </div>
                  <p className="font-medium">
                    {(avgResponseTime ?? 0).toFixed(1)}s
                  </p>
                </div>
              )}

              {successRate !== undefined && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    {successRate >= 95 ? (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    ) : successRate >= 80 ? (
                      <CheckCircle className="h-3 w-3 text-yellow-500" />
                    ) : (
                      <AlertCircle className="h-3 w-3 text-red-500" />
                    )}
                    <span>Success</span>
                  </div>
                  <p className="font-medium">
                    {(successRate ?? 0).toFixed(1)}%
                  </p>
                </div>
              )}
            </div>

            {/* Description */}
            <div className="pt-2 border-t text-xs text-muted-foreground">
              <p>
                This prompt has been used {useCount ?? 0} time
                {(useCount ?? 0) !== 1 ? 's' : ''}.
                {(useCount ?? 0) === 0 &&
                  ' Try testing it to see how it works!'}
                {(useCount ?? 0) > 0 &&
                  (useCount ?? 0) < 10 &&
                  " It's still new - consider testing more."}
                {(useCount ?? 0) >= 10 &&
                  (useCount ?? 0) < 50 &&
                  " It's being actively used."}
                {(useCount ?? 0) >= 50 &&
                  " It's a popular prompt in your library."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
