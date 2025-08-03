import { useQuery } from '@tanstack/react-query';
import { analyticsApi, TimeRange } from '@/api/analytics';

interface SuccessRateCardProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function SuccessRateCard({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: SuccessRateCardProps) {
  const { data: sessionHealth, isLoading } = useQuery({
    queryKey: ['sessionHealth', sessionId, projectId, timeRange],
    queryFn: () => analyticsApi.getSessionHealth(sessionId, timeRange),
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

  const successRate = sessionHealth?.success_rate || 0;
  const totalOps = sessionHealth?.total_operations || 0;
  const errorCount = sessionHealth?.error_count || 0;

  // Color coding based on success rate as per requirements
  const getSuccessRateColor = (rate: number): string => {
    if (rate > 95) {
      return 'var(--success)'; // Green for >95%
    } else if (rate >= 80) {
      return 'var(--text-primary)'; // Normal color for 80-95%
    } else {
      return '#ef4444'; // Red for <80%
    }
  };

  const getHealthStatusIcon = (status: string): string => {
    switch (status) {
      case 'excellent':
        return '🟢';
      case 'good':
        return '🟡';
      case 'fair':
        return '🟠';
      case 'poor':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div
      className={`bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c ${className}`}
    >
      <div
        className="text-2xl font-semibold stat-value"
        style={{ color: getSuccessRateColor(successRate) }}
      >
        {successRate.toFixed(1)}%
      </div>
      <div className="text-xs text-muted-c stat-label">Success Rate</div>
      {sessionHealth?.health_status && (
        <div className="mt-1 text-xs text-tertiary-c flex items-center justify-center gap-1">
          <span>{getHealthStatusIcon(sessionHealth.health_status)}</span>
          <span className="capitalize">{sessionHealth.health_status}</span>
        </div>
      )}
      {totalOps > 0 && (
        <div className="mt-1 text-xs text-dim-c">
          {totalOps} operation{totalOps !== 1 ? 's' : ''}
          {errorCount > 0 && (
            <span className="text-red-400 ml-1">
              ({errorCount} error{errorCount !== 1 ? 's' : ''})
            </span>
          )}
        </div>
      )}
    </div>
  );
}
