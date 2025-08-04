import { Session } from '@/api/types';

interface SessionStatCardsProps {
  session: Session;
}

export function SessionStatCards({ session }: SessionStatCardsProps) {
  return (
    <>
      {/* Messages Count */}
      <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center">
        <div className="text-2xl font-semibold text-primary">
          {session.messageCount}
        </div>
        <div className="text-xs text-muted-c">Messages</div>
      </div>

      {/* Tools Used */}
      <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c">
        <div className="text-2xl font-semibold text-primary stat-value">
          {session.toolsUsed || 0}
        </div>
        <div className="text-xs text-muted-c stat-label">Tools Used</div>
      </div>

      {/* Success Rate - placeholder for now */}
      <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c">
        <div className="text-2xl font-semibold text-primary stat-value">
          100%
        </div>
        <div className="text-xs text-muted-c stat-label">Success Rate</div>
      </div>

      {/* Tokens */}
      <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c">
        <div className="text-2xl font-semibold text-primary stat-value">
          {formatTokenCount(session.totalTokens || 0)}
        </div>
        <div className="text-xs text-muted-c stat-label">Tokens</div>
        {session.totalCost && (
          <div className="mt-1 text-xs text-tertiary-c">
            ${session.totalCost.toFixed(2)} estimated
          </div>
        )}
      </div>
    </>
  );
}

function formatTokenCount(count: number): string {
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`;
  } else if (count >= 1000) {
    return `${Math.round(count / 1000)}K`;
  }
  return count.toString();
}

export function SessionCostCard({ session }: { session: Session }) {
  return (
    <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center transition-all duration-300 hover:border-primary-c">
      <div className="text-2xl font-semibold text-primary stat-value font-mono">
        ${session.totalCost?.toFixed(2) || '0.00'}
      </div>
      <div className="text-xs text-muted-c stat-label">Cost</div>
    </div>
  );
}
