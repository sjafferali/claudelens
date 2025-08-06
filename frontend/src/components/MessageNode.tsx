import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Message } from '../api/types';
import { formatDistanceToNow } from 'date-fns';
import { User, Bot, Wrench, FileText } from 'lucide-react';

interface MessageNodeData {
  message: Message;
  isActive?: boolean;
  onSelect?: (messageId: string) => void;
}

const MessageNode = memo(({ data, selected }: NodeProps<MessageNodeData>) => {
  const { message, isActive, onSelect } = data;

  // Determine node color based on message type
  const getNodeStyle = () => {
    const baseClasses =
      'px-4 py-3 rounded-lg shadow-md border-2 transition-all duration-200 cursor-pointer';
    const activeClasses = isActive ? 'ring-4 ring-opacity-50' : '';
    const selectedClasses = selected ? 'shadow-lg scale-105' : '';

    switch (message.type) {
      case 'user':
        return `${baseClasses} ${activeClasses} ${selectedClasses} bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 ${isActive ? 'ring-blue-400' : ''}`;
      case 'assistant':
        return `${baseClasses} ${activeClasses} ${selectedClasses} bg-emerald-50 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-700 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 ${isActive ? 'ring-emerald-400' : ''}`;
      case 'tool_use':
        return `${baseClasses} ${activeClasses} ${selectedClasses} bg-purple-50 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700 hover:bg-purple-100 dark:hover:bg-purple-900/30 ${isActive ? 'ring-purple-400' : ''}`;
      case 'tool_result':
        return `${baseClasses} ${activeClasses} ${selectedClasses} bg-violet-50 dark:bg-violet-900/20 border-violet-300 dark:border-violet-700 hover:bg-violet-100 dark:hover:bg-violet-900/30 ${isActive ? 'ring-violet-400' : ''}`;
      default:
        return `${baseClasses} ${activeClasses} ${selectedClasses} bg-slate-50 dark:bg-slate-900/20 border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-900/30 ${isActive ? 'ring-slate-400' : ''}`;
    }
  };

  // Get icon based on message type
  const getIcon = () => {
    switch (message.type) {
      case 'user':
        return <User className="w-4 h-4" />;
      case 'assistant':
        return <Bot className="w-4 h-4" />;
      case 'tool_use':
        return <Wrench className="w-4 h-4" />;
      case 'tool_result':
        return <FileText className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  // Get display text for message
  const getDisplayText = () => {
    if (message.content) {
      const text = message.content.trim();
      if (text.length > 100) {
        return text.substring(0, 100) + '...';
      }
      return text;
    }

    if (message.type === 'tool_use') {
      // Try to extract tool name from metadata or content
      const toolName = message.metadata?.toolName || 'Tool';
      return `Tool: ${toolName}`;
    }

    if (message.type === 'tool_result') {
      return 'Tool Result';
    }

    return `${message.type} message`;
  };

  // Format timestamp
  const timeAgo = message.timestamp
    ? formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })
    : '';

  const handleClick = () => {
    if (onSelect && message.uuid) {
      onSelect(message.uuid);
    }
  };

  return (
    <div
      className={getNodeStyle()}
      onClick={handleClick}
      style={{ width: '280px' }}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-400" />

      <div className="flex flex-col space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div
              className={`
              ${message.type === 'user' ? 'text-blue-600 dark:text-blue-400' : ''}
              ${message.type === 'assistant' ? 'text-emerald-600 dark:text-emerald-400' : ''}
              ${message.type === 'tool_use' ? 'text-purple-600 dark:text-purple-400' : ''}
              ${message.type === 'tool_result' ? 'text-violet-600 dark:text-violet-400' : ''}
              ${!['user', 'assistant', 'tool_use', 'tool_result'].includes(message.type || '') ? 'text-slate-600 dark:text-slate-400' : ''}
            `}
            >
              {getIcon()}
            </div>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
              {message.type === 'user'
                ? 'You'
                : message.type?.replace('_', ' ')}
            </span>
          </div>
          {message.isSidechain && (
            <span className="text-xs px-2 py-0.5 bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-300 rounded-full">
              Sidechain
            </span>
          )}
        </div>

        {/* Content */}
        <div className="text-sm text-slate-600 dark:text-slate-400 line-clamp-3">
          {getDisplayText()}
        </div>

        {/* Footer */}
        {timeAgo && (
          <div className="text-xs text-slate-500 dark:text-slate-500">
            {timeAgo}
          </div>
        )}

        {/* Branch indicator */}
        {message.branchCount && message.branchCount > 1 && (
          <div className="flex items-center space-x-1">
            <span className="text-xs px-2 py-0.5 bg-amber-200 dark:bg-amber-800 text-amber-700 dark:text-amber-300 rounded-full">
              {message.branchIndex || 1} of {message.branchCount} branches
            </span>
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-slate-400"
      />
    </div>
  );
});

MessageNode.displayName = 'MessageNode';

export default MessageNode;
