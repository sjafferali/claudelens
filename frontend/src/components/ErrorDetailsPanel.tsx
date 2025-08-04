import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { analyticsApi, TimeRange, ErrorDetail } from '@/api/analytics';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface ErrorDetailsPanelProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function ErrorDetailsPanel({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: ErrorDetailsPanelProps) {
  const [expandedErrors, setExpandedErrors] = useState<Set<number>>(new Set());
  const [selectedSeverity, setSelectedSeverity] = useState<
    'critical' | 'warning' | 'info' | undefined
  >(undefined);

  const {
    data: errorData,
    isLoading,
    error,
  } = useQuery({
    queryKey: [
      'detailedErrors',
      sessionId,
      projectId,
      timeRange,
      selectedSeverity,
    ],
    queryFn: () =>
      analyticsApi.getDetailedErrors(sessionId, timeRange, selectedSeverity),
    refetchInterval: 5 * 60 * 1000, // 5 minutes cache
    retry: 1, // Only retry once on failure
  });

  const toggleErrorExpansion = (index: number) => {
    setExpandedErrors((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">
          Error Details
        </h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-3 bg-layer-tertiary border border-secondary-c rounded-lg animate-pulse"
            >
              <div className="h-4 bg-layer-secondary rounded mb-2"></div>
              <div className="h-3 bg-layer-secondary rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">
          Error Details
        </h3>
        <div className="text-sm text-muted-c">Unable to load error details</div>
      </div>
    );
  }

  const errors = errorData?.errors || [];
  const errorSummary = errorData?.error_summary;

  const getSeverityBadgeClass = (severity: ErrorDetail['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-700 border-red-300 dark:bg-red-950/20 dark:text-red-400 dark:border-red-800';
      case 'warning':
        return 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-950/20 dark:text-orange-400 dark:border-orange-800';
      case 'info':
        return 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-800';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-950/20 dark:text-gray-400 dark:border-gray-800';
    }
  };

  const getSeverityIcon = (severity: ErrorDetail['severity']) => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'warning':
        return '🟠';
      case 'info':
        return '🔵';
      default:
        return '⚪';
    }
  };

  if (errors.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">
          Error Details
        </h3>
        <div className="text-sm text-muted-c">
          {selectedSeverity
            ? `No ${selectedSeverity} errors found in this period`
            : 'No errors found in this period'}
        </div>
        {selectedSeverity && (
          <button
            onClick={() => setSelectedSeverity(undefined)}
            className="mt-2 text-xs text-primary hover:text-primary-hover"
          >
            Show all errors
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-medium text-primary-c">Error Details</h3>
        <div className="flex gap-1">
          <button
            onClick={() => setSelectedSeverity(undefined)}
            className={`px-2 py-1 text-xs rounded transition-all ${
              !selectedSeverity
                ? 'bg-primary text-primary-foreground'
                : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setSelectedSeverity('critical')}
            className={`px-2 py-1 text-xs rounded transition-all ${
              selectedSeverity === 'critical'
                ? 'bg-red-600 text-white'
                : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
            }`}
          >
            Critical
          </button>
          <button
            onClick={() => setSelectedSeverity('warning')}
            className={`px-2 py-1 text-xs rounded transition-all ${
              selectedSeverity === 'warning'
                ? 'bg-orange-600 text-white'
                : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
            }`}
          >
            Warning
          </button>
        </div>
      </div>

      {/* Error Summary */}
      {errorSummary && (
        <div className="mb-4 text-sm text-muted-c">
          {errors.length} error{errors.length !== 1 ? 's' : ''} found
          {Object.keys(errorSummary.by_tool).length > 0 && (
            <span className="ml-2">
              across {Object.keys(errorSummary.by_tool).length} tool
              {Object.keys(errorSummary.by_tool).length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      )}

      {/* Error List */}
      <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-thin">
        {errors.map((error, index) => {
          const isExpanded = expandedErrors.has(index);

          return (
            <div
              key={index}
              className="border border-secondary-c rounded-lg p-3 bg-layer-secondary hover:border-primary-c transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getSeverityBadgeClass(error.severity)}`}
                  >
                    <span className="mr-1">
                      {getSeverityIcon(error.severity)}
                    </span>
                    {error.severity}
                  </span>
                  <span className="text-sm font-medium text-secondary-c">
                    {error.tool}
                  </span>
                </div>
                <span className="text-xs text-dim-c">
                  {format(new Date(error.timestamp), 'MMM d, HH:mm')}
                </span>
              </div>

              <div className="text-sm text-tertiary-c mb-2">
                <span className="font-medium">{error.error_type}</span>
                {error.context && (
                  <span className="text-muted-c ml-2">• {error.context}</span>
                )}
              </div>

              <div className="text-sm text-secondary-c">
                {error.message.length > 100 && !isExpanded ? (
                  <>
                    {error.message.slice(0, 100)}...
                    <button
                      onClick={() => toggleErrorExpansion(index)}
                      className="ml-2 inline-flex items-center gap-1 text-primary hover:text-primary-hover"
                    >
                      <ChevronDown className="h-3 w-3" />
                      Show more
                    </button>
                  </>
                ) : (
                  <>
                    {error.message}
                    {error.message.length > 100 && (
                      <button
                        onClick={() => toggleErrorExpansion(index)}
                        className="ml-2 inline-flex items-center gap-1 text-primary hover:text-primary-hover"
                      >
                        <ChevronUp className="h-3 w-3" />
                        Show less
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Error Summary Stats */}
      {errorSummary && Object.keys(errorSummary.by_type).length > 0 && (
        <div className="mt-4 pt-4 border-t border-secondary-c">
          <div className="text-xs text-muted-c font-medium mb-2">
            Error Types:
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(errorSummary.by_type).map(([type, count]) => (
              <div
                key={type}
                className="px-2 py-1 bg-layer-tertiary border border-secondary-c rounded text-xs text-tertiary-c"
              >
                {type}: {count}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
