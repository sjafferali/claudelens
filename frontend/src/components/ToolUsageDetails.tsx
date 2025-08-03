import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { analyticsApi, TimeRange, ToolUsage } from '@/api/analytics';

interface ToolUsageDetailsProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function ToolUsageDetails({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: ToolUsageDetailsProps) {
  const { data: toolUsageData, isLoading } = useQuery({
    queryKey: ['toolUsageDetailed', sessionId, projectId, timeRange],
    queryFn: () =>
      analyticsApi.getToolUsageDetailed(sessionId, projectId, timeRange),
    refetchInterval: 5 * 60 * 1000, // 5 minutes cache
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">
          Tools Used
        </h3>
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full animate-pulse"
            >
              <div className="h-3 w-16 bg-layer-secondary rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const tools = toolUsageData?.tools || [];

  if (tools.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">
          Tools Used
        </h3>
        <div className="text-sm text-muted-c">No tools used in this period</div>
      </div>
    );
  }

  const getCategoryIcon = (category: ToolUsage['category']) => {
    switch (category) {
      case 'file':
        return '📁';
      case 'search':
        return '🔍';
      case 'execution':
        return '⚡';
      default:
        return '🔧';
    }
  };

  const getCategoryColor = (category: ToolUsage['category']) => {
    switch (category) {
      case 'file':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/20';
      case 'search':
        return 'border-green-500 bg-green-50 dark:bg-green-950/20';
      case 'execution':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-950/20';
    }
  };

  return (
    <div className={className}>
      <h3 className="text-base font-medium text-primary-c mb-4">Tools Used</h3>
      <div className="space-y-3">
        {/* Total summary */}
        <div className="text-sm text-muted-c mb-3">
          {toolUsageData?.total_calls} total calls across {tools.length} tool
          {tools.length !== 1 ? 's' : ''}
        </div>

        {/* Tool tags */}
        <div className="flex flex-wrap gap-2">
          {tools.map((tool) => (
            <div
              key={tool.name}
              className={`tag px-3 py-1 border rounded-full text-xs transition-all duration-200 hover:scale-105 ${getCategoryColor(
                tool.category
              )}`}
              title={`${tool.name} - ${tool.count} uses (${
                tool.percentage
              }%)\nCategory: ${tool.category}\nLast used: ${format(
                new Date(tool.last_used),
                'MMM d, yyyy at h:mm a'
              )}`}
            >
              <span className="mr-1">{getCategoryIcon(tool.category)}</span>
              <span className="text-tertiary-c font-medium">{tool.name}</span>
              <span className="ml-1 text-muted-c">× {tool.count}</span>
            </div>
          ))}
        </div>

        {/* Top tools breakdown */}
        {tools.length > 3 && (
          <div className="mt-4 space-y-2">
            <div className="text-xs text-muted-c font-medium">Top Tools:</div>
            {tools.slice(0, 3).map((tool) => (
              <div
                key={tool.name}
                className="flex justify-between items-center text-xs"
              >
                <div className="flex items-center gap-2">
                  <span>{getCategoryIcon(tool.category)}</span>
                  <span className="text-secondary-c">{tool.name}</span>
                </div>
                <div className="text-muted-c">
                  {tool.count} ({tool.percentage}%)
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
