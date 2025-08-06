import { memo, useCallback, useMemo, useState } from 'react';
import { Message } from '@/api/types';
import { format } from 'date-fns';
import {
  User,
  Bot,
  Wrench,
  Copy,
  Check,
  Coins,
  Share2,
  Bug,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { getMessageUuid } from '@/types/message-extensions';
import { copyToClipboard } from '@/utils/clipboard';
import { MessageNavigationButtons } from './MessageNavigationButtons';
import { useMessageNavigation } from '@/hooks/useMessageNavigation';
import {
  copyMessageLink,
  getMessageLinkDescription,
} from '@/utils/message-linking';
import toast from 'react-hot-toast';

// Memoized message header component
const MessageHeader = memo(
  ({
    message,
    cost,
    position,
    totalMessages,
  }: {
    message: Message;
    cost: number;
    position: number;
    totalMessages: number;
  }) => {
    const messageType = message.type;
    const isUser = messageType === 'user';
    const isAssistant = messageType === 'assistant';

    return (
      <div className="flex items-center gap-2 mb-2">
        <div
          className={cn(
            'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
            isUser
              ? 'bg-blue-500'
              : isAssistant
                ? 'bg-emerald-500'
                : 'bg-purple-500'
          )}
        >
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : isAssistant ? (
            <Bot className="w-5 h-5 text-white" />
          ) : (
            <Wrench className="w-5 h-5 text-white" />
          )}
        </div>

        <span className="font-medium text-primary-c">
          {isUser ? 'You' : isAssistant ? 'Claude' : 'Tool'}
        </span>

        <span className="text-xs text-muted-c">
          {format(new Date(message.created_at || 0), 'h:mm a')}
        </span>

        {cost > 0 && (
          <span className="text-xs text-muted-c flex items-center gap-1">
            <Coins className="w-3 h-3" />${cost.toFixed(4)}
          </span>
        )}

        <span className="text-xs text-muted-c font-mono ml-auto">
          #{position} of {totalMessages}
        </span>
      </div>
    );
  }
);

MessageHeader.displayName = 'MessageHeader';

// Memoized message content component
const MessageContent = memo(({ content }: { content: string }) => {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <div className="whitespace-pre-wrap break-words">{content}</div>
    </div>
  );
});

MessageContent.displayName = 'MessageContent';

// Memoized message actions component
const MessageActions = memo(
  ({
    message,
    sessionId,
    onCopy,
    onShare,
    onDebug,
  }: {
    message: Message;
    sessionId?: string;
    onCopy: (message: Message) => void;
    onShare: (message: Message) => void;
    onDebug?: (message: Message) => void;
  }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = useCallback(() => {
      onCopy(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }, [message, onCopy]);

    return (
      <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handleCopy}
          className="p-1 hover:bg-layer-tertiary rounded"
          title="Copy message"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-500" />
          ) : (
            <Copy className="w-4 h-4 text-muted-c" />
          )}
        </button>

        {sessionId && (
          <button
            onClick={() => onShare(message)}
            className="p-1 hover:bg-layer-tertiary rounded"
            title="Share link"
          >
            <Share2 className="w-4 h-4 text-muted-c" />
          </button>
        )}

        {onDebug && (
          <button
            onClick={() => onDebug(message)}
            className="p-1 hover:bg-layer-tertiary rounded"
            title="Debug"
          >
            <Bug className="w-4 h-4 text-muted-c" />
          </button>
        )}
      </div>
    );
  }
);

MessageActions.displayName = 'MessageActions';

