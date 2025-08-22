import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils/cn';
import { AlertCircle, Clock } from 'lucide-react';
import axios from 'axios';

interface RateLimitData {
  export: {
    current: number;
    limit: number;
    remaining: number;
    window_hours: number;
    reset_in_seconds: number | null;
  };
  import: {
    current: number;
    limit: number;
    remaining: number;
    window_hours: number;
    reset_in_seconds: number | null;
  };
}

async function fetchRateLimits(): Promise<RateLimitData> {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await axios.get(`${apiUrl}/api/v1/rate-limits`);
  return response.data;
}

interface RateLimitIndicatorProps {
  type: 'export' | 'import';
  className?: string;
}

export const RateLimitIndicator: React.FC<RateLimitIndicatorProps> = ({
  type,
  className,
}) => {
  const { data, isLoading } = useQuery({
    queryKey: ['rateLimits'],
    queryFn: fetchRateLimits,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  });

  if (isLoading || !data) {
    return null;
  }

  const limits = data[type];
  const percentUsed = (limits.current / limits.limit) * 100;
  const isNearLimit = percentUsed >= 80;
  const isAtLimit = limits.remaining === 0;

  const formatResetTime = (seconds: number | null) => {
    if (!seconds) return '';
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m`;
    } else {
      return `${Math.floor(seconds)}s`;
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg border',
        isAtLimit
          ? 'bg-red-50 border-red-300 dark:bg-red-900/20 dark:border-red-700'
          : isNearLimit
            ? 'bg-yellow-50 border-yellow-300 dark:bg-yellow-900/20 dark:border-yellow-700'
            : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700',
        className
      )}
    >
      <div className="flex items-center gap-2">
        {isAtLimit ? (
          <AlertCircle className="w-4 h-4 text-red-500" />
        ) : isNearLimit ? (
          <AlertCircle className="w-4 h-4 text-yellow-500" />
        ) : (
          <Clock className="w-4 h-4 text-gray-400" />
        )}

        <div className="text-sm">
          <span className="font-medium text-gray-700 dark:text-gray-300">
            {type === 'export' ? 'Export' : 'Import'} Limit:
          </span>
          <span
            className={cn(
              'ml-2 font-semibold',
              isAtLimit
                ? 'text-red-600 dark:text-red-400'
                : isNearLimit
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-gray-900 dark:text-gray-100'
            )}
          >
            {limits.current} / {limits.limit}
          </span>
          {limits.reset_in_seconds && limits.reset_in_seconds > 0 && (
            <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
              (resets in {formatResetTime(limits.reset_in_seconds)})
            </span>
          )}
        </div>
      </div>

      {/* Visual progress bar */}
      <div className="flex-1 max-w-[100px] h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full transition-all duration-300',
            isAtLimit
              ? 'bg-red-500'
              : isNearLimit
                ? 'bg-yellow-500'
                : 'bg-green-500'
          )}
          style={{ width: `${Math.min(100, percentUsed)}%` }}
        />
      </div>

      {isAtLimit && (
        <div className="text-xs text-red-600 dark:text-red-400 font-medium">
          Limit reached
        </div>
      )}
    </div>
  );
};
