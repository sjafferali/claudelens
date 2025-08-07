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
  Terminal,
  CheckCircle,
  XCircle,
  FileEdit,
  FolderOpen,
  List,
} from 'lucide-react';
import { Message } from '@/api/types';
import { format, formatDistanceToNow } from 'date-fns';
import { cn } from '@/utils/cn';

interface SidechainPanelProps {
  messages: Message[];
  isOpen: boolean;
  onClose: () => void;
  onNavigateToParent?: (parent_uuid: string) => void;
  className?: string;
}

interface ToolOperation {
  toolUse: Message;
  toolResult?: Message;
}

interface OperationGroup {
  parentMessage: Message;
  operations: ToolOperation[];
}

export function SidechainPanel({
  messages,
  isOpen,
  onClose,
  onNavigateToParent,
  className,
}: SidechainPanelProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [expandedOperations, setExpandedOperations] = useState<Set<string>>(
    new Set()
  );

  // Parse tool information from message content
  const parseToolInfo = (
    message: Message
  ): {
    name: string;
    input: Record<string, unknown>;
    icon: React.ReactNode;
    color: string;
    category: string;
  } => {
    try {
      const parsed = JSON.parse(message.content);
      const name = parsed.name || 'Unknown Tool';
      const input = parsed.input || {};

      // Determine icon, color, and category based on tool name
      let icon = <Wrench className="h-4 w-4" />;
      let color = 'text-gray-500';
      let category = 'Tool';

      if (name.includes('Read') || name.includes('NotebookRead')) {
        icon = <FileText className="h-4 w-4" />;
        color = 'text-blue-500';
        category = 'File Read';
      } else if (
        name.includes('Write') ||
        name.includes('Edit') ||
        name.includes('NotebookEdit')
      ) {
        icon = <FileEdit className="h-4 w-4" />;
        color = 'text-green-500';
        category = 'File Edit';
      } else if (name.includes('LS') || name.includes('Glob')) {
        icon = <FolderOpen className="h-4 w-4" />;
        color = 'text-yellow-500';
        category = 'File Browse';
      } else if (name.includes('Grep')) {
        icon = <Search className="h-4 w-4" />;
        color = 'text-purple-500';
        category = 'Search';
      } else if (name.includes('Web') || name.includes('WebSearch')) {
        icon = <Globe className="h-4 w-4" />;
        color = 'text-indigo-500';
        category = 'Web';
      } else if (name.includes('Bash') || name.includes('Shell')) {
        icon = <Terminal className="h-4 w-4" />;
        color = 'text-orange-500';
        category = 'Terminal';
      } else if (name.includes('Task') || name.includes('Todo')) {
        icon = <List className="h-4 w-4" />;
        color = 'text-pink-500';
        category = 'Task Management';
      }

      return { name, input, icon, color, category };
    } catch {
      return {
        name: 'Unknown Tool',
        input: {},
        icon: <Wrench className="h-4 w-4" />,
        color: 'text-gray-500',
        category: 'Tool',
      };
    }
  };

  // Format tool input for display
  const formatToolInput = (
    name: string,
    input: Record<string, unknown>
  ): string => {
    if (!input) return '';

    // Format based on tool type
    if (name.includes('Read')) {
      return (
        (input.file_path as string) || (input.notebook_path as string) || ''
      );
    } else if (name.includes('Write') || name.includes('Edit')) {
      const path =
        (input.file_path as string) || (input.notebook_path as string) || '';
      const preview =
        (input.content as string) || (input.new_string as string) || '';
      return path + (preview ? ` (${preview.substring(0, 50)}...)` : '');
    } else if (name.includes('LS')) {
      return (input.path as string) || '';
    } else if (name.includes('Glob')) {
      return (input.pattern as string) || '';
    } else if (name.includes('Grep')) {
      return input.pattern ? `"${input.pattern as string}"` : '';
    } else if (name.includes('Bash')) {
      const cmd = (input.command as string) || '';
      return cmd.length > 60 ? cmd.substring(0, 60) + '...' : cmd;
    } else if (name.includes('WebSearch')) {
      return (input.query as string) || '';
    } else if (name.includes('WebFetch')) {
      return (input.url as string) || '';
    } else if (name.includes('TodoWrite')) {
      const todos = (input.todos as unknown[]) || [];
      return `${todos.length} items`;
    } else if (name.includes('Task')) {
      return (input.description as string) || '';
    }

    // Default: show first meaningful value
    const values = Object.values(input);
    if (values.length > 0) {
      const firstValue = values[0];
      if (typeof firstValue === 'string') {
        return firstValue.length > 60
          ? firstValue.substring(0, 60) + '...'
          : firstValue;
      }
    }
    return '';
  };

  // Parse tool result
  const parseToolResult = (
    message: Message
  ): {
    success: boolean;
    preview: string;
    hasError: boolean;
  } => {
    const content = message.content || '';
    const hasError =
      content.toLowerCase().includes('error') ||
      content.toLowerCase().includes('failed') ||
      content.toLowerCase().includes('exception');

    // Truncate long results
    let preview = content;
    if (preview.length > 200) {
      preview = preview.substring(0, 200) + '...';
    }

    return {
      success: !hasError,
      preview,
      hasError,
    };
  };

  // Group operations by their parent assistant message
  const operationGroups = useMemo(() => {
    const groups: OperationGroup[] = [];
    const toolUseMap = new Map<string, Message>();
    const processedToolUses = new Set<string>();

    // First, create a map of tool_use messages by their UUID
    messages.forEach((message) => {
      if (message.type === 'tool_use') {
        toolUseMap.set(message.uuid || message._id, message);
      }
    });

    // Find assistant messages that have tool operations
    messages.forEach((message) => {
      if (message.type === 'assistant') {
        const operations: ToolOperation[] = [];

        // Find all tool_use messages that are children of this assistant message
        messages.forEach((toolMsg) => {
          if (
            toolMsg.type === 'tool_use' &&
            toolMsg.parent_uuid === (message.uuid || message._id) &&
            !processedToolUses.has(toolMsg._id)
          ) {
            processedToolUses.add(toolMsg._id);

            // Find corresponding tool_result
            const toolResult = messages.find(
              (resultMsg) =>
                resultMsg.type === 'tool_result' &&
                resultMsg.parent_uuid === (toolMsg.uuid || toolMsg._id)
            );

            operations.push({
              toolUse: toolMsg,
              toolResult,
            });
          }
        });

        if (operations.length > 0) {
          groups.push({
            parentMessage: message,
            operations,
          });
        }
      }
    });

    // Sort groups by parent message timestamp
    groups.sort(
      (a, b) =>
        new Date(a.parentMessage.timestamp).getTime() -
        new Date(b.parentMessage.timestamp).getTime()
    );

    return groups;
  }, [messages]);

  const toggleGroup = (groupId: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(groupId)) {
        newSet.delete(groupId);
      } else {
        newSet.add(groupId);
      }
      return newSet;
    });
  };

  const toggleOperation = (operationId: string) => {
    setExpandedOperations((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(operationId)) {
        newSet.delete(operationId);
      } else {
        newSet.add(operationId);
      }
      return newSet;
    });
  };

  if (!isOpen) return null;

  const totalOperations = operationGroups.reduce(
    (sum, group) => sum + group.operations.length,
    0
  );

  return (
    <div
      className={cn(
        'w-96 bg-layer-secondary border-l border-primary-c flex flex-col h-full',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-secondary-c">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-purple-500" />
            <h3 className="text-sm font-semibold text-primary-c">
              Tool Operations
            </h3>
            {totalOperations > 0 && (
              <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-full">
                {totalOperations}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-layer-tertiary rounded transition-colors"
            aria-label="Close operations panel"
          >
            <X className="h-4 w-4 text-muted-c" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {operationGroups.length === 0 ? (
          <div className="px-4 py-8 text-center text-muted-c text-sm">
            No tool operations in this conversation
          </div>
        ) : (
          <div className="p-3 space-y-3">
            {operationGroups.map((group) => {
              const groupId = group.parentMessage._id;
              const isExpanded = expandedGroups.has(groupId);

              // Get unique categories
              const categories = Array.from(
                new Set(
                  group.operations.map(
                    (op) => parseToolInfo(op.toolUse).category
                  )
                )
              );

              return (
                <div
                  key={groupId}
                  className="bg-layer-tertiary border border-secondary-c rounded-lg overflow-hidden"
                >
                  {/* Group Header */}
                  <div className="flex items-center gap-2 px-3 py-2.5">
                    <button
                      className="flex-1 flex items-center gap-2 hover:bg-layer-primary/50 transition-colors rounded p-1 -m-1"
                      onClick={() => toggleGroup(groupId)}
                    >
                      <div className="text-muted-c">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </div>

                      <div className="flex-1 text-left">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-primary-c">
                            {group.operations.length} operation
                            {group.operations.length !== 1 ? 's' : ''}
                          </span>
                          <span className="text-xs text-muted-c">
                            {formatDistanceToNow(
                              new Date(group.parentMessage.timestamp),
                              { addSuffix: true }
                            )}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 mt-1">
                          {categories.map((cat) => (
                            <span
                              key={cat}
                              className="text-xs px-1.5 py-0.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded"
                            >
                              {cat}
                            </span>
                          ))}
                        </div>
                      </div>
                    </button>

                    {onNavigateToParent && (
                      <button
                        onClick={() =>
                          onNavigateToParent(
                            group.parentMessage.uuid || group.parentMessage._id
                          )
                        }
                        className="text-xs text-primary hover:text-primary-hover px-2 py-1 hover:bg-layer-primary/50 rounded"
                      >
                        Jump to message →
                      </button>
                    )}
                  </div>

                  {/* Expanded Operations */}
                  {isExpanded && (
                    <div className="border-t border-secondary-c">
                      {group.operations.map((operation) => {
                        const toolInfo = parseToolInfo(operation.toolUse);
                        const toolInput = formatToolInput(
                          toolInfo.name,
                          toolInfo.input
                        );
                        const operationId = operation.toolUse._id;
                        const isOperationExpanded =
                          expandedOperations.has(operationId);

                        const result = operation.toolResult
                          ? parseToolResult(operation.toolResult)
                          : null;

                        return (
                          <div
                            key={operationId}
                            className={cn(
                              'border-b border-secondary-c/50 last:border-b-0',
                              'hover:bg-layer-primary/30 transition-colors'
                            )}
                          >
                            <button
                              onClick={() => toggleOperation(operationId)}
                              className="w-full px-3 py-2 text-left"
                            >
                              <div className="flex items-start gap-2">
                                <div className={cn('mt-0.5', toolInfo.color)}>
                                  {toolInfo.icon}
                                </div>

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-primary-c">
                                      {toolInfo.name}
                                    </span>
                                    {result && (
                                      <span
                                        className={cn(
                                          'text-xs',
                                          result.hasError
                                            ? 'text-red-500'
                                            : 'text-green-500'
                                        )}
                                      >
                                        {result.hasError ? (
                                          <XCircle className="h-3 w-3" />
                                        ) : (
                                          <CheckCircle className="h-3 w-3" />
                                        )}
                                      </span>
                                    )}
                                    <span className="text-xs text-dim-c ml-auto">
                                      {format(
                                        new Date(operation.toolUse.timestamp),
                                        'HH:mm:ss'
                                      )}
                                    </span>
                                  </div>

                                  {toolInput && (
                                    <div className="text-xs text-secondary-c mt-0.5 font-mono">
                                      {toolInput}
                                    </div>
                                  )}

                                  {/* Expanded details */}
                                  {isOperationExpanded && result && (
                                    <div className="mt-2 p-2 bg-layer-primary/50 rounded text-xs">
                                      <div className="text-muted-c mb-1">
                                        Result:
                                      </div>
                                      <pre className="whitespace-pre-wrap break-words text-secondary-c">
                                        {result.preview}
                                      </pre>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Summary */}
      {totalOperations > 0 && (
        <div className="px-4 py-3 border-t border-secondary-c bg-layer-primary/50">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-c">
              {operationGroups.length} message
              {operationGroups.length !== 1 ? 's' : ''} with tools
            </span>
            <span className="text-primary-c font-medium">
              {totalOperations} total operation
              {totalOperations !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
