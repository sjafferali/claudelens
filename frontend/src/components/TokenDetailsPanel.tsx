import { useQuery } from '@tanstack/react-query';
import { analyticsApi, TimeRange } from '@/api/analytics';

interface TokenDetailsPanelProps {
  sessionId?: string;
  projectId?: string;
  timeRange?: TimeRange;
  className?: string;
}

export default function TokenDetailsPanel({
  sessionId,
  projectId,
  timeRange = TimeRange.LAST_30_DAYS,
  className = '',
}: TokenDetailsPanelProps) {
  const { data: tokenDetails, isLoading } = useQuery({
    queryKey: ['tokenEfficiencyDetailed', sessionId, projectId, timeRange],
    queryFn: () =>
      analyticsApi.getTokenEfficiencyDetailed(sessionId, timeRange, true),
    refetchInterval: 5 * 60 * 1000, // 5 minutes cache
  });

  if (isLoading) {
    return (
      <div className={className}>
        <h3 className="text-base font-medium text-primary-c mb-4">
          Token Usage
        </h3>
        <div className="space-y-4 animate-pulse">
          <div className="h-4 bg-layer-tertiary rounded"></div>
          <div className="h-8 bg-layer-tertiary rounded"></div>
          <div className="h-4 bg-layer-tertiary rounded"></div>
        </div>
      </div>
    );
  }

  if (!tokenDetails) {
    return null;
  }

  const { token_breakdown, efficiency_metrics, formatted_values } =
    tokenDetails;

  // Calculate percentages for visual breakdown
  const total = token_breakdown.total;
  const inputPercentage =
    total > 0 ? (token_breakdown.input_tokens / total) * 100 : 0;
  const outputPercentage =
    total > 0 ? (token_breakdown.output_tokens / total) * 100 : 0;
  const cacheCreationPercentage =
    total > 0 ? (token_breakdown.cache_creation / total) * 100 : 0;
  const cacheReadPercentage =
    total > 0 ? (token_breakdown.cache_read / total) * 100 : 0;

  return (
    <div className={className}>
      <h3 className="text-base font-medium text-primary-c mb-4">Token Usage</h3>

      {/* Visual breakdown bar */}
      <div className="mb-4">
        <div className="token-bar h-2 bg-layer-tertiary rounded-full overflow-hidden flex">
          {inputPercentage > 0 && (
            <div
              className="token-segment input bg-primary transition-all duration-300"
              style={{ width: `${inputPercentage}%` }}
              title={`Input: ${formatted_values.input} tokens`}
            />
          )}
          {outputPercentage > 0 && (
            <div
              className="token-segment output bg-green-500 transition-all duration-300"
              style={{ width: `${outputPercentage}%` }}
              title={`Output: ${formatted_values.output} tokens`}
            />
          )}
          {cacheCreationPercentage > 0 && (
            <div
              className="token-segment cache-creation bg-purple-500 transition-all duration-300"
              style={{ width: `${cacheCreationPercentage}%` }}
              title={`Cache Creation: ${formatted_values.cache_creation} tokens`}
            />
          )}
          {cacheReadPercentage > 0 && (
            <div
              className="token-segment cache-read bg-orange-500 transition-all duration-300"
              style={{ width: `${cacheReadPercentage}%` }}
              title={`Cache Read: ${formatted_values.cache_read} tokens`}
            />
          )}
        </div>
      </div>

      {/* Token breakdown stats */}
      <div className="token-stats space-y-2 mb-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-primary rounded-sm"></div>
            <span className="token-stat text-sm text-secondary-c">Input</span>
          </div>
          <span className="text-sm font-medium text-primary-c">
            {formatted_values.input}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-sm"></div>
            <span className="token-stat text-sm text-secondary-c">Output</span>
          </div>
          <span className="text-sm font-medium text-primary-c">
            {formatted_values.output}
          </span>
        </div>

        {token_breakdown.cache_creation > 0 && (
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-500 rounded-sm"></div>
              <span className="token-stat text-sm text-secondary-c">
                Cache Creation
              </span>
            </div>
            <span className="text-sm font-medium text-primary-c">
              {formatted_values.cache_creation}
            </span>
          </div>
        )}

        {token_breakdown.cache_read > 0 && (
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded-sm"></div>
              <span className="token-stat text-sm text-secondary-c">
                Cache Read
              </span>
            </div>
            <span className="text-sm font-medium text-primary-c">
              {formatted_values.cache_read}
            </span>
          </div>
        )}
      </div>

      {/* Efficiency metrics */}
      <div className="border-t border-secondary-c pt-4">
        <h4 className="text-sm font-medium text-secondary-c mb-3">
          Efficiency Metrics
        </h4>

        <div className="space-y-3">
          {efficiency_metrics.cache_hit_rate > 0 && (
            <div className="flex justify-between py-2 border-b border-secondary-c">
              <span className="text-sm text-muted-c">Cache Hit Rate</span>
              <div className="flex items-center gap-2">
                <span className="text-sm text-secondary-c font-mono">
                  {efficiency_metrics.cache_hit_rate.toFixed(1)}%
                </span>
                {efficiency_metrics.cache_hit_rate > 80 && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                    High
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="flex justify-between py-2 border-b border-secondary-c">
            <span className="text-sm text-muted-c">Input/Output Ratio</span>
            <span className="text-sm text-secondary-c font-mono">
              {efficiency_metrics.input_output_ratio.toFixed(2)}
            </span>
          </div>

          <div className="flex justify-between py-2 border-b border-secondary-c">
            <span className="text-sm text-muted-c">Avg per Message</span>
            <span className="text-sm text-secondary-c font-mono">
              {efficiency_metrics.avg_tokens_per_message.toFixed(1)}
            </span>
          </div>

          {efficiency_metrics.cost_per_token > 0 && (
            <div className="flex justify-between py-2">
              <span className="text-sm text-muted-c">Cost per Token</span>
              <span className="text-sm text-secondary-c font-mono">
                ${efficiency_metrics.cost_per_token.toFixed(6)}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
