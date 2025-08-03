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
  Hash,
  Zap,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { memo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageItemProps {
  message: Message;
  isExpanded: boolean;
  isCollapsedByDefault?: boolean;
  isFirstMessage: boolean;
  isDifferentSender: boolean;
  copiedId: string | null;
  onToggleExpanded: (messageId: string) => void;
  onCopy: (text: string, messageId: string) => void;
}

const MessageItem = memo(function MessageItem({
  message,
  isExpanded,
  isFirstMessage,
  isDifferentSender,
  copiedId,
  onToggleExpanded,
  onCopy,
}: MessageItemProps) {
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
        return (
          <>
            <span className="mr-1">🛠️</span>
            <Code className="h-5 w-5" />
          </>
        );
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
        return '🛠️ Tool Result';
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
          background:
            'bg-[#E6F2FF] dark:bg-[#D6ECFF]/10 border-l-4 border-l-[#3366FF]',
          label: 'text-[#1A1A1A] dark:text-blue-300 font-semibold',
          textColor: 'text-[#1A1A1A] dark:text-slate-200',
          fontWeight: 'font-semibold',
          hover: 'hover:bg-[#D6ECFF] dark:hover:bg-[#D6ECFF]/20',
        };
      case 'assistant':
        return {
          avatar:
            'bg-gradient-to-br from-cyan-500 to-cyan-600 text-white shadow-md',
          background:
            'bg-[#F0F4F8] dark:bg-[#F0F4F8]/10 border-l-4 border-l-[#00B8D9]',
          label: 'text-[#333] dark:text-cyan-300 font-medium',
          textColor: 'text-[#333] dark:text-slate-200',
          fontWeight: 'font-medium',
          fontStyle: 'italic',
          hover: 'hover:bg-[#E3EDF5] dark:hover:bg-[#F0F4F8]/20',
        };
      case 'system':
        return {
          avatar:
            'bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-md',
          background:
            'bg-amber-50/50 dark:bg-amber-950/20 border-l-4 border-l-amber-500',
          label: 'text-amber-700 dark:text-amber-300 font-semibold',
          textColor: 'text-slate-800 dark:text-slate-200',
          fontWeight: 'font-normal',
          hover: 'hover:bg-amber-100/50 dark:hover:bg-amber-950/30',
        };
      case 'tool_use':
      case 'tool_result':
        return {
          avatar:
            'bg-gradient-to-br from-slate-600 to-slate-700 text-white shadow-md',
          background:
            'bg-[#1E293B] dark:bg-[#1E293B] border-l-4 border-l-slate-500',
          label: 'text-[#C5D2E2] dark:text-[#C5D2E2] font-medium',
          textColor: 'text-[#C5D2E2] dark:text-[#C5D2E2]',
          fontWeight: 'font-normal',
          fontFamily: 'font-mono',
          hover: 'hover:bg-[#2A3444] dark:hover:bg-[#2A3444]',
        };
      default:
        return {
          avatar:
            'bg-gradient-to-br from-gray-500 to-gray-600 text-white shadow-md',
          background:
            'bg-gray-50/50 dark:bg-gray-900/50 border-l-4 border-l-gray-500',
          label: 'text-gray-700 dark:text-gray-300 font-semibold',
          textColor: 'text-slate-800 dark:text-slate-200',
          fontWeight: 'font-normal',
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
    // For tool results, always show toggle and collapse by default
    const shouldShowToggle =
      type === 'tool_result' ||
      content.length > 800 ||
      content.split('\n').length > 15;

    // Override expansion state for tool results
    const effectiveIsExpanded =
      type === 'tool_result' ? isExpanded : isExpanded;

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
                !effectiveIsExpanded &&
                  shouldShowToggle &&
                  (type === 'tool_result' ? 'max-h-[250px]' : 'max-h-[400px]')
              )}
            >
              <div className="relative group">
                <button
                  onClick={() => onCopy(formatted, messageId)}
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
                onClick={() => onToggleExpanded(messageId)}
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
                  onClick={() => onCopy(code.trim(), `${messageId}-${i}`)}
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
              onClick={() => onToggleExpanded(messageId)}
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
            onClick={() => onToggleExpanded(messageId)}
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

  const colors = getMessageColors(message.type);

  return (
    <div
      data-message-id={message._id}
      className={cn(
        'relative transition-all duration-200',
        isDifferentSender && !isFirstMessage && 'mt-8'
      )}
    >
      {/* Message Header - Only show for first message or different sender */}
      {(isFirstMessage || isDifferentSender) && (
        <div className="flex items-center gap-2 sm:gap-4 px-3 sm:px-6 py-2 sm:py-3 mb-1 sm:mb-2">
          <div
            className={cn(
              'flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl transition-transform duration-200 hover:scale-105',
              colors.avatar
            )}
          >
            {getMessageIcon(message.type)}
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-1">
            <span
              className={cn('text-sm sm:text-base font-semibold', colors.label)}
            >
              {getMessageLabel(message.type)}
            </span>
            {message.model && (
              <span className="hidden sm:inline text-xs px-2 sm:px-3 py-0.5 sm:py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full font-medium border border-slate-200 dark:border-slate-700">
                {message.model}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Message Card */}
      <div
        className={cn(
          'message-card group rounded-lg mx-4 mb-2 transition-all duration-200',
          colors.background,
          colors.hover,
          'shadow-sm hover:shadow-md'
        )}
      >
        {/* Message Header */}
        <div className="message-header flex items-center justify-between px-4 py-2 text-xs text-gray-600 dark:text-gray-400 border-b border-gray-200/30 dark:border-gray-700/30">
          <div className="flex items-center gap-2">
            <span className={cn('font-medium', colors.label)}>
              {getMessageLabel(message.type)}
            </span>
            {message.model && (
              <span className="text-gray-500 dark:text-gray-400">
                ({message.model})
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <time dateTime={message.timestamp}>
              {format(new Date(message.timestamp), 'MMM d, HH:mm:ss')}
            </time>
            {message.totalCost && <span>${message.totalCost.toFixed(4)}</span>}
            {message.inputTokens && message.outputTokens && (
              <span>
                {(message.inputTokens + message.outputTokens).toLocaleString()}{' '}
                tokens
              </span>
            )}
          </div>
        </div>

        {/* Message Body */}
        <div className="message-body px-4 py-3">
          <div
            className={cn(
              'prose prose-slate dark:prose-invert max-w-none whitespace-pre-wrap',
              colors.textColor,
              colors.fontWeight,
              colors.fontStyle,
              colors.fontFamily
            )}
          >
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
});

export default MessageItem;
