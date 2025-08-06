import { useEffect, useState } from 'react';
import {
  GitFork,
  ExternalLink,
  Calendar,
  MessageSquare,
  X,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { sessionsApi } from '@/api/sessions';
import { Session } from '@/api/types';
import { SessionWithForks } from '@/types/session-with-forks';

interface Fork {
  sessionId: string;
  messageId: string;
  timestamp: string;
  description?: string;
  sessionData?: Session;
}

interface ForksPanelProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  currentSessionData?: Session;
}

export function ForksPanel({
  sessionId,
  isOpen,
  onClose,
  currentSessionData,
}: ForksPanelProps) {
  const navigate = useNavigate();
  const [forks, setForks] = useState<Fork[]>([]);
  const [forkedFrom, setForkedFrom] = useState<{
    sessionId: string;
    messageId: string;
    description?: string;
    sessionData?: Session;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadForkData = async () => {
      setLoading(true);
      try {
        // Get current session details to check if it's a fork
        const currentSession =
          currentSessionData || (await sessionsApi.getSession(sessionId));
        const sessionWithForks = currentSession as SessionWithForks;

        // Check if this session is a fork
        if (sessionWithForks.isFork && sessionWithForks.forkedFrom) {
          const forkedFromData = sessionWithForks.forkedFrom;
          setForkedFrom({
            sessionId: forkedFromData.sessionId,
            messageId: forkedFromData.messageId,
            description: forkedFromData.description,
          });

          // Try to load the parent session data
          try {
            const parentSession = await sessionsApi.getSession(
              forkedFromData.sessionId
            );
            setForkedFrom((prev) =>
              prev ? { ...prev, sessionData: parentSession } : null
            );
          } catch (error) {
            console.error('Failed to load parent session:', error);
          }
        }

        // Check if this session has forks
        if (sessionWithForks.forks && Array.isArray(sessionWithForks.forks)) {
          const forksData = sessionWithForks.forks;
          setForks(forksData);

          // Load session data for each fork
          const forksWithData = await Promise.all(
            forksData.map(async (fork) => {
              try {
                const sessionData = await sessionsApi.getSession(
                  fork.sessionId
                );
                return { ...fork, sessionData };
              } catch (error) {
                console.error(
                  `Failed to load fork session ${fork.sessionId}:`,
                  error
                );
                return fork;
              }
            })
          );
          setForks(forksWithData);
        }
      } catch (error) {
        console.error('Failed to load fork data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && sessionId) {
      loadForkData();
    }
  }, [isOpen, sessionId, currentSessionData]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const navigateToSession = (targetSessionId: string) => {
    navigate(`/sessions/${targetSessionId}`);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-slate-900 shadow-2xl z-40 flex flex-col border-l border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
            <GitFork className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Fork Relationships
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              View conversation branches
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          aria-label="Close forks panel"
        >
          <X className="h-5 w-5 text-slate-500 dark:text-slate-400" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div
              className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-amber-600"
              data-testid="loading-spinner"
            ></div>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Parent Session (if this is a fork) */}
            {forkedFrom && (
              <div>
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
                  <GitFork className="h-4 w-4 rotate-180" />
                  Forked From
                </h3>
                <div
                  className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-amber-300 dark:hover:border-amber-600 transition-colors cursor-pointer group"
                  onClick={() => navigateToSession(forkedFrom.sessionId)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        Parent Session
                      </p>
                      {forkedFrom.description && (
                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                          {forkedFrom.description}
                        </p>
                      )}
                    </div>
                    <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors" />
                  </div>

                  {forkedFrom.sessionData && (
                    <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(forkedFrom.sessionData.startedAt)}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" />
                        {forkedFrom.sessionData.messageCount} messages
                      </span>
                    </div>
                  )}

                  <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    Fork point: Message {forkedFrom.messageId.slice(0, 8)}...
                  </div>
                </div>
              </div>
            )}

            {/* Child Sessions (forks from this session) */}
            {forks.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
                  <GitFork className="h-4 w-4" />
                  Forked Sessions ({forks.length})
                </h3>
                <div className="space-y-3">
                  {forks.map((fork, index) => (
                    <div
                      key={fork.sessionId}
                      className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-amber-300 dark:hover:border-amber-600 transition-colors cursor-pointer group"
                      onClick={() => navigateToSession(fork.sessionId)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            Fork #{index + 1}
                          </p>
                          {fork.description && (
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                              {fork.description}
                            </p>
                          )}
                        </div>
                        <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors" />
                      </div>

                      {fork.sessionData && (
                        <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(fork.timestamp)}
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageSquare className="h-3 w-3" />
                            {fork.sessionData.messageCount} messages
                          </span>
                        </div>
                      )}

                      <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                        Forked at: Message {fork.messageId.slice(0, 8)}...
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!forkedFrom && forks.length === 0 && (
              <div className="text-center py-8">
                <GitFork className="h-12 w-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  No fork relationships found
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                  This session hasn't been forked and isn't a fork
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer with Info */}
      <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-amber-50 dark:bg-amber-900/20">
        <p className="text-xs text-amber-800 dark:text-amber-200 flex items-start gap-2">
          <GitFork className="h-3 w-3 mt-0.5 flex-shrink-0" />
          <span>
            Forks allow you to explore alternative conversation paths without
            affecting the original discussion.
          </span>
        </p>
      </div>
    </div>
  );
}
