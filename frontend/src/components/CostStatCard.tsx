import { useQuery } from '@tanstack/react-query';
import { analyticsApi, TimeRange } from '@/api/analytics';

interface CostStatCardProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function CostStatCard({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: CostStatCardProps) {
  const { data: costData, isLoading } = useQuery({
    queryKey: ['costSummary', sessionId, projectId, timeRange],
    queryFn: () => analyticsApi.getCostSummary(sessionId, projectId, timeRange),
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

  const formattedCost = costData?.formatted_cost || '$0.00';
  const trend = costData?.trend || 'stable';
  const period = costData?.period || '30d';

  // Get trend icon and color
  const getTrendStyle = () => {
    switch (trend) {
      case 'up':
        return { icon: '↗', color: 'text-red-500' };
      case 'down':
        return { icon: '↘', color: 'text-green-500' };
      default:
        return { icon: '→', color: 'text-gray-500' };
    }
  };

  const trendStyle = getTrendStyle();

  return (
    <div
      className={`bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c ${className}`}
    >
      <div className="text-2xl font-semibold text-primary stat-value font-mono">
        {formattedCost}
      </div>
      <div className="text-xs text-muted-c stat-label">Cost</div>

      {/* Period info */}
      <div className="mt-1 text-xs text-tertiary-c">{period}</div>

      {/* Trend indicator */}
      <div className="mt-1 flex items-center justify-center gap-1">
        <span className={`text-xs ${trendStyle.color}`}>{trendStyle.icon}</span>
        <span className="text-xs text-dim-c capitalize">{trend}</span>
      </div>
    </div>
  );
}
