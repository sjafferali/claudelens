import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/common';
import {
  useSessions,
  useSession,
  useSessionMessages,
} from '@/hooks/useSessions';
import { formatDistanceToNow } from 'date-fns';
import { Loader2 } from 'lucide-react';
import MessageList from '@/components/MessageList';

export default function Sessions() {
  const { sessionId } = useParams();

  if (sessionId) {
    return <SessionDetail sessionId={sessionId} />;
  }

  return <SessionsList />;
}

function SessionsList() {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 20;

  // Get project_id from URL search params
  const searchParams = new URLSearchParams(window.location.search);
  const projectId = searchParams.get('project_id') || undefined;

  const { data, isLoading, error } = useSessions({
    projectId,
    skip: currentPage * pageSize,
    limit: pageSize,
    sortBy: 'started_at',
    sortOrder: 'desc',
  });

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
          <p className="text-muted-foreground">
            Browse all your Claude conversation sessions
          </p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Failed to load sessions</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
        <p className="text-muted-foreground">
          Browse all your Claude conversation sessions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>
            Your conversation history with Claude
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {data?.items.length === 0 ? (
                  <p className="text-center py-8 text-muted-foreground">
                    No sessions found
                  </p>
                ) : (
                  data?.items.map((session) => (
                    <div
                      key={session._id}
                      onClick={() => navigate(`/sessions/${session._id}`)}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    >
                      <div className="space-y-1 flex-1">
                        <p className="font-medium">
                          {session.summary ||
                            `Session ${session.sessionId.slice(0, 8)}...`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {session.messageCount} messages •
                          {formatDistanceToNow(new Date(session.startedAt), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {session.totalCost
                          ? `$${session.totalCost.toFixed(2)}`
                          : 'N/A'}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {data && data.items.length > 0 && (
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-muted-foreground">
                    Showing {currentPage * pageSize + 1} to{' '}
                    {Math.min((currentPage + 1) * pageSize, data.total)} of{' '}
                    {data.total}
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 0}
                      className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={!data.has_more}
                      className="px-3 py-1 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SessionDetail({ sessionId }: { sessionId: string }) {
  const navigate = useNavigate();
  const { data: session, isLoading: sessionLoading } = useSession(sessionId);
  const { data: messages, isLoading: messagesLoading } =
    useSessionMessages(sessionId);

  if (sessionLoading || messagesLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!session || !messages) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Session Not Found
          </h2>
          <p className="text-muted-foreground">
            This session could not be found.
          </p>
        </div>
        <button
          onClick={() => navigate('/sessions')}
          className="text-sm text-primary hover:underline"
        >
          ← Back to sessions
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate('/sessions')}
            className="text-sm text-muted-foreground hover:text-foreground mb-2 flex items-center gap-1"
          >
            ← Back to sessions
          </button>
          <h2 className="text-3xl font-bold tracking-tight">
            {session.summary || `Session ${session.sessionId.slice(0, 8)}...`}
          </h2>
          <p className="text-muted-foreground">
            {formatDistanceToNow(new Date(session.startedAt), {
              addSuffix: true,
            })}{' '}
            •{session.messageCount} messages •
            {session.totalCost
              ? ` $${session.totalCost.toFixed(2)}`
              : ' No cost data'}
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Conversation</CardTitle>
            <CardDescription>Messages in this session</CardDescription>
          </CardHeader>
          <CardContent>
            <MessageList messages={messages.messages} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Session ID
              </p>
              <p className="text-sm font-mono">{session.sessionId}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Started
              </p>
              <p className="text-sm">
                {new Date(session.startedAt).toLocaleString()}
              </p>
            </div>
            {session.endedAt && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Ended
                </p>
                <p className="text-sm">
                  {new Date(session.endedAt).toLocaleString()}
                </p>
              </div>
            )}
            {session.modelsUsed && session.modelsUsed.length > 0 && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Models Used
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {session.modelsUsed.map((model, i) => (
                    <span
                      key={i}
                      className="text-xs px-2 py-1 bg-secondary rounded-md"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
