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
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
        return 'Assistant';
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
                !isExpanded && shouldShowToggle && 'max-h-[200px]'
              )}
            >
              <div className="relative group">
                <button
                  onClick={() => copyToClipboard(formatted, messageId)}
                  className="absolute top-2 right-2 p-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity bg-gray-700 hover:bg-gray-600 z-10"
                  title="Copy to clipboard"
                >
                  {copiedId === messageId ? (
                    <Check className="h-3.5 w-3.5 text-green-400" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-gray-300" />
                  )}
                </button>
                <SyntaxHighlighter
                  language="json"
                  style={tomorrow}
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.375rem',
                    fontSize: '0.8125rem',
                    padding: '1rem',
                    backgroundColor: '#1e1e1e',
                  }}
                  wrapLines={true}
                  wrapLongLines={true}
                >
                  {formatted}
                </SyntaxHighlighter>
              </div>
              {!isExpanded && shouldShowToggle && (
                <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-[#1e1e1e] to-transparent pointer-events-none" />
              )}
            </div>
            {shouldShowToggle && (
              <button
                onClick={() => toggleExpanded(messageId)}
                className="mt-2 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 flex items-center gap-1 transition-colors"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="h-3.5 w-3.5" /> Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3.5 w-3.5" /> Show more
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
                className="whitespace-pre-wrap break-words text-sm leading-relaxed"
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
              <div key={i} className="relative group my-3">
                <button
                  onClick={() =>
                    copyToClipboard(code.trim(), `${messageId}-${i}`)
                  }
                  className="absolute top-2 right-2 p-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity bg-gray-700 hover:bg-gray-600 z-10"
                  title="Copy to clipboard"
                >
                  {copiedId === `${messageId}-${i}` ? (
                    <Check className="h-3.5 w-3.5 text-green-400" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-gray-300" />
                  )}
                </button>
                <SyntaxHighlighter
                  language={language}
                  style={tomorrow}
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.375rem',
                    fontSize: '0.8125rem',
                    padding: '1rem',
                    backgroundColor: '#1e1e1e',
                  }}
                  wrapLines={true}
                  wrapLongLines={true}
                >
                  {code.trim()}
                </SyntaxHighlighter>
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
              'max-w-none overflow-hidden transition-all duration-300',
              !isExpanded && shouldShowToggle && 'max-h-[200px]'
            )}
          >
            {formattedParts}
            {!isExpanded && shouldShowToggle && (
              <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-white dark:from-gray-900 to-transparent pointer-events-none" />
            )}
          </div>
          {shouldShowToggle && (
            <button
              onClick={() => toggleExpanded(messageId)}
              className="mt-2 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 flex items-center gap-1 transition-colors"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" /> Show less
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" /> Show more
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
            'max-w-none overflow-hidden transition-all duration-300',
            !isExpanded && shouldShowToggle && 'max-h-[200px]'
          )}
        >
          <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {content}
          </div>
          {!isExpanded && shouldShowToggle && (
            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-white dark:from-gray-900 to-transparent pointer-events-none" />
          )}
        </div>
        {shouldShowToggle && (
          <button
            onClick={() => toggleExpanded(messageId)}
            className="mt-2 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 flex items-center gap-1 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3.5 w-3.5" /> Show less
              </>
            ) : (
              <>
                <ChevronDown className="h-3.5 w-3.5" /> Show more
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
    <div className="space-y-3 px-4 py-4 max-w-5xl mx-auto">
      {messages.map((message) => {
        const isExpanded = expandedMessages.has(message._id);
        return (
          <div
            key={message._id}
            className={cn(
              'flex gap-3 p-4 rounded-lg border transition-all duration-200 shadow-sm',
              message.type === 'user' &&
                'bg-gray-50 dark:bg-gray-900/50 border-gray-200 dark:border-gray-700',
              message.type === 'assistant' &&
                'bg-white dark:bg-gray-800/50 border-gray-200 dark:border-gray-700',
              message.type === 'system' &&
                'bg-amber-50/50 dark:bg-amber-900/10 border-amber-200/50 dark:border-amber-800/30',
              message.type === 'tool_use' &&
                'bg-violet-50/50 dark:bg-violet-900/10 border-violet-200/50 dark:border-violet-800/30',
              message.type === 'tool_result' &&
                'bg-blue-50/50 dark:bg-blue-900/10 border-blue-200/50 dark:border-blue-800/30'
            )}
          >
            <div className="flex-shrink-0">
              <div
                className={cn(
                  'p-2 rounded-lg',
                  message.type === 'user' &&
                    'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
                  message.type === 'assistant' &&
                    'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300',
                  message.type === 'system' &&
                    'bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300',
                  message.type === 'tool_use' &&
                    'bg-violet-100 dark:bg-violet-900/50 text-violet-700 dark:text-violet-300',
                  message.type === 'tool_result' &&
                    'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                )}
              >
                {getMessageIcon(message.type)}
              </div>
            </div>
            <div className="flex-1 min-w-0 space-y-2">
              <div className="flex items-start justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
                    {getMessageLabel(message.type)}
                  </span>
                  {message.model && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded">
                      {message.model}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  {message.totalCost && (
                    <span>${message.totalCost.toFixed(4)}</span>
                  )}
                  {message.inputTokens && message.outputTokens && (
                    <span>
                      {message.inputTokens + message.outputTokens} tokens
                    </span>
                  )}
                  <time dateTime={message.timestamp}>
                    {format(new Date(message.timestamp), 'HH:mm:ss')}
                  </time>
                </div>
              </div>
              <div className="mt-3 overflow-x-auto">
                {formatContent(
                  message.content,
                  message.type,
                  isExpanded,
                  message._id
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
