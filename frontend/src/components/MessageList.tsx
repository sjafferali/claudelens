import { Message } from '@/api/types';
import { format } from 'date-fns';
import {
  User,
  Bot,
  Terminal,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Wrench,
  Copy,
  Check,
  Clock,
  Coins,
  Hash,
  Zap,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { getMessageUuid, getMessageCost } from '@/types/message-extensions';

interface MessageListProps {
  messages: Message[];
  costMap?: Map<string, number>;
}

export default function MessageList({ messages, costMap }: MessageListProps) {
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );
  const [expandedToolPairs, setExpandedToolPairs] = useState<Set<string>>(
    new Set()
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);

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

  const getMessageIcon = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return <User className="h-5 w-5" />;
      case 'assistant':
        return <Bot className="h-5 w-5" />;
      case 'system':
        return <Terminal className="h-5 w-5" />;
      case 'tool_use':
        return <Wrench className="h-5 w-5" />;
      case 'tool_result':
        return <Terminal className="h-5 w-5" />;
      default:
        return <MessageSquare className="h-5 w-5" />;
    }
  };

  const getMessageLabel = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Claude';
      case 'system':
        return 'System';
      case 'tool_use':
        return 'Tool Use';
      case 'tool_result':
        return 'Tool Result';
      default:
        return type;
    }
  };

  const getMessageColors = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return {
          avatar:
            'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md',
          background: 'bg-white dark:bg-slate-900 border-l-4 border-l-blue-500',
          label: 'text-blue-700 dark:text-blue-300 font-semibold',
          hover: 'hover:bg-blue-50/50 dark:hover:bg-blue-950/20',
        };
      case 'assistant':
        return {
          avatar:
            'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white shadow-md',
          background:
            'bg-emerald-50/50 dark:bg-emerald-950/20 border-l-4 border-l-emerald-500',
          label: 'text-emerald-700 dark:text-emerald-300 font-semibold',
          hover: 'hover:bg-emerald-100/50 dark:hover:bg-emerald-950/30',
        };
      case 'system':
        return {
          avatar:
            'bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-md',
          background:
            'bg-amber-50/50 dark:bg-amber-950/20 border-l-4 border-l-amber-500',
          label: 'text-amber-700 dark:text-amber-300 font-semibold',
          hover: 'hover:bg-amber-100/50 dark:hover:bg-amber-950/30',
        };
      case 'tool_use':
        return {
          avatar:
            'bg-gradient-to-br from-purple-500 to-violet-600 text-white shadow-md',
          background:
            'bg-purple-50/50 dark:bg-purple-950/20 border-l-4 border-l-purple-500',
          label: 'text-purple-700 dark:text-purple-300 font-semibold',
          hover: 'hover:bg-purple-100/50 dark:hover:bg-purple-950/30',
        };
      case 'tool_result':
        return {
          avatar:
            'bg-gradient-to-br from-indigo-500 to-blue-600 text-white shadow-md',
          background:
            'bg-indigo-50/50 dark:bg-indigo-950/20 border-l-4 border-l-indigo-500',
          label: 'text-indigo-700 dark:text-indigo-300 font-semibold',
          hover: 'hover:bg-indigo-100/50 dark:hover:bg-indigo-950/30',
        };
      default:
        return {
          avatar:
            'bg-gradient-to-br from-gray-500 to-gray-600 text-white shadow-md',
          background:
            'bg-gray-50/50 dark:bg-gray-900/50 border-l-4 border-l-gray-500',
          label: 'text-gray-700 dark:text-gray-300 font-semibold',
          hover: 'hover:bg-gray-100/50 dark:hover:bg-gray-900/30',
        };
    }
  };

  const formatContent = (
    content: string,
    type: Message['type'],
    isExpanded: boolean,
    messageId: string
  ) => {
    const shouldShowToggle =
      content.length > 800 || content.split('\n').length > 15;

    // For tool messages, try to parse and format JSON
    if (type === 'tool_use' || type === 'tool_result') {
      try {
        const parsed = JSON.parse(content);
        const formatted = JSON.stringify(parsed, null, 2);
        return (
          <div className="relative">
            <div
              className={cn(
                'overflow-hidden transition-all duration-300 ease-in-out',
                !isExpanded && shouldShowToggle && 'max-h-[400px]'
              )}
            >
              <div className="relative group">
                <button
                  onClick={() => copyToClipboard(formatted, messageId)}
                  className="absolute top-3 right-3 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 bg-white/90 dark:bg-gray-800/90 hover:bg-white dark:hover:bg-gray-700 backdrop-blur-sm shadow-lg z-10 border border-gray-200/50 dark:border-gray-600/50"
                  title="Copy JSON to clipboard"
                >
                  {copiedId === messageId ? (
                    <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <Copy className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                  )}
                </button>
                <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
                  <div className="flex items-center gap-2 px-4 py-3 bg-slate-100 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                    <Hash className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      JSON Data
                    </span>
                  </div>
                  <div className="p-4">
                    <SyntaxHighlighter
                      language="json"
                      style={oneDark}
                      customStyle={{
                        margin: 0,
                        padding: 0,
                        background: 'transparent',
                        fontSize: '0.875rem',
                        lineHeight: '1.6',
                      }}
                      wrapLines={true}
                      wrapLongLines={true}
                    >
                      {formatted}
                    </SyntaxHighlighter>
                  </div>
                </div>
              </div>
              {!isExpanded && shouldShowToggle && (
                <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-slate-950 via-white/90 dark:via-slate-950/90 to-transparent pointer-events-none" />
              )}
            </div>
            {shouldShowToggle && (
              <button
                onClick={() => toggleExpanded(messageId)}
                className="mt-4 inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-lg transition-all duration-200"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="h-4 w-4" /> Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" /> Show more (
                    {content.length} chars)
                  </>
                )}
              </button>
            )}
          </div>
        );
      } catch {
        // If not JSON, display as regular text
      }
    }

    // Check if content contains code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const hasCodeBlocks = codeBlockRegex.test(content);

    if (hasCodeBlocks) {
      const parts = content.split(codeBlockRegex);
      const formattedParts = [];

      for (let i = 0; i < parts.length; i++) {
        if (i % 3 === 0) {
          // Regular text
          if (parts[i]) {
            formattedParts.push(
              <div
                key={i}
                className="whitespace-pre-wrap break-words text-base leading-relaxed text-slate-800 dark:text-slate-200 font-normal"
                style={{ fontSize: '15px', lineHeight: '1.7' }}
              >
                {parts[i]}
              </div>
            );
          }
        } else if (i % 3 === 1) {
          // Language identifier
          const language = parts[i] || 'text';
          const code = parts[i + 1];
          if (code) {
            formattedParts.push(
              <div key={i} className="relative group my-6">
                <button
                  onClick={() =>
                    copyToClipboard(code.trim(), `${messageId}-${i}`)
                  }
                  className="absolute top-3 right-3 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 bg-white/95 dark:bg-slate-800/95 hover:bg-white dark:hover:bg-slate-700 backdrop-blur-sm shadow-lg z-10 border border-slate-200/50 dark:border-slate-600/50"
                  title={`Copy ${language} code`}
                >
                  {copiedId === `${messageId}-${i}` ? (
                    <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <Copy className="h-4 w-4 text-slate-600 dark:text-slate-400" />
                  )}
                </button>
                <div className="bg-white dark:bg-slate-900/80 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm backdrop-blur-sm">
                  <div className="flex items-center gap-3 px-4 py-3 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
                        {language === 'text' ? 'Code' : language}
                      </span>
                    </div>
                    <div className="flex gap-1.5 ml-auto">
                      <div className="w-3 h-3 rounded-full bg-red-400"></div>
                      <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                      <div className="w-3 h-3 rounded-full bg-green-400"></div>
                    </div>
                  </div>
                  <div className="relative">
                    <SyntaxHighlighter
                      language={language}
                      style={oneDark}
                      customStyle={{
                        margin: 0,
                        padding: '1.5rem',
                        background: 'transparent',
                        fontSize: '14px',
                        lineHeight: '1.6',
                      }}
                      wrapLines={true}
                      wrapLongLines={true}
                      showLineNumbers={code.trim().split('\n').length > 5}
                    >
                      {code.trim()}
                    </SyntaxHighlighter>
                  </div>
                </div>
              </div>
            );
          }
          i++; // Skip the code content as we've already processed it
        }
      }

      return (
        <div className="relative">
          <div
            className={cn(
              'overflow-hidden transition-all duration-300 ease-in-out',
              !isExpanded && shouldShowToggle && 'max-h-[400px]'
            )}
          >
            {formattedParts}
            {!isExpanded && shouldShowToggle && (
              <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-slate-950 via-white/90 dark:via-slate-950/90 to-transparent pointer-events-none" />
            )}
          </div>
          {shouldShowToggle && (
            <button
              onClick={() => toggleExpanded(messageId)}
              className="mt-4 inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-lg transition-all duration-200"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4" /> Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" /> Show more (
                  {content.length} chars)
                </>
              )}
            </button>
          )}
        </div>
      );
    }

    // For regular messages without code blocks
    return (
      <div className="relative">
        <div
          className={cn(
            'overflow-hidden transition-all duration-300 ease-in-out',
            !isExpanded && shouldShowToggle && 'max-h-[400px]'
          )}
        >
          <div
            className="whitespace-pre-wrap break-words text-base leading-relaxed text-slate-800 dark:text-slate-200 font-normal"
            style={{ fontSize: '15px', lineHeight: '1.7' }}
          >
            {content}
          </div>
          {!isExpanded && shouldShowToggle && (
            <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white dark:from-slate-950 via-white/90 dark:via-slate-950/90 to-transparent pointer-events-none" />
          )}
        </div>
        {shouldShowToggle && (
          <button
            onClick={() => toggleExpanded(messageId)}
            className="mt-4 inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-lg transition-all duration-200"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4" /> Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" /> Show more ({content.length}{' '}
                chars)
              </>
            )}
          </button>
        )}
      </div>
    );
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

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6">
        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center mb-4">
          <MessageSquare className="h-8 w-8 text-slate-400 dark:text-slate-500" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
          No messages yet
        </h3>
        <p className="text-slate-600 dark:text-slate-400 text-center max-w-sm">
          This conversation session doesn't contain any messages yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1 py-6 max-w-5xl mx-auto">
      {messageGroups.map((group) => {
        if (group.type === 'single') {
          const message = group.messages[0];
          const index = messages.indexOf(message);
          const isExpanded = expandedMessages.has(message._id);
          const isFirstMessage = index === 0;
          const previousMessage = index > 0 ? messages[index - 1] : null;
          const isDifferentSender = previousMessage?.type !== message.type;
          const colors = getMessageColors(message.type);

          return (
            <div
              key={message._id}
              className={cn(
                'relative transition-all duration-200',
                isDifferentSender && !isFirstMessage && 'mt-8'
              )}
            >
              {/* Message Header - Only show for first message or different sender */}
              {(isFirstMessage || isDifferentSender) && (
                <div className="flex items-center gap-4 px-6 py-3 mb-2">
                  <div
                    className={cn(
                      'flex items-center justify-center w-10 h-10 rounded-xl transition-transform duration-200 hover:scale-105',
                      colors.avatar
                    )}
                  >
                    {getMessageIcon(message.type)}
                  </div>
                  <div className="flex items-center gap-3 flex-1">
                    <span
                      className={cn('text-base font-semibold', colors.label)}
                    >
                      {getMessageLabel(message.type)}
                    </span>
                    {message.model && (
                      <span className="text-xs px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full font-medium border border-slate-200 dark:border-slate-700">
                        {message.model}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() =>
                      copyToClipboard(message.content, `message-${message._id}`)
                    }
                    className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200"
                    title="Copy message"
                  >
                    {copiedId === `message-${message._id}` ? (
                      <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <Copy className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                    )}
                  </button>
                </div>
              )}

              {/* Message Content */}
              <div
                className={cn(
                  'group rounded-xl mx-3 px-6 py-5 transition-all duration-200 border backdrop-blur-sm relative',
                  colors.background,
                  colors.hover,
                  'border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md'
                )}
              >
                {/* Copy button for messages without header */}
                {!isFirstMessage && !isDifferentSender && (
                  <button
                    onClick={() =>
                      copyToClipboard(message.content, `message-${message._id}`)
                    }
                    className="absolute top-4 right-4 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 bg-white/90 dark:bg-slate-800/90 hover:bg-slate-100 dark:hover:bg-slate-700 backdrop-blur-sm shadow-md border border-slate-200/50 dark:border-slate-600/50"
                    title="Copy message"
                  >
                    {copiedId === `message-${message._id}` ? (
                      <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <Copy className="h-4 w-4 text-slate-600 dark:text-slate-400" />
                    )}
                  </button>
                )}
                <div className="max-w-none">
                  {/* Metadata - Show on hover with better styling */}
                  <div className="flex items-center gap-4 mb-3 opacity-60 group-hover:opacity-100 transition-all duration-200">
                    <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 font-medium">
                      <Clock className="h-3.5 w-3.5" />
                      <time dateTime={message.timestamp}>
                        {format(new Date(message.timestamp), 'MMM d, HH:mm:ss')}
                      </time>
                    </div>
                    {getMessageCost(message) ||
                    (costMap && costMap.get(getMessageUuid(message) || '')) ? (
                      <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 font-medium">
                        <Coins className="h-3.5 w-3.5" />
                        <span>
                          $
                          {(
                            getMessageCost(message) ||
                            costMap?.get(getMessageUuid(message) || '') ||
                            0
                          ).toFixed(4)}
                        </span>
                      </div>
                    ) : null}
                    {message.inputTokens && message.outputTokens && (
                      <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400 font-medium">
                        <Hash className="h-3.5 w-3.5" />
                        <span>
                          {(
                            message.inputTokens + message.outputTokens
                          ).toLocaleString()}{' '}
                          tokens
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Message Content */}
                  <div className="prose prose-slate dark:prose-invert max-w-none">
                    {formatContent(
                      message.content,
                      message.type,
                      isExpanded,
                      message._id
                    )}
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
          const colors = getMessageColors(toolUseMessage.type);

          // Get preview of results (first few lines)
          const getResultPreview = (content: string) => {
            const lines = content.split('\n');
            const previewLines = lines.slice(0, 3);
            const hasMore = lines.length > 3;
            return {
              preview: previewLines.join('\n'),
              hasMore,
              totalLines: lines.length,
            };
          };

          const resultPreview = getResultPreview(toolResultMessage.content);

          return (
            <div
              key={pairId}
              className="relative transition-all duration-200 mt-4"
            >
              {/* Tool Pair Container */}
              <div
                className={cn(
                  'group rounded-xl mx-3 px-6 py-5 transition-all duration-200 border backdrop-blur-sm relative',
                  colors.background,
                  colors.hover,
                  'border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md'
                )}
              >
                {/* Header with expand/collapse button */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-sm mt-0.5">
                      <Wrench className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-violet-700 dark:text-violet-300">
                          Tool Operation
                        </span>
                        {toolUseMessage.model && (
                          <span className="text-xs px-2 py-0.5 bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 rounded-full font-medium">
                            {toolUseMessage.model}
                          </span>
                        )}
                      </div>

                      {/* Tool use content preview */}
                      <div className="text-sm text-slate-700 dark:text-slate-300">
                        {(() => {
                          try {
                            const parsed = JSON.parse(toolUseMessage.content);
                            return parsed.name || 'Tool call';
                          } catch {
                            return toolUseMessage.content.slice(0, 100) + '...';
                          }
                        })()}
                      </div>

                      {/* Result preview */}
                      <div className="mt-3 p-3 bg-slate-50/50 dark:bg-slate-900/30 rounded-lg border border-slate-200/50 dark:border-slate-700/50">
                        <div className="flex items-center gap-2 mb-1">
                          <Terminal className="h-3.5 w-3.5 text-slate-500" />
                          <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                            Result preview
                          </span>
                        </div>
                        <pre className="text-xs text-slate-600 dark:text-slate-400 overflow-hidden whitespace-pre-wrap break-words">
                          {resultPreview.preview}
                          {resultPreview.hasMore && (
                            <span className="text-slate-400 dark:text-slate-500">
                              {'\n'}... ({resultPreview.totalLines} lines total)
                            </span>
                          )}
                        </pre>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => toggleToolPairExpanded(pairId)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-violet-600 hover:text-violet-900 dark:text-violet-400 dark:hover:text-violet-100 bg-violet-100 hover:bg-violet-200 dark:bg-violet-900/30 dark:hover:bg-violet-800/30 rounded-lg transition-all duration-200"
                  >
                    {isPairExpanded ? (
                      <>
                        <ChevronUp className="h-3.5 w-3.5" /> Collapse
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3.5 w-3.5" /> Expand
                      </>
                    )}
                  </button>
                </div>

                {/* Expanded content */}
                {isPairExpanded && (
                  <div className="mt-4 space-y-3 border-t border-slate-200/50 dark:border-slate-700/50 pt-4">
                    {/* Tool use full content */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Wrench className="h-4 w-4 text-violet-600 dark:text-violet-400" />
                        <span className="text-sm font-medium text-violet-700 dark:text-violet-300">
                          Tool Call Details
                        </span>
                      </div>
                      <div className="prose prose-slate dark:prose-invert max-w-none">
                        {formatContent(
                          toolUseMessage.content,
                          toolUseMessage.type,
                          expandedMessages.has(toolUseMessage._id),
                          toolUseMessage._id
                        )}
                      </div>
                    </div>

                    {/* Tool result full content */}
                    <div className="mt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Terminal className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                        <span className="text-sm font-medium text-indigo-700 dark:text-indigo-300">
                          Full Result
                        </span>
                      </div>
                      <div className="prose prose-slate dark:prose-invert max-w-none">
                        {formatContent(
                          toolResultMessage.content,
                          toolResultMessage.type,
                          expandedMessages.has(toolResultMessage._id),
                          toolResultMessage._id
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Metadata footer */}
                <div className="flex items-center gap-4 mt-3 opacity-60 group-hover:opacity-100 transition-all duration-200">
                  <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 font-medium">
                    <Clock className="h-3.5 w-3.5" />
                    <time dateTime={toolUseMessage.timestamp}>
                      {format(
                        new Date(toolUseMessage.timestamp),
                        'MMM d, HH:mm:ss'
                      )}
                    </time>
                  </div>
                  {(getMessageCost(toolUseMessage) ||
                    (costMap &&
                      costMap.get(getMessageUuid(toolUseMessage) || '')) ||
                    getMessageCost(toolResultMessage) ||
                    (costMap &&
                      costMap.get(
                        getMessageUuid(toolResultMessage) || ''
                      ))) && (
                    <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 font-medium">
                      <Coins className="h-3.5 w-3.5" />
                      <span>
                        $
                        {(
                          (getMessageCost(toolUseMessage) ||
                            costMap?.get(
                              getMessageUuid(toolUseMessage) || ''
                            ) ||
                            0) +
                          (getMessageCost(toolResultMessage) ||
                            costMap?.get(
                              getMessageUuid(toolResultMessage) || ''
                            ) ||
                            0)
                        ).toFixed(4)}
                      </span>
                    </div>
                  )}
                  {(toolUseMessage.inputTokens ||
                    toolUseMessage.outputTokens) && (
                    <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400 font-medium">
                      <Hash className="h-3.5 w-3.5" />
                      <span>
                        {(
                          (toolUseMessage.inputTokens || 0) +
                          (toolUseMessage.outputTokens || 0) +
                          (toolResultMessage.inputTokens || 0) +
                          (toolResultMessage.outputTokens || 0)
                        ).toLocaleString()}{' '}
                        tokens
                      </span>
                    </div>
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
