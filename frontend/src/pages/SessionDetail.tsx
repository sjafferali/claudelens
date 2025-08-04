import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  Search,
  Copy,
  Pin,
  Download,
  ChevronDown,
  ChevronUp,
  Check,
  Wrench,
  Terminal,
} from 'lucide-react';
import { format } from 'date-fns';
import {
  useSession,
  useSessionMessages,
  useGenerateSessionSummary,
} from '@/hooks/useSessions';
import { useMessageCosts } from '@/hooks/useMessageCosts';
import { cn } from '@/utils/cn';
import { Message } from '@/api/types';
import ToolUsageStatCard from '@/components/ToolUsageStatCard';
import ToolUsageDetails from '@/components/ToolUsageDetails';
import SuccessRateCard from '@/components/SuccessRateCard';
import ErrorDetailsPanel from '@/components/ErrorDetailsPanel';
import TokenStatCard from '@/components/TokenStatCard';
import TokenDetailsPanel from '@/components/TokenDetailsPanel';
import CostStatCard from '@/components/CostStatCard';
import CostDetailsPanel from '@/components/CostDetailsPanel';
import SessionTopics from '@/components/SessionTopics';
import { getMessageUuid, getMessageCost } from '@/types/message-extensions';
import { getSessionTitle } from '@/utils/session';

