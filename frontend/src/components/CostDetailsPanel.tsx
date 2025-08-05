import { useQuery } from '@tanstack/react-query';
import { analyticsApi, TimeRange } from '@/api/analytics';
import { formatCost } from '@/utils/format';

interface CostDetailsPanelProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function CostDetailsPanel({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: CostDetailsPanelProps) {
  const { data: costBreakdown, isLoading } = useQuery({
    queryKey: ['costBreakdown', sessionId, projectId, timeRange],
    queryFn: () =>
      analyticsApi.getCostBreakdown(sessionId, projectId, timeRange),
    refetchInterval: 5 * 60 * 1000, // 5 minutes cache
  });

  if (isLoading) {
    return (
      <div
        className={`bg-layer-primary border border-secondary-c rounded-lg p-4 ${className}`}
      >
        <div className="animate-pulse">
          <div className="h-5 bg-layer-tertiary rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-layer-tertiary rounded"></div>
            <div className="h-4 bg-layer-tertiary rounded w-3/4"></div>
            <div className="h-4 bg-layer-tertiary rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!costBreakdown) {
    return (
      <div
        className={`bg-layer-primary border border-secondary-c rounded-lg p-4 ${className}`}
      >
        <h3 className="text-base font-medium text-primary-c mb-4">
          Cost Breakdown
        </h3>
        <div className="text-center text-muted-c text-sm">
          No cost data available
        </div>
      </div>
    );
  }

  const { cost_breakdown, cost_metrics } = costBreakdown;

  return (
    <div
      className={`bg-layer-primary border border-secondary-c rounded-lg p-4 ${className}`}
    >
      <h3 className="text-base font-medium text-primary-c mb-4">
        Cost Breakdown
      </h3>

      {/* Cost by Model */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-secondary-c mb-3">By Model</h4>
        <div className="space-y-2">
          {cost_breakdown.by_model.length > 0 ? (
            cost_breakdown.by_model.map((item, index) => (
              <div
                key={index}
                className="flex justify-between items-center p-2 bg-layer-secondary rounded"
              >
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-primary-c cost-model">
                    {item.model}
                  </span>
                  <span className="text-xs text-muted-c">
                    {item.message_count} message
                    {item.message_count !== 1 ? 's' : ''}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono text-primary cost-amount">
                    {formatCost(item.cost)}
                  </div>
                  <div className="text-xs text-muted-c">
                    {item.percentage.toFixed(1)}%
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-muted-c text-center py-2">
              No model data available
            </div>
          )}
        </div>
      </div>

      {/* Most Expensive Model */}
      {cost_metrics.most_expensive_model && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-secondary-c mb-3">
            Most Used Model
          </h4>
          <div className="p-2 bg-layer-secondary rounded">
            <div className="text-sm font-medium text-primary-c">
              {cost_metrics.most_expensive_model}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
