import React, { useMemo, useState } from 'react';
import {
  ChevronRight,
  ChevronDown,
  X,
  GitBranch,
  Wrench,
  FileText,
  Search,
  Globe,
} from 'lucide-react';
import { Message } from '@/api/types';
import { format } from 'date-fns';
import { cn } from '@/utils/cn';

interface SidechainPanelProps {
  messages: Message[];
  isOpen: boolean;
  onClose: () => void;
  onNavigateToParent?: (parent_uuid: string) => void;
  className?: string;
}

export function SidechainPanel({
  messages,
  isOpen,
  onClose,
  onNavigateToParent,
  className,
}: SidechainPanelProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );

  // Filter and group sidechain messages by parent
  const sidechainGroups = useMemo(() => {
    const groups = new Map<string, Message[]>();

    // Debug logging
    console.log('[SidechainPanel] Total messages:', messages.length);
    const sidechainMessages = messages.filter((m) => m.isSidechain);
    console.log(
      '[SidechainPanel] Sidechain messages found:',
      sidechainMessages.length
    );

    // Also check for tool_use and tool_result messages even if not marked as sidechain
    const toolMessages = messages.filter(
      (m) => m.type === 'tool_use' || m.type === 'tool_result'
    );
    console.log(
      '[SidechainPanel] Tool messages (tool_use/tool_result):',
      toolMessages.length
    );

    // Log a sample of messages to see their structure
    if (messages.length > 0) {
      console.log('[SidechainPanel] Sample message:', messages[0]);
      const toolMsg = toolMessages[0];
      if (toolMsg) {
        console.log('[SidechainPanel] Sample tool message:', toolMsg);
        console.log(
          '[SidechainPanel] Tool message parent_uuid:',
          toolMsg.parent_uuid
        );
        console.log('[SidechainPanel] Tool message uuid:', toolMsg.uuid);

        // Check if any tool messages have parent_uuid
        const toolMessagesWithParent = toolMessages.filter(
          (m) => m.parent_uuid
        );
        console.log(
          '[SidechainPanel] Tool messages with parent_uuid:',
          toolMessagesWithParent.length
        );
      }
    }

    messages.forEach((message) => {
      // Include messages marked as sidechain OR tool_use/tool_result types
      const isSidechainMessage =
        message.isSidechain ||
        message.type === 'tool_use' ||
        message.type === 'tool_result';

      if (isSidechainMessage && message.parent_uuid) {
        const existing = groups.get(message.parent_uuid) || [];
        groups.set(message.parent_uuid, [...existing, message]);
      }
    });

    console.log('[SidechainPanel] Groups created:', groups.size);
    groups.forEach((msgs, parentId) => {
      console.log(
        `[SidechainPanel] Group for parent ${parentId}:`,
        msgs.length,
        'messages'
      );
    });

    // Sort messages within each group by timestamp
    groups.forEach((msgs) => {
      msgs.sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
    });

    return groups;
  }, [messages]);

  // Get parent message details for each group
  const getParentMessage = (parent_uuid: string): Message | undefined => {
    return messages.find((m) => (m.uuid || m.messageUuid) === parent_uuid);
  };

  // Categorize sidechain type based on content
  const getSidechainType = (
    message: Message
  ): { icon: React.ReactNode; label: string; color: string } => {
    const content = message.content.toLowerCase();

    if (message.type === 'tool_use') {
      try {
        const parsed = JSON.parse(message.content);
        const toolName = parsed.name || '';

        if (
          toolName.includes('Read') ||
          toolName.includes('Glob') ||
          toolName.includes('LS')
        ) {
          return {
            icon: <FileText className="h-3.5 w-3.5" />,
            label: 'File Operation',
            color: 'text-blue-500',
          };
        }
        if (toolName.includes('Grep') || toolName.includes('Search')) {
          return {
            icon: <Search className="h-3.5 w-3.5" />,
            label: 'Search',
            color: 'text-green-500',
          };
        }
        if (toolName.includes('Web')) {
          return {
            icon: <Globe className="h-3.5 w-3.5" />,
            label: 'Web',
            color: 'text-purple-500',
          };
        }
      } catch {
        // Fall through to default
      }
    }

    if (content.includes('error') || content.includes('failed')) {
      return {
        icon: <X className="h-3.5 w-3.5" />,
        label: 'Error',
        color: 'text-red-500',
      };
    }

    return {
      icon: <Wrench className="h-3.5 w-3.5" />,
      label: 'Tool',
      color: 'text-purple-500',
    };
  };

  const toggleGroup = (parent_uuid: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(parent_uuid)) {
        newSet.delete(parent_uuid);
      } else {
        newSet.add(parent_uuid);
      }
      return newSet;
    });
  };

  const toggleMessage = (messageId: string) => {
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

  // Format message content for preview
  const getMessagePreview = (message: Message): string => {
    const maxLength = 100;
    let content = message.content;

    // Try to parse tool_use messages
    if (message.type === 'tool_use') {
      try {
        const parsed = JSON.parse(content);
        content = `${parsed.name}: ${JSON.stringify(parsed.input || {}).substring(0, maxLength)}`;
      } catch {
        // Use raw content
      }
    }

    if (content.length > maxLength) {
      return content.substring(0, maxLength) + '...';
    }
    return content;
  };

  if (!isOpen) return null;

  return (
    <div
      className={cn(
        'w-80 bg-layer-secondary border-l border-primary-c flex flex-col h-full',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-secondary-c flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-purple-500" />
          <h3 className="text-sm font-semibold text-primary-c">
            Sidechains & Operations
          </h3>
          <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-full">
            {sidechainGroups.size} group{sidechainGroups.size !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-layer-tertiary rounded transition-colors"
          aria-label="Close sidechain panel"
        >
          <X className="h-4 w-4 text-muted-c" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {sidechainGroups.size === 0 ? (
          <div className="px-4 py-8 text-center text-muted-c text-sm">
            No sidechain operations in this conversation
          </div>
        ) : (
          <div className="p-3 space-y-3">
            {Array.from(sidechainGroups.entries()).map(
              ([parent_uuid, sidechainMessages]) => {
                const parentMessage = getParentMessage(parent_uuid);
                const isExpanded = expandedGroups.has(parent_uuid);
                const totalCount = sidechainMessages.length;

                return (
                  <div
                    key={parent_uuid}
                    className="bg-layer-tertiary border border-purple-500/20 rounded-lg overflow-hidden"
                  >
                    {/* Group Header */}
                    <button
                      onClick={() => toggleGroup(parent_uuid)}
                      className="w-full px-3 py-2 flex items-center justify-between hover:bg-purple-500/5 transition-colors"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <div className="text-purple-500">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </div>
                        <div className="flex-1 text-left min-w-0">
                          <div className="text-xs text-muted-c truncate">
                            Parent:{' '}
                            {parentMessage
                              ? parentMessage.content.substring(0, 50) + '...'
                              : 'Unknown'}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                              {totalCount} operation
                              {totalCount !== 1 ? 's' : ''}
                            </span>
                            {onNavigateToParent && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onNavigateToParent(parent_uuid);
                                }}
                                className="text-xs text-primary hover:text-primary-hover"
                              >
                                Jump to parent →
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {/* Show operation type badges */}
                        {Array.from(
                          new Set(
                            sidechainMessages.map(
                              (m) => getSidechainType(m).label
                            )
                          )
                        ).map((label) => (
                          <span
                            key={label}
                            className="text-xs px-1.5 py-0.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded"
                          >
                            {label}
                          </span>
                        ))}
                      </div>
                    </button>

                    {/* Expanded Content */}
                    {isExpanded && (
                      <div className="border-t border-purple-500/20">
                        {sidechainMessages.map((message, index) => {
                          const messageExpanded = expandedMessages.has(
                            message._id
                          );
                          const { icon, label, color } =
                            getSidechainType(message);

                          return (
                            <div
                              key={message._id}
                              className={cn(
                                'border-b border-purple-500/10 last:border-b-0',
                                'hover:bg-purple-500/5 transition-colors'
                              )}
                            >
                              <button
                                onClick={() => toggleMessage(message._id)}
                                className="w-full px-3 py-2 text-left"
                              >
                                <div className="flex items-start gap-2">
                                  <div className={cn('mt-0.5', color)}>
                                    {icon}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="text-xs font-medium text-primary-c">
                                        {label}
                                      </span>
                                      <span className="text-xs text-dim-c">
                                        {format(
                                          new Date(message.timestamp),
                                          'HH:mm:ss'
                                        )}
                                      </span>
                                    </div>
                                    <div className="text-xs text-secondary-c">
                                      {messageExpanded ? (
                                        <pre className="whitespace-pre-wrap break-words font-mono">
                                          {message.content}
                                        </pre>
                                      ) : (
                                        <span className="line-clamp-2">
                                          {getMessagePreview(message)}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </button>

                              {/* Connecting line to next message */}
                              {index < sidechainMessages.length - 1 && (
                                <div className="ml-6 border-l-2 border-purple-500/20 h-2" />
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              }
            )}
          </div>
        )}
      </div>

      {/* Footer with stats */}
      {sidechainGroups.size > 0 && (
        <div className="px-4 py-3 border-t border-secondary-c bg-purple-500/5">
          <div className="text-xs text-muted-c">
            Total:{' '}
            {Array.from(sidechainGroups.values()).reduce(
              (sum, msgs) => sum + msgs.length,
              0
            )}{' '}
            sidechain operations
          </div>
        </div>
      )}
    </div>
  );
}