export default function SessionDetail() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const targetMessageId = searchParams.get('messageId');
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const MESSAGES_PER_PAGE = 100;

  // Reset pagination when session changes
  useEffect(() => {
    setCurrentPage(0);
    setAllMessages([]);
    setHasLoadedInitial(false);
  }, [sessionId]);

  const { data: session, isLoading: sessionLoading } = useSession(sessionId!);
  const {
    data: messages,
    isLoading: messagesLoading,
    isFetching,
  } = useSessionMessages(
    sessionId!,
    currentPage * MESSAGES_PER_PAGE,
    MESSAGES_PER_PAGE
  );
  const generateSummary = useGenerateSessionSummary();

  // State to accumulate all loaded messages
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const [hasLoadedInitial, setHasLoadedInitial] = useState(false);

  // Update accumulated messages when new page loads
  useEffect(() => {
    if (messages?.messages && !messagesLoading) {
      if (currentPage === 0) {
        // First page - replace all messages
        setAllMessages(messages.messages);
        setHasLoadedInitial(true);
      } else {
        // Subsequent pages - append messages
        setAllMessages((prev) => [...prev, ...messages.messages]);
      }
    }
  }, [messages, currentPage, messagesLoading]);

  // Calculate if there are more messages to load
  const hasMoreMessages = session && allMessages.length < session.messageCount;
  const canLoadMore = hasMoreMessages && !isFetching && hasLoadedInitial;

  // Handle loading more messages with scroll position preservation
  const handleLoadMore = () => {
    if (!scrollContainerRef.current) {
      setCurrentPage((prev) => prev + 1);
      return;
    }

    // Save current scroll position from bottom
    const container = scrollContainerRef.current;
    const scrollBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    // Set up observer to restore scroll position when content changes
    const observer = new MutationObserver(() => {
      if (scrollContainerRef.current) {
        const newScrollTop =
          scrollContainerRef.current.scrollHeight -
          scrollBottom -
          scrollContainerRef.current.clientHeight;
        scrollContainerRef.current.scrollTop = newScrollTop;
      }
      observer.disconnect();
    });

    // Start observing
    observer.observe(container, { childList: true, subtree: true });

    // Load more messages
    setCurrentPage((prev) => prev + 1);

    // Disconnect observer after timeout as fallback
    setTimeout(() => observer.disconnect(), 1000);
  };

  // Calculate costs for messages
  const { costMap } = useMessageCosts(sessionId, allMessages);

  const [viewMode, setViewMode] = useState<'timeline' | 'compact' | 'raw'>(
    'timeline'
  );

  // Clear scroll container ref when view mode changes
  useEffect(() => {
    scrollContainerRef.current = null;
  }, [viewMode]);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [collapsedToolResults, setCollapsedToolResults] = useState<Set<string>>(
    new Set()
  );
  const [expandedToolPairs, setExpandedToolPairs] = useState<Set<string>>(
    new Set()
  );

  // Filter messages based on search
  const filteredMessages = allMessages.filter((msg) =>
    msg.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Auto-collapse tool results on load
  useEffect(() => {
    if (allMessages.length > 0) {
      const toolResultIds = allMessages
        .filter((msg) => msg.content.startsWith('[Tool Result:'))
        .map((msg) => msg._id);
      setCollapsedToolResults(new Set(toolResultIds));
    }
  }, [allMessages]);

  // Scroll to target message when navigating from search
  useEffect(() => {
    if (targetMessageId && messages && !messagesLoading) {
      // Give the DOM time to render
      setTimeout(() => {
        const targetElement = messageRefs.current[targetMessageId];
        if (targetElement) {
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // Highlight the message temporarily
          targetElement.classList.add(
            'ring-2',
            'ring-primary',
            'ring-offset-2'
          );
          setTimeout(() => {
            targetElement.classList.remove(
              'ring-2',
              'ring-primary',
              'ring-offset-2'
            );
          }, 2000);
        }
      }, 100);
    }
  }, [targetMessageId, messages, messagesLoading]);

  const toggleExpanded = (messageId: string) => {
    setExpandedMessages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const toggleToolResult = (messageId: string) => {
    setCollapsedToolResults((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const toggleToolPairExpanded = (pairId: string) => {
    setExpandedToolPairs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(pairId)) {
        newSet.delete(pairId);
      } else {
        newSet.add(pairId);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getMessageColors = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return {
          avatar: 'bg-gradient-to-br from-secondary to-purple-600',
          bg: 'bg-layer-secondary',
        };
      case 'assistant':
        return {
          avatar: 'bg-gradient-to-br from-primary to-primary-hover',
          bg: 'bg-layer-secondary',
        };
      case 'tool_use':
      case 'tool_result':
        return {
          avatar: 'bg-gradient-to-br from-primary to-primary-hover',
          bg: 'bg-layer-secondary',
        };
      default:
        return {
          avatar: 'bg-gradient-to-br from-gray-500 to-gray-600',
          bg: 'bg-layer-secondary',
        };
    }
  };

  const getMessageLabel = (type: Message['type'], content?: string) => {
    // Special handling for legacy tool result messages
    if (
      type === 'user' &&
      content &&
      content.trim().startsWith('--- Tool Result ---')
    ) {
      return 'System';
    }

    switch (type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Claude';
      case 'tool_use':
        return 'Claude';
      case 'tool_result':
        return 'System';
      default:
        return type;
    }
  };

  const getAvatarText = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return 'Y';
      case 'assistant':
      case 'tool_use':
      case 'tool_result':
        return 'C';
      default:
        return '?';
    }
  };

  if (sessionLoading || messagesLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!session || !messages) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h2 className="text-2xl font-bold text-primary-c mb-2">
          Session Not Found
        </h2>
        <p className="text-muted-c mb-4">This session could not be found.</p>
        <button
          onClick={() => navigate('/sessions')}
          className="text-primary hover:text-primary-hover"
        >
          ← Back to sessions
        </button>
      </div>
    );
  }

  const duration = session.endedAt
    ? Math.floor(
        (new Date(session.endedAt).getTime() -
          new Date(session.startedAt).getTime()) /
          1000
      )
    : 0;
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = duration % 60;

  return (
    <div className="flex flex-col h-screen bg-layer-primary overflow-hidden">
      {/* Header */}
      <div className="bg-layer-secondary border-b border-primary-c px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-muted-c text-sm mb-2">
              <button
                onClick={() => navigate('/sessions')}
                className="flex items-center gap-1 hover:text-primary-c transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to sessions
              </button>
            </div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-medium text-primary-c">
                {getSessionTitle(session)}
              </h2>
              {!session.summary && (
                <button
                  onClick={() => generateSummary.mutate(sessionId!)}
                  disabled={generateSummary.isPending}
                  className="text-xs px-2 py-1 bg-primary text-white rounded hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generateSummary.isPending
                    ? 'Generating...'
                    : 'Generate Title'}
                </button>
              )}
            </div>
            <div className="flex items-center gap-4 mt-1 text-sm text-muted-c">
              <span>
                {format(new Date(session.startedAt), 'MMM d, yyyy')} at{' '}
                {format(new Date(session.startedAt), 'h:mm a')}
              </span>
              <span>•</span>
              <span>{session.messageCount} messages</span>
              <span>•</span>
              <span>
                {session.totalCost
                  ? `$${session.totalCost.toFixed(2)}`
                  : 'No cost data'}
              </span>
            </div>
          </div>
          <div className="flex items-center bg-layer-tertiary border border-primary-c rounded-lg px-4 py-2">
            <Search className="h-4 w-4 text-muted-c mr-2" />
            <input
              type="text"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none outline-none text-primary-c placeholder-muted-c w-64"
            />
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden min-h-0">
        {/* Conversation Panel */}
        <div className="flex-1 flex flex-col bg-layer-primary overflow-hidden">
          <div className="bg-layer-secondary px-6 py-4 border-b border-primary-c flex items-center justify-between">
            <h3 className="text-base font-medium text-primary-c">
              Conversation
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('timeline')}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-md transition-all',
                  viewMode === 'timeline'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                )}
              >
                Timeline
              </button>
              <button
                onClick={() => setViewMode('compact')}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-md transition-all',
                  viewMode === 'compact'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                )}
              >
                Compact
              </button>
              <button
                onClick={() => setViewMode('raw')}
                className={cn(
                  'px-3 py-1.5 text-sm rounded-md transition-all',
                  viewMode === 'raw'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                )}
              >
                Raw
              </button>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {viewMode === 'timeline' && (
              <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin"
              >
                <TimelineView
                  messages={filteredMessages}
                  expandedMessages={expandedMessages}
                  collapsedToolResults={collapsedToolResults}
                  expandedToolPairs={expandedToolPairs}
                  copiedId={copiedId}
                  costMap={costMap}
                  onToggleExpanded={toggleExpanded}
                  onToggleToolResult={toggleToolResult}
                  onToggleToolPairExpanded={toggleToolPairExpanded}
                  onCopy={copyToClipboard}
                  messageRefs={messageRefs}
                  getMessageColors={getMessageColors}
                  getMessageLabel={getMessageLabel}
                  getAvatarText={getAvatarText}
                />
                {canLoadMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={handleLoadMore}
                      disabled={isFetching}
                      className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isFetching ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                          Loading...
                        </span>
                      ) : (
                        `Load More (${allMessages.length} of ${session.messageCount})`
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
            {viewMode === 'compact' && (
              <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin"
              >
                <CompactView
                  messages={filteredMessages}
                  getMessageLabel={getMessageLabel}
                  getMessageColors={getMessageColors}
                />
                {canLoadMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={handleLoadMore}
                      disabled={isFetching}
                      className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isFetching ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                          Loading...
                        </span>
                      ) : (
                        `Load More (${allMessages.length} of ${session.messageCount})`
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
            {viewMode === 'raw' && (
              <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
                <RawView
                  messages={filteredMessages}
                  onCopy={copyToClipboard}
                  copiedId={copiedId}
                />
                {canLoadMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={handleLoadMore}
                      disabled={isFetching}
                      className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isFetching ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                          Loading...
                        </span>
                      ) : (
                        `Load More (${allMessages.length} of ${session.messageCount})`
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Details Panel */}
        <div className="w-80 bg-layer-secondary border-l border-primary-c overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
            <div className="space-y-8">
              {/* Session Details */}
              <div>
                <h3 className="text-base font-medium text-primary-c mb-4">
                  Session Details
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-secondary-c">
                    <span className="text-sm text-muted-c">Session ID</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-secondary-c font-mono text-xs">
                        {session.sessionId}
                      </span>
                      <button
                        onClick={() =>
                          copyToClipboard(session.sessionId, 'session-id')
                        }
                        className="p-1 hover:bg-layer-tertiary rounded transition-colors"
                        title="Copy Session ID"
                      >
                        {copiedId === 'session-id' ? (
                          <Check className="h-3 w-3 text-green-500" />
                        ) : (
                          <Copy className="h-3 w-3 text-muted-c" />
                        )}
                      </button>
                    </div>
                  </div>
                  <div className="flex justify-between py-2 border-b border-secondary-c">
                    <span className="text-sm text-muted-c">Started</span>
                    <span className="text-sm text-secondary-c font-mono">
                      {format(
                        new Date(session.startedAt),
                        'M/d/yyyy, h:mm:ss a'
                      )}
                    </span>
                  </div>
                  {session.endedAt && (
                    <div className="flex justify-between py-2 border-b border-secondary-c">
                      <span className="text-sm text-muted-c">Ended</span>
                      <span className="text-sm text-secondary-c font-mono">
                        {format(
                          new Date(session.endedAt),
                          'M/d/yyyy, h:mm:ss a'
                        )}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between py-2 border-b border-secondary-c">
                    <span className="text-sm text-muted-c">Duration</span>
                    <span className="text-sm text-secondary-c font-mono">
                      {hours}h {minutes}m {seconds}s
                    </span>
                  </div>
                </div>
              </div>

              {/* Statistics */}
              <div>
                <h3 className="text-base font-medium text-primary-c mb-4">
                  Statistics
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center">
                    <div className="text-2xl font-semibold text-primary">
                      {session.messageCount}
                    </div>
                    <div className="text-xs text-muted-c">Messages</div>
                  </div>
                  <ToolUsageStatCard sessionId={sessionId} />
                  <SuccessRateCard sessionId={sessionId} />
                  <TokenStatCard sessionId={sessionId} />
                </div>

                {/* Additional Stats */}
                <div className="mt-4 grid grid-cols-1 gap-4">
                  <CostStatCard sessionId={sessionId} />
                </div>
              </div>

              {/* Tools Used */}
              <ToolUsageDetails sessionId={sessionId} />

              {/* Token Usage Details */}
              <TokenDetailsPanel sessionId={sessionId} />

              {/* Cost Details */}
              <CostDetailsPanel sessionId={sessionId} />

              {/* Error Details */}
              <ErrorDetailsPanel sessionId={sessionId} />

              {/* Topics */}
              <SessionTopics sessionId={sessionId!} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Timeline View Component
interface TimelineViewProps {
  messages: Message[];
  expandedMessages: Set<string>;
  collapsedToolResults: Set<string>;
  expandedToolPairs: Set<string>;
  copiedId: string | null;
  costMap?: Map<string, number>;
  onToggleExpanded: (messageId: string) => void;
  onToggleToolResult: (messageId: string) => void;
  onToggleToolPairExpanded: (pairId: string) => void;
  onCopy: (text: string, messageId: string) => void;
  getMessageColors: (type: Message['type']) => { avatar: string; bg: string };
  getMessageLabel: (type: Message['type'], content?: string) => string;
  getAvatarText: (type: Message['type']) => string;
  messageRefs: React.MutableRefObject<{ [key: string]: HTMLDivElement | null }>;
}

function TimelineView({
  messages,
  expandedMessages,
  collapsedToolResults,
  expandedToolPairs,
  copiedId,
  costMap,
  onToggleExpanded,
  onToggleToolResult,
  onToggleToolPairExpanded,
  onCopy,
  getMessageColors,
  getMessageLabel,
  getAvatarText,
  messageRefs,
}: TimelineViewProps) {
  // Format message content based on type and content
  const formatMessageContent = (message: Message) => {
    // Handle tool_result messages
    if (message.type === 'tool_result') {
      // Try to identify the tool type from content
      const content = message.content.trim();

      // TodoWrite results
      if (content.startsWith('Todos have been modified successfully')) {
        return '✅ Todo list updated successfully';
      }

      // Read tool results (file contents)
      else if (
        content.includes('File contents:') ||
        content.includes('cat -n') ||
        /^\s*\d+→/.test(content)
      ) {
        const lines = content.split('\n');
        const preview = lines.slice(0, 5).join('\n');
        return `📄 File contents:\n${preview}${lines.length > 5 ? '\n...' : ''}`;
      }

      // Write/Edit tool results
      else if (
        content.includes('File created successfully') ||
        content.includes('has been updated') ||
        content.includes('File written successfully')
      ) {
        return `✅ File operation completed`;
      }

      // Grep/Glob search results
      else if (
        content.startsWith('Found') &&
        (content.includes('files') || content.includes('matches'))
      ) {
        const lines = content.split('\n');
        if (lines.length > 10) {
          return `🔍 Search results:\n${lines.slice(0, 10).join('\n')}\n... and ${lines.length - 10} more`;
        }
        return `🔍 Search results:\n${content}`;
      } else if (
        content === 'No matches found' ||
        content === 'No files found'
      ) {
        return '❌ No matches found';
      }

      // LS results
      else if (
        content.includes('total') &&
        (content.includes('drwx') || content.includes('-rw'))
      ) {
        const lines = content.split('\n');
        const fileCount = lines.filter(
          (l) => l.trim() && !l.startsWith('total')
        ).length;
        return `📁 Directory listing: ${fileCount} items`;
      }

      // Bash command results
      else if (
        content.includes('npm install') ||
        content.includes('poetry install')
      ) {
        return '📦 Dependencies installed successfully';
      } else if (
        content.includes('npm run') ||
        content.includes('poetry run')
      ) {
        return '🚀 Command executed successfully';
      } else if (
        content.includes('git') &&
        (content.includes('commit') || content.includes('branch'))
      ) {
        return '🔧 Git operation completed';
      } else if (
        content.includes('docker') &&
        (content.includes('built') || content.includes('Started'))
      ) {
        return '🐳 Docker operation completed';
      } else if (
        content.match(/^\s*\w+\s+\w+\s+\w+\s+\w+\s+\w+/) &&
        content.includes('ago')
      ) {
        // Docker ps output
        return '🐳 Container status retrieved';
      } else if (
        content.includes('pip install') ||
        content.includes('Successfully installed')
      ) {
        return '📦 Python packages installed';
      } else if (content.includes('chmod') || content.includes('permissions')) {
        return '🔐 Permissions updated';
      } else if (content.includes('mkdir') && content.includes('created')) {
        return '📁 Directory created';
      } else if (
        content.includes('curl') &&
        (content.includes('200') || content.includes('OK'))
      ) {
        return '🌐 HTTP request successful';
      }

      // Error handling
      else if (
        content.includes('Error') ||
        content.includes('error') ||
        content.includes('ERROR')
      ) {
        const firstLine = content.split('\n')[0];
        return `❌ Error: ${firstLine}`;
      } else if (
        content.includes('command not found') ||
        content.includes('No such file or directory')
      ) {
        const firstLine = content.split('\n')[0];
        return `⚠️ Warning: ${firstLine}`;
      }

      // Task results
      else if (
        content.includes('Task completed') ||
        content.includes('Agent task completed')
      ) {
        return '🤖 Task completed successfully';
      }

      // WebFetch/WebSearch results
      else if (content.includes('<!DOCTYPE') || content.includes('<html')) {
        return '🌐 Web content fetched successfully';
      } else if (
        content.includes('search results') ||
        content.includes('Search Results')
      ) {
        return '🔍 Web search completed';
      }

      // Notebook operations
      else if (content.includes('cells') && content.includes('notebook')) {
        return '📓 Notebook operation completed';
      }

      // Generic success patterns
      else if (
        content.includes('Successfully') ||
        content.includes('successfully') ||
        content.includes('Success')
      ) {
        const firstLine = content.split('\n')[0];
        return `✅ ${firstLine}`;
      }

      // Plan mode results
      else if (
        content.includes('Plan approved') ||
        content.includes('Exiting plan mode')
      ) {
        return '📋 Plan mode completed';
      }

      // Long results - show preview
      else if (content.length > 200) {
        const preview = content.substring(0, 200);
        const lineCount = content.split('\n').length;
        return `📥 Tool Result (${lineCount} lines):\n${preview}...`;
      }

      // Default
      else {
        return `📥 Tool Result:\n${content}`;
      }
    }

    // Handle tool_use messages with JSON content
    if (message.type === 'tool_use') {
      try {
        const parsed = JSON.parse(message.content);
        if (parsed.name) {
          // Format tool use more nicely
          let toolInfo = `🔧 Tool: ${parsed.name}`;

          // Add specific formatting for each tool type
          switch (parsed.name) {
            // File Operations
            case 'Read':
              if (parsed.input?.file_path) {
                toolInfo += `\n📄 Reading: ${parsed.input.file_path}`;
                if (parsed.input.offset || parsed.input.limit) {
                  toolInfo += ` (lines ${parsed.input.offset || 0}-${(parsed.input.offset || 0) + (parsed.input.limit || 'end')})`;
                }
              }
              break;

            case 'Write':
              if (parsed.input?.file_path) {
                toolInfo += `\n✏️ Writing to: ${parsed.input.file_path}`;
                if (parsed.input.content) {
                  const lines = parsed.input.content.split('\n').length;
                  toolInfo += ` (${lines} line${lines > 1 ? 's' : ''})`;
                }
              }
              break;

            case 'Edit':
              if (parsed.input?.file_path) {
                toolInfo += `\n✏️ Editing: ${parsed.input.file_path}`;
                if (parsed.input.replace_all) {
                  toolInfo += ' (replace all occurrences)';
                }
              }
              break;

            case 'MultiEdit':
              if (parsed.input?.file_path) {
                toolInfo += `\n✏️ Multiple edits to: ${parsed.input.file_path}`;
                if (parsed.input.edits && Array.isArray(parsed.input.edits)) {
                  toolInfo += ` (${parsed.input.edits.length} edit${parsed.input.edits.length > 1 ? 's' : ''})`;
                }
              }
              break;

            // Directory Operations
            case 'LS':
              if (parsed.input?.path) {
                toolInfo += `\n📁 Listing: ${parsed.input.path}`;
                if (parsed.input.ignore && parsed.input.ignore.length > 0) {
                  toolInfo += ` (ignoring ${parsed.input.ignore.length} pattern${parsed.input.ignore.length > 1 ? 's' : ''})`;
                }
              }
              break;

            case 'Glob':
              if (parsed.input?.pattern) {
                toolInfo += `\n🔍 Pattern: ${parsed.input.pattern}`;
                if (parsed.input.path) {
                  toolInfo += ` in ${parsed.input.path}`;
                }
              }
              break;

            // Search Operations
            case 'Grep':
              if (parsed.input?.pattern) {
                toolInfo += `\n🔍 Searching for: ${parsed.input.pattern}`;
                if (parsed.input.path) {
                  toolInfo += ` in ${parsed.input.path}`;
                }
                if (parsed.input.glob) {
                  toolInfo += ` (files matching ${parsed.input.glob})`;
                }
                if (parsed.input.type) {
                  toolInfo += ` (${parsed.input.type} files)`;
                }
              }
              break;

            // Command Execution
            case 'Bash':
              if (parsed.input?.command) {
                const cmd = parsed.input.command;
                toolInfo += `\n💻 Command: ${cmd.length > 60 ? cmd.substring(0, 60) + '...' : cmd}`;
                if (parsed.input.timeout) {
                  toolInfo += ` (timeout: ${parsed.input.timeout}ms)`;
                }
              }
              break;

            // Web Operations
            case 'WebSearch':
              if (parsed.input?.query) {
                toolInfo += `\n🌐 Searching web for: "${parsed.input.query}"`;
                if (
                  parsed.input.allowed_domains &&
                  parsed.input.allowed_domains.length > 0
                ) {
                  toolInfo += ` (only ${parsed.input.allowed_domains.join(', ')})`;
                }
              }
              break;

            case 'WebFetch':
              if (parsed.input?.url) {
                toolInfo += `\n🌐 Fetching: ${parsed.input.url}`;
                if (parsed.input.prompt) {
                  toolInfo += `\n💭 Purpose: ${parsed.input.prompt.substring(0, 50)}${parsed.input.prompt.length > 50 ? '...' : ''}`;
                }
              }
              break;

            // Notebook Operations
            case 'NotebookRead':
              if (parsed.input?.notebook_path) {
                toolInfo += `\n📓 Reading notebook: ${parsed.input.notebook_path}`;
                if (parsed.input.cell_id) {
                  toolInfo += ` (cell ${parsed.input.cell_id})`;
                }
              }
              break;

            case 'NotebookEdit':
              if (parsed.input?.notebook_path) {
                toolInfo += `\n📓 Editing notebook: ${parsed.input.notebook_path}`;
                if (parsed.input.edit_mode) {
                  toolInfo += ` (${parsed.input.edit_mode})`;
                }
                if (parsed.input.cell_type) {
                  toolInfo += ` - ${parsed.input.cell_type} cell`;
                }
              }
              break;

            // Task Management
            case 'TodoWrite':
              if (parsed.input?.todos) {
                const todos = parsed.input.todos;
                if (Array.isArray(todos) && todos.length > 0) {
                  const pending = todos.filter(
                    (t) => t.status === 'pending'
                  ).length;
                  const inProgress = todos.filter(
                    (t) => t.status === 'in_progress'
                  ).length;
                  const completed = todos.filter(
                    (t) => t.status === 'completed'
                  ).length;
                  toolInfo += `\n📝 Todo list: ${todos.length} item${todos.length > 1 ? 's' : ''}`;
                  toolInfo += `\n  ⏳ Pending: ${pending} | 🔄 In Progress: ${inProgress} | ✅ Completed: ${completed}`;

                  // Show actual todo items
                  toolInfo += '\n\n  Tasks:';
                  todos.forEach((todo, index) => {
                    const statusIcon =
                      todo.status === 'completed'
                        ? '✅'
                        : todo.status === 'in_progress'
                          ? '🔄'
                          : '⏳';
                    const priority =
                      todo.priority === 'high'
                        ? '🔴'
                        : todo.priority === 'medium'
                          ? '🟡'
                          : '🟢';

                    // Truncate long todo content
                    const content =
                      todo.content && todo.content.length > 60
                        ? todo.content.substring(0, 60) + '...'
                        : todo.content || 'No description';

                    toolInfo += `\n  ${index + 1}. ${statusIcon} ${priority} ${content}`;
                  });

                  // Limit display to first 10 todos if there are many
                  if (todos.length > 10) {
                    toolInfo += `\n  ... and ${todos.length - 10} more tasks`;
                  }
                }
              }
              break;

            case 'Task':
              if (parsed.input?.description) {
                toolInfo += `\n🤖 Agent task: ${parsed.input.description}`;
                if (parsed.input.subagent_type) {
                  toolInfo += ` (${parsed.input.subagent_type})`;
                }
              }
              break;

            case 'ExitPlanMode':
            case 'exit_plan_mode': // Handle lowercase variant
              toolInfo += '\n📋 Exiting plan mode';
              if (parsed.input?.plan) {
                const planLines = parsed.input.plan.split('\n').length;
                toolInfo += ` (${planLines} line plan)`;
              }
              break;

            default:
              // For any unknown tools, show basic info
              if (parsed.input) {
                const keys = Object.keys(parsed.input);
                if (keys.length > 0) {
                  toolInfo += `\n📦 Parameters: ${keys.join(', ')}`;
                }
              }
          }

          return toolInfo;
        }
      } catch {
        // If not JSON, return as is
      }
    }

    // Handle assistant messages with tool uses
    if (
      message.type === 'assistant' &&
      (message.content.startsWith('Reading file:') ||
        message.content.startsWith('Writing to file:') ||
        message.content.startsWith('Editing file:') ||
        message.content.startsWith('Running command:') ||
        message.content.startsWith('Updating todo list') ||
        message.content.startsWith('Searching for:') ||
        message.content.startsWith('Using tool:'))
    ) {
      // These are already nicely formatted by the backend
      return `🔧 ${message.content}`;
    }

    // Final check: if content looks like JSON structure, try to extract meaningful text
    if (
      message.content.startsWith('1→') ||
      message.content.includes('"type":') ||
      message.content.includes('"content":')
    ) {
      // This might be improperly formatted content
      try {
        // Try to parse as JSON first
        const parsed = JSON.parse(message.content);
        if (parsed.content) {
          if (typeof parsed.content === 'string') {
            return parsed.content;
          } else if (Array.isArray(parsed.content)) {
            // Extract text from content array
            const textParts = parsed.content
              .filter((part: { type?: string }) => part.type === 'text')
              .map((part: { text?: string }) => part.text || '')
              .join('\n');
            return textParts || message.content;
          }
        }
      } catch {
        // If JSON parsing fails, try to extract content between quotes
        const match = message.content.match(/"content"\s*:\s*"([^"]+)"/);
        if (match && match[1]) {
          return match[1];
        }

        // Look for actual message text patterns
        const textMatch = message.content.match(/"text"\s*:\s*"([^"]+)"/);
        if (textMatch && textMatch[1]) {
          return textMatch[1];
        }
      }
    }

    return message.content;
  };
  // Group consecutive tool_use and tool_result messages into pairs
  const messageGroups: Array<{
    type: 'single' | 'tool_pair';
    messages: Message[];
  }> = [];

  let i = 0;
  while (i < messages.length) {
    const message = messages[i];

    if (message.type === 'tool_use') {
      // Look for the corresponding tool_result
      const toolUseMessage = message;
      const nextMessage = messages[i + 1];

      if (nextMessage && nextMessage.type === 'tool_result') {
        // Found a tool_use/tool_result pair
        messageGroups.push({
          type: 'tool_pair',
          messages: [toolUseMessage, nextMessage],
        });
        i += 2; // Skip both messages
      } else {
        // Tool use without result
        messageGroups.push({
          type: 'single',
          messages: [toolUseMessage],
        });
        i++;
      }
    } else {
      // Regular message
      messageGroups.push({
        type: 'single',
        messages: [message],
      });
      i++;
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {messageGroups.map((group) => {
        if (group.type === 'single') {
          const message = group.messages[0];
          const isExpanded = expandedMessages.has(message._id);
          const isToolResultCollapsed = collapsedToolResults.has(message._id);
          const colors = getMessageColors(message.type);

          return (
            <div
              key={message._id}
              className="group"
              ref={(el) => {
                messageRefs.current[message._id] = el;
              }}
            >
              <div
                className={cn(
                  'rounded-xl p-4',
                  colors.bg,
                  'border border-secondary-c hover:border-primary-c transition-all'
                )}
              >
                <div className="flex gap-4">
                  <div
                    className={cn(
                      'w-9 h-9 rounded-lg flex items-center justify-center text-white font-semibold flex-shrink-0',
                      colors.avatar
                    )}
                  >
                    {getAvatarText(message.type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-primary-c">
                          {getMessageLabel(message.type, message.content)}
                        </span>
                        {message.model && (
                          <span className="text-xs px-2 py-0.5 bg-layer-tertiary rounded-full text-muted-c">
                            {message.model}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        {getMessageCost(message) ||
                        (costMap &&
                          costMap.get(getMessageUuid(message) || '')) ? (
                          <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                            $
                            {(
                              getMessageCost(message) ||
                              costMap?.get(getMessageUuid(message) || '') ||
                              0
                            ).toFixed(4)}
                          </span>
                        ) : null}
                        <span className="text-xs text-dim-c">
                          {format(
                            new Date(message.timestamp),
                            'MMM d, HH:mm:ss'
                          )}
                        </span>
                      </div>
                    </div>

                    {/* Tool Result - Collapsible */}
                    {message.content.startsWith('[Tool Result:') &&
                    isToolResultCollapsed ? (
                      <div className="inline-flex items-center gap-2 bg-layer-tertiary px-3 py-1 rounded-md text-sm text-muted-c">
                        <span>Tool Result</span>
                        <button
                          onClick={() => onToggleToolResult(message._id)}
                          className="text-primary hover:text-primary-hover text-xs"
                        >
                          Show
                        </button>
                      </div>
                    ) : (
                      <div className="text-secondary-c whitespace-pre-wrap break-words">
                        {(() => {
                          const formattedContent =
                            formatMessageContent(message);
                          const contentLength = formattedContent.length;

                          if (contentLength > 500 && !isExpanded) {
                            return (
                              <>
                                {formattedContent.slice(0, 500)}...
                                <button
                                  onClick={() => onToggleExpanded(message._id)}
                                  className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover"
                                >
                                  <ChevronDown className="h-4 w-4" />
                                  Show more
                                </button>
                              </>
                            );
                          } else {
                            return (
                              <>
                                {formattedContent}
                                {contentLength > 500 && (
                                  <button
                                    onClick={() =>
                                      onToggleExpanded(message._id)
                                    }
                                    className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover"
                                  >
                                    <ChevronUp className="h-4 w-4" />
                                    Show less
                                  </button>
                                )}
                                {message.content.startsWith(
                                  '[Tool Result:'
                                ) && (
                                  <button
                                    onClick={() =>
                                      onToggleToolResult(message._id)
                                    }
                                    className="mt-2 ml-4 text-sm text-primary hover:text-primary-hover"
                                  >
                                    Hide
                                  </button>
                                )}
                              </>
                            );
                          }
                        })()}
                      </div>
                    )}

                    {/* Message Actions */}
                    <div className="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() =>
                          onCopy(formatMessageContent(message), message._id)
                        }
                        className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
                      >
                        {copiedId === message._id ? (
                          <>
                            <Check className="h-3 w-3" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            Copy
                          </>
                        )}
                      </button>
                      <button className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1">
                        <Pin className="h-3 w-3" />
                        Pin
                      </button>
                      <button className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1">
                        <Download className="h-3 w-3" />
                        Export
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        } else {
          // Tool pair rendering
          const [toolUseMessage, toolResultMessage] = group.messages;
          const pairId = toolUseMessage._id;
          const isPairExpanded = expandedToolPairs.has(pairId);

          // Get preview of results (first line only for minimal preview)
          const getResultPreview = (content: string) => {
            const lines = content.split('\n');
            const firstLine = lines[0] || '';
            const previewText =
              firstLine.length > 80
                ? firstLine.slice(0, 80) + '...'
                : firstLine;
            const hasMore = lines.length > 1 || firstLine.length > 80;
            return {
              preview: previewText,
              hasMore,
              totalLines: lines.length,
            };
          };

          const resultPreview = getResultPreview(toolResultMessage.content);

          return (
            <div key={pairId} className="group">
              <div className="rounded-xl p-4 bg-layer-secondary border border-secondary-c hover:border-primary-c transition-all relative">
                {/* Version indicator for debugging */}
                <div className="absolute top-1 right-1 text-[8px] text-gray-400 dark:text-gray-600 font-mono">
                  v2.1
                </div>
                {/* Header with expand/collapse button */}
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white shadow-sm">
                      <Wrench className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-primary-c">
                          Tool Operation
                        </span>
                        {toolUseMessage.model && (
                          <span className="text-xs px-2 py-0.5 bg-layer-tertiary rounded-full text-muted-c">
                            {toolUseMessage.model}
                          </span>
                        )}
                      </div>

                      {/* Tool use content preview */}
                      <div className="text-sm text-secondary-c font-medium">
                        {(() => {
                          try {
                            const parsed = JSON.parse(toolUseMessage.content);
                            return `🔧 ${parsed.name || 'Tool call'}`;
                          } catch {
                            return '🔧 Tool call';
                          }
                        })()}
                      </div>

                      {/* Result preview - Collapsed state */}
                      {!isPairExpanded && (
                        <div className="mt-2 p-3 bg-amber-50 dark:bg-amber-950/20 rounded-lg border-2 border-dashed border-amber-300 dark:border-amber-700">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Terminal className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                              <span className="text-sm font-bold text-amber-700 dark:text-amber-300">
                                Tool Result (COLLAPSED)
                              </span>
                            </div>
                            <span className="text-xs text-amber-600 dark:text-amber-400 font-mono">
                              {resultPreview.totalLines} lines hidden
                            </span>
                          </div>
                          <div className="mt-1 text-xs text-amber-600 dark:text-amber-400 italic">
                            Click "Expand" to view the full tool operation and
                            result
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => onToggleToolPairExpanded(pairId)}
                    className={
                      isPairExpanded
                        ? 'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-all duration-200'
                        : 'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 rounded-lg transition-all duration-200 shadow-md animate-pulse'
                    }
                  >
                    {isPairExpanded ? (
                      <>
                        <ChevronUp className="h-3.5 w-3.5" /> Collapse
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3.5 w-3.5" /> EXPAND TO VIEW
                      </>
                    )}
                  </button>
                </div>

                {/* Expanded content */}
                {isPairExpanded && (
                  <div className="mt-4 space-y-3 border-t border-secondary-c pt-4">
                    {/* Tool use full content */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Wrench className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium text-primary-c">
                          Tool Call Details
                        </span>
                      </div>
                      <div className="text-secondary-c whitespace-pre-wrap break-words bg-layer-primary p-3 rounded-lg border border-secondary-c">
                        {toolUseMessage.content}
                      </div>
                    </div>

                    {/* Tool result full content */}
                    <div className="mt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Terminal className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium text-primary-c">
                          Full Result
                        </span>
                      </div>
                      <div className="text-secondary-c whitespace-pre-wrap break-words bg-layer-primary p-3 rounded-lg border border-secondary-c">
                        {toolResultMessage.content}
                      </div>
                    </div>
                  </div>
                )}

                {/* Metadata footer */}
                <div className="flex items-center gap-4 mt-3 text-xs text-dim-c">
                  <time dateTime={toolUseMessage.timestamp}>
                    {format(
                      new Date(toolUseMessage.timestamp),
                      'MMM d, HH:mm:ss'
                    )}
                  </time>
                  {(getMessageCost(toolUseMessage) ||
                    (costMap &&
                      costMap.get(getMessageUuid(toolUseMessage) || '')) ||
                    getMessageCost(toolResultMessage) ||
                    (costMap &&
                      costMap.get(
                        getMessageUuid(toolResultMessage) || ''
                      ))) && (
                    <span className="text-green-600 dark:text-green-400 font-medium">
                      $
                      {(
                        (getMessageCost(toolUseMessage) ||
                          costMap?.get(getMessageUuid(toolUseMessage) || '') ||
                          0) +
                        (getMessageCost(toolResultMessage) ||
                          costMap?.get(
                            getMessageUuid(toolResultMessage) || ''
                          ) ||
                          0)
                      ).toFixed(4)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        }
      })}
    </div>
  );
}

// Compact View Component
interface CompactViewProps {
  messages: Message[];
  getMessageLabel: (type: Message['type'], content?: string) => string;
  getMessageColors: (type: Message['type']) => { avatar: string; bg: string };
}

function CompactView({
  messages,
  getMessageLabel,
  getMessageColors,
}: CompactViewProps) {
  return (
    <div className="space-y-2 max-w-4xl mx-auto">
      {messages.map((message: Message) => {
        const colors = getMessageColors(message.type);
        const label = getMessageLabel(message.type, message.content);
        const isUser = message.type === 'user';

        return (
          <div
            key={message._id}
            className={cn(
              'bg-layer-secondary border border-secondary-c rounded-lg p-3 hover:border-primary-c transition-all',
              colors.bg
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className={cn(
                  'text-sm font-medium',
                  isUser ? 'text-secondary' : 'text-primary'
                )}
              >
                {label}
              </span>
              <span className="text-xs text-dim-c">
                {format(new Date(message.timestamp), 'MMM d, HH:mm:ss')}
              </span>
            </div>
            <div className="text-sm text-tertiary-c line-clamp-2">
              {message.content}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Raw View Component
interface RawViewProps {
  messages: Message[];
  onCopy: (text: string, messageId: string) => void;
  copiedId: string | null;
}

function RawView({ messages, onCopy, copiedId }: RawViewProps) {
  const [scrollRef, setScrollRef] = useState<HTMLDivElement | null>(null);

  const rawContent = messages
    .map((msg: Message) => {
      const model = msg.model ? ` (${msg.model})` : '';
      return `[${format(
        new Date(msg.timestamp),
        'yyyy-MM-dd HH:mm:ss'
      )}] ${msg.type}${model}: ${msg.content}`;
    })
    .join('\n\n');

  const scrollToEnd = () => {
    if (scrollRef) {
      scrollRef.scrollTop = scrollRef.scrollHeight;
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 overflow-hidden">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-medium text-primary-c">
          Raw Conversation Data
        </h4>
        <div className="flex gap-2">
          <button
            onClick={scrollToEnd}
            className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
          >
            <ChevronDown className="h-3 w-3" />
            Jump to End
          </button>
          <button
            onClick={() => onCopy(rawContent, 'raw-content')}
            className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
          >
            {copiedId === 'raw-content' ? (
              <>
                <Check className="h-3 w-3" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                Copy All
              </>
            )}
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden bg-layer-tertiary border border-secondary-c rounded-lg relative">
        <div
          ref={setScrollRef}
          className="h-full overflow-auto scrollbar-thin scroll-smooth"
        >
          <pre className="p-6 text-secondary-c font-mono text-sm whitespace-pre-wrap break-words min-w-0">
            {rawContent}
          </pre>
        </div>
      </div>
    </div>
  );
}
