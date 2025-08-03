import { Message } from '@/api/types';
import { format } from 'date-fns';
import {
  User,
  Bot,
  Terminal,
  ChevronDown,
  ChevronUp,
  Code,
  MessageSquare,
  Wrench,
  Copy,
  Check,
  Clock,
  Coins,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
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
        return <User className="h-4 w-4" />;
      case 'assistant':
        return <Bot className="h-4 w-4" />;
      case 'system':
        return <Terminal className="h-4 w-4" />;
      case 'tool_use':
        return <Wrench className="h-4 w-4" />;
      case 'tool_result':
        return <Code className="h-4 w-4" />;
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getMessageLabel = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return 'User';
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

  const formatContent = (
    content: string,
    type: Message['type'],
    isExpanded: boolean,
    messageId: string
  ) => {
    const shouldShowToggle =
      content.length > 500 || content.split('\n').length > 10;

    // For tool messages, try to parse and format JSON
    if (type === 'tool_use' || type === 'tool_result') {
      try {
        const parsed = JSON.parse(content);
        const formatted = JSON.stringify(parsed, null, 2);
        return (
          <div className="relative">
            <div
              className={cn(
                'overflow-hidden transition-all duration-300',
                !isExpanded && shouldShowToggle && 'max-h-[300px]'
              )}
            >
              <div className="relative group">
                <button
                  onClick={() => copyToClipboard(formatted, messageId)}
                  className="absolute top-2 right-2 p-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 z-10"
                  title="Copy to clipboard"
                >
                  {copiedId === messageId ? (
                    <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-gray-600 dark:text-gray-400" />
                  )}
                </button>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-4 border border-gray-200 dark:border-gray-700">
                  <SyntaxHighlighter
                    language="json"
                    style={oneDark}
                    customStyle={{
                      margin: 0,
                      padding: 0,
                      background: 'transparent',
                      fontSize: '0.8125rem',
                    }}
                    wrapLines={true}
                    wrapLongLines={true}
                  >
                    {formatted}
                  </SyntaxHighlighter>
                </div>
              </div>
              {!isExpanded && shouldShowToggle && (
                <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white dark:from-gray-950 via-white/80 dark:via-gray-950/80 to-transparent pointer-events-none" />
              )}
            </div>
            {shouldShowToggle && (
              <button
                onClick={() => toggleExpanded(messageId)}
                className="mt-3 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 flex items-center gap-1 transition-colors"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="h-4 w-4" /> Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" /> Show more
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
                className="whitespace-pre-wrap break-words text-[0.9375rem] leading-relaxed text-gray-700 dark:text-gray-300"
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
              <div key={i} className="relative group my-4">
                <button
                  onClick={() =>
                    copyToClipboard(code.trim(), `${messageId}-${i}`)
                  }
                  className="absolute top-2 right-2 p-1.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 z-10"
                  title="Copy to clipboard"
                >
                  {copiedId === `${messageId}-${i}` ? (
                    <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-gray-600 dark:text-gray-400" />
                  )}
                </button>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-1 border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <div className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400 font-mono">
                    {language}
                  </div>
                  <SyntaxHighlighter
                    language={language}
                    style={oneDark}
                    customStyle={{
                      margin: 0,
                      padding: '1rem',
                      background: 'transparent',
                      fontSize: '0.8125rem',
                      lineHeight: '1.5',
                    }}
                    wrapLines={true}
                    wrapLongLines={true}
                  >
                    {code.trim()}
                  </SyntaxHighlighter>
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
              'overflow-hidden transition-all duration-300',
              !isExpanded && shouldShowToggle && 'max-h-[300px]'
            )}
          >
            {formattedParts}
            {!isExpanded && shouldShowToggle && (
              <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white dark:from-gray-950 via-white/80 dark:via-gray-950/80 to-transparent pointer-events-none" />
            )}
          </div>
          {shouldShowToggle && (
            <button
              onClick={() => toggleExpanded(messageId)}
              className="mt-3 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 flex items-center gap-1 transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4" /> Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" /> Show more
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
            'overflow-hidden transition-all duration-300',
            !isExpanded && shouldShowToggle && 'max-h-[300px]'
          )}
        >
          <div className="whitespace-pre-wrap break-words text-[0.9375rem] leading-relaxed text-gray-700 dark:text-gray-300">
            {content}
          </div>
          {!isExpanded && shouldShowToggle && (
            <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white dark:from-gray-950 via-white/80 dark:via-gray-950/80 to-transparent pointer-events-none" />
          )}
        </div>
        {shouldShowToggle && (
          <button
            onClick={() => toggleExpanded(messageId)}
            className="mt-3 text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 flex items-center gap-1 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4" /> Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" /> Show more
              </>
            )}
          </button>
        )}
      </div>
    );
  };

  if (messages.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No messages found in this session
      </div>
    );
  }

  return (
    <div className="space-y-0.5 py-4">
      {messages.map((message, index) => {
        const isExpanded = expandedMessages.has(message._id);
        const isFirstMessage = index === 0;
        const isLastMessage = index === messages.length - 1;
        const previousMessage = index > 0 ? messages[index - 1] : null;
        const isDifferentSender = previousMessage?.type !== message.type;

        return (
          <div
            key={message._id}
            className={cn(
              'relative',
              isDifferentSender && !isFirstMessage && 'mt-4'
            )}
          >
            {/* Message Header - Only show for first message or different sender */}
            {(isFirstMessage || isDifferentSender) && (
              <div className="flex items-center gap-3 px-6 py-2">
                <div
                  className={cn(
                    'flex items-center justify-center w-8 h-8 rounded-full',
                    message.type === 'user' &&
                      'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
                    message.type === 'assistant' &&
                      'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
                    message.type === 'system' &&
                      'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
                    message.type === 'tool_use' &&
                      'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
                    message.type === 'tool_result' &&
                      'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                  )}
                >
                  {getMessageIcon(message.type)}
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
                    {getMessageLabel(message.type)}
                  </span>
                  {message.model && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
                      {message.model}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Message Content */}
            <div
              className={cn(
                'group px-6 py-3 hover:bg-gray-50/50 dark:hover:bg-gray-900/20 transition-colors',
                message.type === 'user' && 'bg-white dark:bg-gray-950',
                message.type === 'assistant' &&
                  'bg-gray-50/50 dark:bg-gray-900/30',
                message.type === 'system' &&
                  'bg-amber-50/30 dark:bg-amber-900/10',
                message.type === 'tool_use' &&
                  'bg-purple-50/30 dark:bg-purple-900/10',
                message.type === 'tool_result' &&
                  'bg-emerald-50/30 dark:bg-emerald-900/10',
                isLastMessage && 'rounded-b-lg'
              )}
            >
              <div className="max-w-4xl">
                {/* Metadata - Show on hover */}
                <div className="flex items-center gap-3 mb-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                    <Clock className="h-3 w-3" />
                    <time dateTime={message.timestamp}>
                      {format(new Date(message.timestamp), 'HH:mm:ss')}
                    </time>
                  </div>
                  {message.totalCost && (
                    <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                      <Coins className="h-3 w-3" />
                      <span>${message.totalCost.toFixed(4)}</span>
                    </div>
                  )}
                  {message.inputTokens && message.outputTokens && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {message.inputTokens + message.outputTokens} tokens
                    </span>
                  )}
                </div>

                {/* Message Content */}
                <div>
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
      })}
    </div>
  );
}
