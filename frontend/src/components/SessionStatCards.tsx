import { Session } from '@/api/types';

interface SessionStatCardsProps {
  session: Session;
}

export function SessionStatCards({ session }: SessionStatCardsProps) {
  return (
    <>
      {/* Messages Count */}
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-500">
          {session.message_count}
        </div>
        <div className="text-xs text-muted-c font-medium">Messages</div>
      </div>

      {/* Tools Used */}
      <div className="text-center">
        <div className="text-2xl font-bold text-purple-500">
          {session.tools_used || 0}
        </div>
        <div className="text-xs text-muted-c font-medium">Tools Used</div>
      </div>

      {/* Success Rate - placeholder for now */}
      <div className="text-center">
        <div className="text-2xl font-bold text-green-500">100%</div>
        <div className="text-xs text-muted-c font-medium">Success Rate</div>
      </div>

      {/* Tokens */}
      <div className="text-center">
        <div className="text-2xl font-bold text-orange-500">
          {formatTokenCount(session.total_tokens || 0)}
        </div>
        <div className="text-xs text-muted-c font-medium">Tokens</div>
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
    <div className="text-center">
      <div className="text-3xl font-bold text-primary font-mono">
        ${session.total_cost?.toFixed(2) || '0.00'}
      </div>
      <div className="text-sm text-muted-c font-medium">Cost</div>
    </div>
  );
}