// Memoized single message component
const MessageItem = memo(
  ({
    message,
    cost,
    position,
    totalMessages,
    sessionId,
    onCopy,
    onShare,
    onDebug,
    onNavigate,
    hasParent,
    hasChildren,
  }: {
    message: Message;
    cost: number;
    position: number;
    totalMessages: number;
    sessionId?: string;
    onCopy: (message: Message) => void;
    onShare: (message: Message) => void;
    onDebug?: (message: Message) => void;
    onNavigate?: (messageId: string) => void;
    hasParent: boolean;
    hasChildren: boolean;
  }) => {
    const messageId = getMessageUuid(message);

    return (
      <div
        id={`message-${messageId}`}
        className={cn(
          'group relative px-6 py-4',
          message.type === 'assistant'
            ? 'bg-layer-secondary'
            : 'bg-layer-primary'
        )}
      >
        <MessageHeader
          message={message}
          cost={cost}
          position={position}
          totalMessages={totalMessages}
        />

        {message.content && <MessageContent content={message.content} />}

        {onNavigate && (hasParent || hasChildren) && (
          <MessageNavigationButtons
            message={message}
            hasParent={hasParent}
            hasChildren={hasChildren}
            onNavigateToParent={() =>
              message.parent_uuid ? onNavigate(message.parent_uuid) : undefined
            }
            onNavigateToChildren={() =>
              messageId ? onNavigate(messageId) : undefined
            }
          />
        )}

        <MessageActions
          message={message}
          sessionId={sessionId}
          onCopy={onCopy}
          onShare={onShare}
          onDebug={onDebug}
        />
      </div>
    );
  }
);

MessageItem.displayName = 'MessageItem';

// Main optimized message list component
interface OptimizedMessageListProps {
  messages: Message[];
  costMap?: Map<string, number>;
  sessionId?: string;
  onDebugMessage?: (message: Message) => void;
}

export const OptimizedMessageList = memo(
  ({
    messages,
    costMap = new Map(),
    sessionId,
    onDebugMessage,
  }: OptimizedMessageListProps) => {
    const { navigateToMessage } = useMessageNavigation(messages);

    // Memoize message filtering
    const filteredMessages = useMemo(() => {
      return messages.filter(
        (msg) => msg.type !== 'tool_use' && msg.type !== 'tool_result'
      );
    }, [messages]);

    // Create parent/child lookup maps
    const { parentMap, childrenMap } = useMemo(() => {
      const parents = new Map<string, boolean>();
      const children = new Map<string, boolean>();

      messages.forEach((msg) => {
        const id = getMessageUuid(msg);
        if (msg.parent_uuid) {
          parents.set(id, true);
          children.set(msg.parent_uuid, true);
        }
      });

      return { parentMap: parents, childrenMap: children };
    }, [messages]);

    // Memoized callbacks
    const handleCopy = useCallback(async (message: Message) => {
      const success = await copyToClipboard(message.content || '');
      if (success) {
        toast.success('Message copied to clipboard');
      }
    }, []);

    const handleShare = useCallback(
      (message: Message) => {
        if (!sessionId) return;
        const messageId = getMessageUuid(message);
        if (!messageId) return;
        const description = getMessageLinkDescription(message);
        copyMessageLink(sessionId, messageId);
        toast.success(`Copied link to ${description}`);
      },
      [sessionId]
    );

    const handleNavigate = useCallback(
      (messageId: string | undefined) => {
        if (messageId) {
          navigateToMessage(messageId);
        }
      },
      [navigateToMessage]
    );

    return (
      <div className="divide-y divide-border">
        {filteredMessages.map((message, index) => {
          const messageId = getMessageUuid(message);
          const cost = costMap.get(messageId) || 0;
          const hasParent = parentMap.has(messageId);
          const hasChildren = childrenMap.has(messageId);

          return (
            <MessageItem
              key={messageId}
              message={message}
              cost={cost}
              position={index + 1}
              totalMessages={filteredMessages.length}
              sessionId={sessionId}
              onCopy={handleCopy}
              onShare={handleShare}
              onDebug={onDebugMessage}
              onNavigate={handleNavigate}
              hasParent={hasParent}
              hasChildren={hasChildren}
            />
          );
        })}
      </div>
    );
  }
);

OptimizedMessageList.displayName = 'OptimizedMessageList';

export default OptimizedMessageList;
