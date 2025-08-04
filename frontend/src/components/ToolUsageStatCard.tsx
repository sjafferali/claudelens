import { useQuery } from '@tanstack/react-query';
import { analyticsApi, TimeRange } from '@/api/analytics';

interface ToolUsageStatCardProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function ToolUsageStatCard({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: ToolUsageStatCardProps) {
  const { data: toolUsage, isLoading } = useQuery({
    queryKey: ['toolUsageSummary', sessionId, projectId, timeRange],
    queryFn: () =>
      analyticsApi.getToolUsageSummary(sessionId, projectId, timeRange),
    enabled: (!!sessionId && sessionId !== 'undefined') || !!projectId, // Only query if we have a valid sessionId or projectId
    refetchInterval: 5 * 60 * 1000, // 5 minutes cache as per requirements
  });

  if (isLoading) {
    return (
      <div
        className={`bg-layer-primary border border-secondary-c rounded-lg p-4 text-center animate-pulse ${className}`}
      >
        <div className="h-8 bg-layer-tertiary rounded mb-2"></div>
        <div className="h-4 bg-layer-tertiary rounded"></div>
      </div>
    );
  }

  const toolCount = toolUsage?.unique_tools || 0;
  const totalCalls = toolUsage?.total_tool_calls || 0;

  return (
    <div
      className={`bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c ${className}`}
    >
      <div className="text-2xl font-semibold text-primary stat-value">
        {toolCount}
      </div>
      <div className="text-xs text-muted-c stat-label">Tools Used</div>
      {toolUsage?.most_used_tool && (
        <div className="mt-1 text-xs text-tertiary-c">
          Most used: {toolUsage.most_used_tool}
        </div>
      )}
      {totalCalls > 0 && (
        <div className="mt-1 text-xs text-dim-c">
          {totalCalls} total call{totalCalls !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
