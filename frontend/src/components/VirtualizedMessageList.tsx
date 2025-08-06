import { useRef, useEffect, useMemo, useCallback, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';
import {
  User,
  Bot,
  Copy,
  ChevronDown,
  ChevronUp,
  Check,
  Wrench,
  Share2,
  Bug,
} from 'lucide-react';
import { format } from 'date-fns';
import { copyToClipboard } from '@/utils/clipboard';
import { ToolDisplay } from '@/components/ToolDisplay';
import { ToolResultDisplay } from '@/components/ToolResultDisplay';
import {
  calculateBranchCounts,
  getBranchAlternatives,
} from '@/utils/branch-detection';
import { BranchSelector } from '@/components/BranchSelector';
import {
  copyMessageLink,
  getMessageLinkDescription,
} from '@/utils/message-linking';
import toast from 'react-hot-toast';

interface VirtualizedMessageListProps {
  messages: Message[];
  costMap: Map<string, number>;
  activeBranches: Map<string, string>;
  onSelectBranch: (parentId: string, branchId: string) => void;
  onDebugClick?: (message: Message) => void;
  messageRefs?: React.MutableRefObject<{
    [key: string]: HTMLDivElement | null;
  }>;
  sessionId: string;
  targetMessageId?: string | null;
}

export function VirtualizedMessageList({
  messages,
  costMap,
  activeBranches,
  onSelectBranch,
  onDebugClick,
  messageRefs,
  sessionId,
  targetMessageId,
}: VirtualizedMessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  // Calculate filtered messages and branch counts
  const { filteredMessages } = useMemo(() => {
    const withBranches = calculateBranchCounts(messages);

    // Create a Map for branch counts lookup
    const branchCountMap = new Map<string, number>();
    withBranches.forEach((msg) => {
      if (msg.parent_uuid && msg.branchCount) {
        branchCountMap.set(msg.parent_uuid, msg.branchCount);
      }
    });

    // Filter messages based on active branches
    const filtered = withBranches.filter((msg) => {
      // Always show messages without parent (root messages)
      if (!msg.parent_uuid) return true;

      // Check if this message's parent has branches
      const parentBranchCount = branchCountMap.get(msg.parent_uuid) || 0;
      if (parentBranchCount <= 1) return true;

      // If parent has multiple branches, only show the active one
      const activeBranchId = activeBranches.get(msg.parent_uuid);
      return !activeBranchId || msg.uuid === activeBranchId;
    });

    return { filteredMessages: filtered };
  }, [messages, activeBranches]);

  // Estimate item size based on message type and content
  const estimateSize = useCallback(
    (index: number) => {
      const message = filteredMessages[index];
      if (!message) return 150; // Default height

      // Base height
      let height = 100;

      // Add height based on content length
      const contentLength = message.content?.length || 0;
      height += Math.floor(contentLength / 100) * 20;

      // Add height for tool messages
      if (message.type === 'tool_use' || message.type === 'tool_result') {
        height += 50;
      }

      // Add height for branches
      const branchCount = message.branchCount || 0;
      if (branchCount > 1) {
        height += 40;
      }

      return Math.min(height, 500); // Cap at max height
    },
    [filteredMessages]
  );

  // Setup virtualizer
  const virtualizer = useVirtualizer({
    count: filteredMessages.length,
    getScrollElement: () => containerRef.current,
    estimateSize,
    overscan: 5,
    getItemKey: (index) =>
      filteredMessages[index]?.uuid ||
      filteredMessages[index]?._id ||
      `msg-${index}`,
  });

  // Scroll to target message when it changes
  useEffect(() => {
    if (targetMessageId && containerRef.current) {
      const targetIndex = filteredMessages.findIndex(
        (msg) => msg.uuid === targetMessageId || msg._id === targetMessageId
      );

      if (targetIndex !== -1) {
        virtualizer.scrollToIndex(targetIndex, {
          align: 'center',
          behavior: 'smooth',
        });
      }
    }
  }, [targetMessageId, filteredMessages, virtualizer]);

  // Toggle tool expansion
  const toggleToolExpansion = useCallback((messageId: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(messageId)) {
        next.delete(messageId);
      } else {
        next.add(messageId);
      }
      return next;
    });
  }, []);

  // Copy message content
  const handleCopyContent = useCallback(async (message: Message) => {
    const success = await copyToClipboard(message.content || '');
    if (success) {
      setCopiedMessageId(message.uuid || message._id);
      setTimeout(() => setCopiedMessageId(null), 2000);
    }
  }, []);

  // Share message link
  const handleShareMessage = useCallback(
    (message: Message) => {
      const description = getMessageLinkDescription(message);
      copyMessageLink(message, sessionId);
      toast.success(`Copied link to ${description}`);
    },
    [sessionId]
  );

  // Render a single message
  const renderMessage = useCallback(
    (message: Message, index: number) => {
      const messageId = message.uuid || message._id;
      const cost = costMap.get(messageId) || 0;
      const isExpanded = expandedTools.has(messageId);
      const isCopied = copiedMessageId === messageId;
      const branchCount = message.branchCount || 0;
      const alternatives =
        branchCount > 1
          ? getBranchAlternatives(messages, message.uuid || message._id)
          : [];

      // Group tool messages
      if (message.type === 'tool_use' || message.type === 'tool_result') {
        return null; // These are rendered as part of assistant messages
      }

      // Find associated tool messages
      const toolMessages = messages.filter(
        (m) =>
          m.parent_uuid === message.uuid &&
          (m.type === 'tool_use' || m.type === 'tool_result')
      );

      return (
        <div
          key={messageId}
          ref={(el) => {
            if (messageRefs?.current) {
              messageRefs.current[messageId] = el;
            }
          }}
          id={`message-${messageId}`}
          className={cn(
            'group relative',
            message.type === 'assistant'
              ? 'bg-layer-secondary'
              : 'bg-layer-primary',
            targetMessageId === messageId &&
              'ring-2 ring-blue-500 ring-offset-2'
          )}
        >
          <div className="px-6 py-4">
            {/* Branch selector if needed */}
            {branchCount > 1 && (
              <div className="mb-3">
                <BranchSelector
                  currentMessage={message}
                  branchMessages={alternatives}
                  onSelectBranch={(messageUuid) => {
                    if (message.parent_uuid) {
                      onSelectBranch(message.parent_uuid, messageUuid);
                    }
                  }}
                />
              </div>
            )}

            {/* Message header */}
            <div className="flex items-start gap-3">
              <div
                className={cn(
                  'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
                  message.type === 'user' ? 'bg-blue-500' : 'bg-emerald-500'
                )}
              >
                {message.type === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-primary-c">
                    {message.type === 'user' ? 'You' : 'Claude'}
                  </span>
                  <span className="text-xs text-muted-c">
                    {format(new Date(message.created_at || 0), 'h:mm a')}
                  </span>
                  {cost > 0 && (
                    <span className="text-xs text-muted-c">
                      ${cost.toFixed(4)}
                    </span>
                  )}
                  <span className="text-xs text-muted-c font-mono">
                    #{index + 1} of {filteredMessages.length}
                  </span>
                </div>

                {/* Message content */}
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                </div>

                {/* Tool messages */}
                {toolMessages.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <button
                      onClick={() => toggleToolExpansion(messageId)}
                      className="flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300"
                    >
                      <Wrench className="w-4 h-4" />
                      <span>{toolMessages.length} tool operations</span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>

                    {isExpanded && (
                      <div className="pl-6 space-y-2 border-l-2 border-purple-500/20">
                        {toolMessages.map((toolMsg) => {
                          if (toolMsg.type === 'tool_use') {
                            // Parse tool info from content
                            let toolName = 'Unknown Tool';
                            let toolInput = {};
                            try {
                              const parsed = JSON.parse(toolMsg.content);
                              toolName = parsed.name || 'Unknown Tool';
                              toolInput = parsed.input || {};
                            } catch (e) {
                              // Fallback for unparseable content
                            }
                            return (
                              <div
                                key={toolMsg.uuid || toolMsg._id}
                                className="text-sm"
                              >
                                <ToolDisplay
                                  toolName={toolName}
                                  toolInput={toolInput}
                                  isCollapsed={!isExpanded}
                                />
                              </div>
                            );
                          } else {
                            // tool_result
                            return (
                              <div
                                key={toolMsg.uuid || toolMsg._id}
                                className="text-sm"
                              >
                                <ToolResultDisplay
                                  content={toolMsg.content}
                                  isCollapsed={!isExpanded}
                                />
                              </div>
                            );
                          }
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleCopyContent(message)}
                    className="p-1 hover:bg-layer-tertiary rounded"
                    title="Copy message"
                  >
                    {isCopied ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4 text-muted-c" />
                    )}
                  </button>
                  <button
                    onClick={() => handleShareMessage(message)}
                    className="p-1 hover:bg-layer-tertiary rounded"
                    title="Share link to message"
                  >
                    <Share2 className="w-4 h-4 text-muted-c" />
                  </button>
                  {onDebugClick && (
                    <button
                      onClick={() => onDebugClick(message)}
                      className="p-1 hover:bg-layer-tertiary rounded"
                      title="View message data"
                    >
                      <Bug className="w-4 h-4 text-muted-c" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    },
    [
      costMap,
      expandedTools,
      copiedMessageId,
      messages,
      filteredMessages,
      messageRefs,
      targetMessageId,
      onSelectBranch,
      toggleToolExpansion,
      handleCopyContent,
      handleShareMessage,
      onDebugClick,
    ]
  );

  return (
    <div
      ref={containerRef}
      className="h-full overflow-auto"
      style={{ contain: 'strict' }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderMessage(
              filteredMessages[virtualItem.index],
              virtualItem.index
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
