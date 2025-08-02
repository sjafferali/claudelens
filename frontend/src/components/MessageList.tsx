import { Message } from '@/api/types';
import { format } from 'date-fns';
import { User, Bot, Terminal, FileCode } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  const getMessageIcon = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return <User className="h-5 w-5" />;
      case 'assistant':
        return <Bot className="h-5 w-5" />;
      case 'system':
        return <Terminal className="h-5 w-5" />;
      case 'tool_use':
      case 'tool_result':
        return <FileCode className="h-5 w-5" />;
      default:
        return null;
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

  const formatContent = (content: string, type: Message['type']) => {
    // For tool messages, try to parse and format JSON
    if (type === 'tool_use' || type === 'tool_result') {
      try {
        const parsed = JSON.parse(content);
        return (
          <pre className="text-sm overflow-x-auto">
            <code>{JSON.stringify(parsed, null, 2)}</code>
          </pre>
        );
      } catch {
        // If not JSON, display as regular text
      }
    }

    // For regular messages, preserve line breaks and format code blocks
    return (
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <pre className="whitespace-pre-wrap break-words">{content}</pre>
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
      {messages.map((message) => (
        <div
          key={message._id}
          className={cn(
            'flex gap-3 p-4 rounded-lg',
            message.type === 'user' && 'bg-primary/5',
            message.type === 'assistant' && 'bg-secondary/30',
            message.type === 'system' && 'bg-muted/50',
            (message.type === 'tool_use' || message.type === 'tool_result') &&
              'bg-accent/30'
          )}
        >
          <div className="flex-shrink-0 mt-1">
            {getMessageIcon(message.type)}
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-medium">
                  {getMessageLabel(message.type)}
                </span>
                {message.model && (
                  <span className="text-xs px-2 py-1 bg-secondary rounded-md">
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
            <div className="text-sm">
              {formatContent(message.content, message.type)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
