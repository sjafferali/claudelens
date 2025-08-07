import { useSessions } from '@/hooks/useSessions';
import { formatDistanceToNow } from 'date-fns';
import { Loader2, MessageSquare, Clock, DollarSign } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getSessionTitle } from '@/utils/session';

export default function RecentSessions() {
  const { data, isLoading, error } = useSessions({
    limit: 5,
    sortOrder: 'desc',
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-6 w-6 animate-spin text-muted-c" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-muted-c">
          Failed to load recent conversations
        </p>
      </div>
    );
  }

  if (!data?.items || data.items.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-muted-c">No recent conversations found</p>
      </div>
    );
  }

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(cost);
  };

  return (
    <div className="space-y-3">
      {data.items.map((session) => (
        <Link
          key={session._id}
          to={`/sessions/${session._id}`}
          className="block bg-layer-primary border border-secondary-c rounded-lg p-4 hover:border-primary-c transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-primary-c truncate">
                {getSessionTitle(session)}
              </p>
              <div className="flex items-center gap-4 mt-2 text-xs text-muted-c">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDistanceToNow(new Date(session.started_at), {
                    addSuffix: true,
                  })}
                </span>
                <span className="flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  {session.message_count} messages
                </span>
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatCost(session.total_cost || 0)}
                </span>
              </div>
            </div>
          </div>
        </Link>
      ))}

      <div className="text-center pt-2">
        <Link
          to="/sessions"
          className="text-sm text-accent hover:text-accent-hover transition-colors"
        >
          View all conversations →
        </Link>
      </div>
    </div>
  );
}
