import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Search,
  Copy,
  Pin,
  Download,
  ChevronDown,
  ChevronUp,
  Check,
} from 'lucide-react';
import { format } from 'date-fns';
import { useSession, useSessionMessages } from '@/hooks/useSessions';
import { cn } from '@/utils/cn';
import { Message } from '@/api/types';

export default function SessionDetail() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { data: session, isLoading: sessionLoading } = useSession(sessionId!);
  const { data: messages, isLoading: messagesLoading } = useSessionMessages(
    sessionId!
  );

  const [viewMode, setViewMode] = useState<'timeline' | 'compact' | 'raw'>(
    'timeline'
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [collapsedToolResults, setCollapsedToolResults] = useState<Set<string>>(
    new Set()
  );

  // Filter messages based on search
  const filteredMessages =
    messages?.messages.filter((msg) =>
      msg.content.toLowerCase().includes(searchQuery.toLowerCase())
    ) || [];

  // Auto-collapse tool results on load
  useEffect(() => {
    if (messages) {
      const toolResultIds = messages.messages
        .filter((msg) => msg.content.startsWith('[Tool Result:'))
        .map((msg) => msg._id);
      setCollapsedToolResults(new Set(toolResultIds));
    }
  }, [messages]);

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

  const getMessageLabel = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Claude';
      case 'tool_use':
        return 'Claude';
      case 'tool_result':
        return 'You';
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

  const toolsUsed = messages.messages.filter(
    (msg) => msg.type === 'tool_use'
  ).length;

  const totalTokens = messages.messages.reduce(
    (acc, msg) => acc + (msg.inputTokens || 0) + (msg.outputTokens || 0),
    0
  );

  return (
    <div className="flex flex-col h-screen bg-layer-primary">
      {/* Header */}
      <div className="bg-layer-secondary border-b border-primary-c px-6 py-4">
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
            <h2 className="text-lg font-medium text-primary-c">
              Session {session.sessionId.slice(0, 8)}...
            </h2>
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

      <div className="flex flex-1 overflow-hidden">
        {/* Conversation Panel */}
        <div className="flex-1 flex flex-col bg-layer-primary">
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
          <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin">
            {viewMode === 'timeline' && (
              <TimelineView
                messages={filteredMessages}
                expandedMessages={expandedMessages}
                collapsedToolResults={collapsedToolResults}
                copiedId={copiedId}
                onToggleExpanded={toggleExpanded}
                onToggleToolResult={toggleToolResult}
                onCopy={copyToClipboard}
                getMessageColors={getMessageColors}
                getMessageLabel={getMessageLabel}
                getAvatarText={getAvatarText}
              />
            )}
            {viewMode === 'compact' && (
              <CompactView
                messages={filteredMessages}
                getMessageLabel={getMessageLabel}
                getMessageColors={getMessageColors}
              />
            )}
            {viewMode === 'raw' && (
              <RawView
                messages={filteredMessages}
                onCopy={copyToClipboard}
                copiedId={copiedId}
              />
            )}
          </div>
        </div>

        {/* Details Panel */}
        <div className="w-80 bg-layer-secondary border-l border-primary-c p-6 overflow-y-auto scrollbar-thin">
          <div className="space-y-8">
            {/* Session Details */}
            <div>
              <h3 className="text-base font-medium text-primary-c mb-4">
                Session Details
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-secondary-c">
                  <span className="text-sm text-muted-c">Session ID</span>
                  <span className="text-sm text-secondary-c font-mono">
                    {session.sessionId.slice(0, 12)}...
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-secondary-c">
                  <span className="text-sm text-muted-c">Started</span>
                  <span className="text-sm text-secondary-c font-mono">
                    {format(new Date(session.startedAt), 'M/d/yyyy, h:mm:ss a')}
                  </span>
                </div>
                {session.endedAt && (
                  <div className="flex justify-between py-2 border-b border-secondary-c">
                    <span className="text-sm text-muted-c">Ended</span>
                    <span className="text-sm text-secondary-c font-mono">
                      {format(new Date(session.endedAt), 'M/d/yyyy, h:mm:ss a')}
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
                <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center">
                  <div className="text-2xl font-semibold text-primary">
                    {toolsUsed}
                  </div>
                  <div className="text-xs text-muted-c">Tools Used</div>
                </div>
                <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center">
                  <div className="text-2xl font-semibold text-primary">
                    {Math.floor(totalTokens / 1000)}K
                  </div>
                  <div className="text-xs text-muted-c">Tokens</div>
                </div>
                <div className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center">
                  <div className="text-2xl font-semibold text-primary">
                    ${session.totalCost?.toFixed(2) || '0.00'}
                  </div>
                  <div className="text-xs text-muted-c">Cost</div>
                </div>
              </div>
            </div>

            {/* Tools Used */}
            <div>
              <h3 className="text-base font-medium text-primary-c mb-4">
                Tools Used
              </h3>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  todoWrite × 12
                </span>
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  fileWrite × 4
                </span>
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  codeAnalysis × 2
                </span>
              </div>
            </div>

            {/* Topics */}
            <div>
              <h3 className="text-base font-medium text-primary-c mb-4">
                Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  Web Development
                </span>
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  Claude API
                </span>
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  Data Visualization
                </span>
                <span className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-full text-xs text-tertiary-c">
                  React
                </span>
              </div>
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
  copiedId: string | null;
  onToggleExpanded: (messageId: string) => void;
  onToggleToolResult: (messageId: string) => void;
  onCopy: (text: string, messageId: string) => void;
  getMessageColors: (type: Message['type']) => { avatar: string; bg: string };
  getMessageLabel: (type: Message['type']) => string;
  getAvatarText: (type: Message['type']) => string;
}

function TimelineView({
  messages,
  expandedMessages,
  collapsedToolResults,
  copiedId,
  onToggleExpanded,
  onToggleToolResult,
  onCopy,
  getMessageColors,
  getMessageLabel,
  getAvatarText,
}: TimelineViewProps) {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {messages.map((message: Message) => {
        const isExpanded = expandedMessages.has(message._id);
        const isToolResultCollapsed = collapsedToolResults.has(message._id);
        const colors = getMessageColors(message.type);

        return (
          <div key={message._id} className="group">
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
                        {getMessageLabel(message.type)}
                      </span>
                      {message.model && (
                        <span className="text-xs px-2 py-0.5 bg-layer-tertiary rounded-full text-muted-c">
                          {message.model}
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-dim-c">
                      {format(new Date(message.timestamp), 'MMM d, HH:mm:ss')}
                    </span>
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
                      {message.content.length > 500 && !isExpanded ? (
                        <>
                          {message.content.slice(0, 500)}...
                          <button
                            onClick={() => onToggleExpanded(message._id)}
                            className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover"
                          >
                            <ChevronDown className="h-4 w-4" />
                            Show more
                          </button>
                        </>
                      ) : (
                        <>
                          {message.content}
                          {message.content.length > 500 && (
                            <button
                              onClick={() => onToggleExpanded(message._id)}
                              className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover"
                            >
                              <ChevronUp className="h-4 w-4" />
                              Show less
                            </button>
                          )}
                          {message.content.startsWith('[Tool Result:') && (
                            <button
                              onClick={() => onToggleToolResult(message._id)}
                              className="mt-2 ml-4 text-sm text-primary hover:text-primary-hover"
                            >
                              Hide
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  )}

                  {/* Message Actions */}
                  <div className="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onCopy(message.content, message._id)}
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
      })}
    </div>
  );
}

// Compact View Component
interface CompactViewProps {
  messages: Message[];
  getMessageLabel: (type: Message['type']) => string;
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
        const label = getMessageLabel(message.type);
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
  const rawContent = messages
    .map((msg: Message) => {
      const model = msg.model ? ` (${msg.model})` : '';
      return `[${format(
        new Date(msg.timestamp),
        'yyyy-MM-dd HH:mm:ss'
      )}] ${msg.type}${model}: ${msg.content}`;
    })
    .join('\n\n');

  return (
    <div className="relative">
      <button
        onClick={() => onCopy(rawContent, 'raw-content')}
        className="absolute top-2 right-2 px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
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
      <pre className="bg-layer-tertiary border border-secondary-c rounded-lg p-6 text-secondary-c font-mono text-sm whitespace-pre-wrap">
        {rawContent}
      </pre>
    </div>
  );
}
