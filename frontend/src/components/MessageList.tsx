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
  const getMessageIcon = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return <User className="h-5 w-5 text-blue-600 dark:text-blue-400" />;
      case 'assistant':
        return <Bot className="h-5 w-5 text-green-600 dark:text-green-400" />;
      case 'system':
        return (
          <Terminal className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        );
      case 'tool_use':
        return (
          <Wrench className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        );
      case 'tool_result':
        return (
          <Code className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
        );
      default:
        return (
          <MessageSquare className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        );
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
              <SyntaxHighlighter
                language="json"
                style={oneDark}
                customStyle={{
                  margin: 0,
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
                wrapLines={true}
                wrapLongLines={true}
              >
                {formatted}
              </SyntaxHighlighter>
              {!isExpanded && shouldShowToggle && (
                <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[#282c34] to-transparent" />
              )}
            </div>
            {shouldShowToggle && (
              <button
                onClick={() => toggleExpanded(messageId)}
                className="mt-2 text-sm text-primary hover:text-primary/80 flex items-center gap-1"
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
              <pre
                key={i}
                className="whitespace-pre-wrap break-words font-sans"
              >
                {parts[i]}
              </pre>
            );
          }
        } else if (i % 3 === 1) {
          // Language identifier
          const language = parts[i] || 'text';
          const code = parts[i + 1];
          if (code) {
            formattedParts.push(
              <SyntaxHighlighter
                key={i}
                language={language}
                style={oneDark}
                customStyle={{
                  margin: '0.5rem 0',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
                wrapLines={true}
                wrapLongLines={true}
              >
                {code.trim()}
              </SyntaxHighlighter>
            );
          }
          i++; // Skip the code content as we've already processed it
        }
      }

      return (
        <div className="relative">
          <div
            className={cn(
              'prose prose-sm dark:prose-invert max-w-none overflow-hidden transition-all duration-300',
              !isExpanded && shouldShowToggle && 'max-h-[200px]'
            )}
          >
            {formattedParts}
            {!isExpanded && shouldShowToggle && (
              <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white dark:from-gray-950 to-transparent" />
            )}
          </div>
          {shouldShowToggle && (
            <button
              onClick={() => toggleExpanded(messageId)}
              className="mt-2 text-sm text-primary hover:text-primary/80 flex items-center gap-1"
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
            'prose prose-sm dark:prose-invert max-w-none overflow-hidden transition-all duration-300',
            !isExpanded && shouldShowToggle && 'max-h-[200px]'
          )}
        >
          <pre className="whitespace-pre-wrap break-words font-sans">
            {content}
          </pre>
          {!isExpanded && shouldShowToggle && (
            <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white dark:from-gray-950 to-transparent" />
          )}
        </div>
        {shouldShowToggle && (
          <button
            onClick={() => toggleExpanded(messageId)}
            className="mt-2 text-sm text-primary hover:text-primary/80 flex items-center gap-1"
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
    <div className="space-y-4">
      {messages.map((message) => {
        const isExpanded = expandedMessages.has(message._id);
        return (
          <div
            key={message._id}
            className={cn(
              'flex gap-3 p-4 rounded-lg border-2 transition-all duration-200',
              message.type === 'user' &&
                'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800',
              message.type === 'assistant' &&
                'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800',
              message.type === 'system' &&
                'bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800',
              message.type === 'tool_use' &&
                'bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-800',
              message.type === 'tool_result' &&
                'bg-indigo-50 dark:bg-indigo-950/30 border-indigo-200 dark:border-indigo-800'
            )}
          >
            <div className="flex-shrink-0">
              <div
                className={cn(
                  'p-2 rounded-full',
                  message.type === 'user' && 'bg-blue-100 dark:bg-blue-900',
                  message.type === 'assistant' &&
                    'bg-green-100 dark:bg-green-900',
                  message.type === 'system' &&
                    'bg-orange-100 dark:bg-orange-900',
                  message.type === 'tool_use' &&
                    'bg-purple-100 dark:bg-purple-900',
                  message.type === 'tool_result' &&
                    'bg-indigo-100 dark:bg-indigo-900'
                )}
              >
                {getMessageIcon(message.type)}
              </div>
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'font-semibold',
                      message.type === 'user' &&
                        'text-blue-700 dark:text-blue-300',
                      message.type === 'assistant' &&
                        'text-green-700 dark:text-green-300',
                      message.type === 'system' &&
                        'text-orange-700 dark:text-orange-300',
                      message.type === 'tool_use' &&
                        'text-purple-700 dark:text-purple-300',
                      message.type === 'tool_result' &&
                        'text-indigo-700 dark:text-indigo-300'
                    )}
                  >
                    {getMessageLabel(message.type)}
                  </span>
                  {message.model && (
                    <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded-full">
                      {message.model}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
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
              <div className="text-sm mt-2">
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
