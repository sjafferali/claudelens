import { useState, useRef, useEffect, useMemo } from 'react';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';
import {
  GitBranch,
  ChevronDown,
  Check,
  Download,
  X,
  Maximize2,
  Minimize2,
  Link2,
  Link2Off,
} from 'lucide-react';
import { getBranchAlternatives } from '@/utils/branch-detection';
import { getMessageCost } from '@/types/message-extensions';
import { format } from 'date-fns';

interface ConversationBranchComparisonProps {
  messages: Message[];
  targetMessage: Message;
  onSelectBranch?: (branchUuid: string) => void;
  onClose?: () => void;
  className?: string;
}

interface BranchMetrics {
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  cost: number;
  timestamp: string;
  messageCount: number;
  toolUsageCount: number;
}

export function ConversationBranchComparison({
  messages,
  targetMessage,
  onSelectBranch,
  onClose,
  className,
}: ConversationBranchComparisonProps) {
  const [selectedBranches, setSelectedBranches] = useState<[string, string]>([
    '',
    '',
  ]);
  const [synchronizedScroll, setSynchronizedScroll] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [highlightDifferences, setHighlightDifferences] = useState(true);

  const leftPaneRef = useRef<HTMLDivElement>(null);
  const rightPaneRef = useRef<HTMLDivElement>(null);
  const isScrollingSyncRef = useRef(false);

  // Get all branch alternatives
  const branchAlternatives = useMemo(() => {
    if (!targetMessage.branches) return [];
    return getBranchAlternatives(
      messages,
      targetMessage.uuid || targetMessage.messageUuid
    );
  }, [messages, targetMessage]);

  // Initialize selected branches
  useEffect(() => {
    if (branchAlternatives.length >= 2) {
      setSelectedBranches([
        branchAlternatives[0].uuid || branchAlternatives[0].messageUuid,
        branchAlternatives[1].uuid || branchAlternatives[1].messageUuid,
      ]);
    } else if (branchAlternatives.length === 1) {
      setSelectedBranches([
        branchAlternatives[0].uuid || branchAlternatives[0].messageUuid,
        '',
      ]);
    }
  }, [branchAlternatives]);

  // Synchronized scrolling
  useEffect(() => {
    if (!synchronizedScroll) return;

    const handleScroll = (source: 'left' | 'right') => {
      if (isScrollingSyncRef.current) return;
      isScrollingSyncRef.current = true;

      const sourcePane =
        source === 'left' ? leftPaneRef.current : rightPaneRef.current;
      const targetPane =
        source === 'left' ? rightPaneRef.current : leftPaneRef.current;

      if (sourcePane && targetPane) {
        const scrollPercentage =
          sourcePane.scrollTop /
          (sourcePane.scrollHeight - sourcePane.clientHeight);
        targetPane.scrollTop =
          scrollPercentage *
          (targetPane.scrollHeight - targetPane.clientHeight);
      }

      requestAnimationFrame(() => {
        isScrollingSyncRef.current = false;
      });
    };

    const leftScrollHandler = () => handleScroll('left');
    const rightScrollHandler = () => handleScroll('right');

    const leftPane = leftPaneRef.current;
    const rightPane = rightPaneRef.current;

    leftPane?.addEventListener('scroll', leftScrollHandler);
    rightPane?.addEventListener('scroll', rightScrollHandler);

    return () => {
      leftPane?.removeEventListener('scroll', leftScrollHandler);
      rightPane?.removeEventListener('scroll', rightScrollHandler);
    };
  }, [synchronizedScroll]);

  // Calculate metrics for a branch
  const calculateBranchMetrics = (branchUuid: string): BranchMetrics => {
    const branch = branchAlternatives.find(
      (b) => (b.uuid || b.messageUuid) === branchUuid
    );

    if (!branch) {
      return {
        totalTokens: 0,
        inputTokens: 0,
        outputTokens: 0,
        cost: 0,
        timestamp: '',
        messageCount: 0,
        toolUsageCount: 0,
      };
    }

    // Get all descendant messages from this branch
    const descendants = getDescendantMessages(messages, branchUuid);
    const allBranchMessages = [branch, ...descendants];

    const totalTokens = allBranchMessages.reduce(
      (sum, msg) => sum + ((msg.inputTokens || 0) + (msg.outputTokens || 0)),
      0
    );
    const inputTokens = allBranchMessages.reduce(
      (sum, msg) => sum + (msg.inputTokens || 0),
      0
    );
    const outputTokens = allBranchMessages.reduce(
      (sum, msg) => sum + (msg.outputTokens || 0),
      0
    );
    const cost = allBranchMessages.reduce(
      (sum, msg) => sum + (getMessageCost(msg) || 0),
      0
    );
    const toolUsageCount = allBranchMessages.filter(
      (msg) => msg.type === 'tool_use'
    ).length;

    return {
      totalTokens,
      inputTokens,
      outputTokens,
      cost,
      timestamp: branch.timestamp,
      messageCount: allBranchMessages.length,
      toolUsageCount,
    };
  };

  // Get descendant messages from a branch
  const getDescendantMessages = (
    allMessages: Message[],
    startUuid: string
  ): Message[] => {
    const descendants: Message[] = [];
    const queue = [startUuid];
    const visited = new Set<string>();

    while (queue.length > 0) {
      const currentUuid = queue.shift()!;
      if (visited.has(currentUuid)) continue;
      visited.add(currentUuid);

      const children = allMessages.filter(
        (msg) => msg.parentUuid === currentUuid
      );
      descendants.push(...children);
      queue.push(...children.map((c) => c.uuid || c.messageUuid));
    }

    return descendants;
  };

  // Export comparison as JSON
  const handleExport = () => {
    const comparisonData = {
      timestamp: new Date().toISOString(),
      branches: selectedBranches.map((branchUuid) => {
        const branch = branchAlternatives.find(
          (b) => (b.uuid || b.messageUuid) === branchUuid
        );
        const metrics = calculateBranchMetrics(branchUuid);
        return {
          uuid: branchUuid,
          content: branch?.content || '',
          metrics,
        };
      }),
    };

    const blob = new Blob([JSON.stringify(comparisonData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `branch-comparison-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Highlight differences between two texts
  const highlightTextDifferences = (text1: string, text2: string) => {
    if (!highlightDifferences) return { left: text1, right: text2 };

    // Simple word-based diff highlighting
    const words1 = text1.split(/\s+/);
    const words2 = text2.split(/\s+/);

    // This is a simplified diff - in production, use a proper diff library
    const maxLength = Math.max(words1.length, words2.length);
    const highlightedLeft: React.ReactNode[] = [];
    const highlightedRight: React.ReactNode[] = [];

    for (let i = 0; i < maxLength; i++) {
      const word1 = words1[i] || '';
      const word2 = words2[i] || '';

      if (word1 === word2) {
        highlightedLeft.push(word1 + ' ');
        highlightedRight.push(word2 + ' ');
      } else {
        highlightedLeft.push(
          <span
            key={i}
            className="bg-red-100 dark:bg-red-900/30 text-red-900 dark:text-red-100"
          >
            {word1}{' '}
          </span>
        );
        highlightedRight.push(
          <span
            key={i}
            className="bg-green-100 dark:bg-green-900/30 text-green-900 dark:text-green-100"
          >
            {word2}{' '}
          </span>
        );
      }
    }

    return { left: highlightedLeft, right: highlightedRight };
  };

  const renderBranchPane = (branchUuid: string, side: 'left' | 'right') => {
    const branch = branchAlternatives.find(
      (b) => (b.uuid || b.messageUuid) === branchUuid
    );

    if (!branch) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          Select a branch to compare
        </div>
      );
    }

    const metrics = calculateBranchMetrics(branchUuid);
    const otherBranchUuid =
      side === 'left' ? selectedBranches[1] : selectedBranches[0];
    const otherBranch = branchAlternatives.find(
      (b) => (b.uuid || b.messageUuid) === otherBranchUuid
    );

    const { left: leftHighlighted, right: rightHighlighted } =
      highlightTextDifferences(
        side === 'left' ? branch.content : otherBranch?.content || '',
        side === 'left' ? otherBranch?.content || '' : branch.content
      );

    return (
      <div className="h-full flex flex-col">
        {/* Branch selector dropdown */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center justify-between mb-3">
            <div className="relative flex-1">
              <select
                value={branchUuid}
                onChange={(e) => {
                  const newBranches: [string, string] = [...selectedBranches];
                  newBranches[side === 'left' ? 0 : 1] = e.target.value;
                  setSelectedBranches(newBranches);
                }}
                className={cn(
                  'w-full px-3 py-2 pr-8',
                  'bg-white dark:bg-gray-800',
                  'border border-gray-300 dark:border-gray-600',
                  'rounded-lg',
                  'text-sm',
                  'appearance-none',
                  'focus:outline-none focus:ring-2 focus:ring-primary'
                )}
              >
                <option value="">Select a branch</option>
                {branchAlternatives.map((alt, index) => (
                  <option
                    key={alt.uuid || alt.messageUuid}
                    value={alt.uuid || alt.messageUuid}
                  >
                    Branch {index + 1} -{' '}
                    {format(new Date(alt.timestamp), 'MMM d, h:mm a')}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-3 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>

            {onSelectBranch && (
              <button
                onClick={() => onSelectBranch(branchUuid)}
                className={cn(
                  'ml-2 px-3 py-2',
                  'bg-primary text-white',
                  'rounded-lg',
                  'hover:bg-primary/90',
                  'transition-colors',
                  'text-sm font-medium',
                  'flex items-center gap-1'
                )}
              >
                <Check className="h-4 w-4" />
                Select
              </button>
            )}
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="bg-white dark:bg-gray-800 p-2 rounded">
              <div className="text-gray-500 dark:text-gray-400">Tokens</div>
              <div className="font-semibold">
                {metrics.totalTokens.toLocaleString()}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-2 rounded">
              <div className="text-gray-500 dark:text-gray-400">Cost</div>
              <div className="font-semibold">${metrics.cost.toFixed(4)}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-2 rounded">
              <div className="text-gray-500 dark:text-gray-400">Tools</div>
              <div className="font-semibold">{metrics.toolUsageCount}</div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div
          ref={side === 'left' ? leftPaneRef : rightPaneRef}
          className="flex-1 overflow-y-auto p-4"
        >
          <div className="prose dark:prose-invert max-w-none">
            <div className="whitespace-pre-wrap">
              {highlightDifferences && otherBranch
                ? side === 'left'
                  ? leftHighlighted
                  : rightHighlighted
                : branch.content}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-900',
        'border border-gray-200 dark:border-gray-700',
        'rounded-lg shadow-xl',
        isFullscreen ? 'fixed inset-0 z-50' : 'relative',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            <h2 className="text-lg font-semibold">Branch Comparison</h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              ({branchAlternatives.length} branches)
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Sync scroll toggle */}
            <button
              onClick={() => setSynchronizedScroll(!synchronizedScroll)}
              className={cn(
                'p-2 rounded-lg transition-colors',
                synchronizedScroll
                  ? 'bg-primary text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              )}
              title={
                synchronizedScroll
                  ? 'Disable synchronized scrolling'
                  : 'Enable synchronized scrolling'
              }
            >
              {synchronizedScroll ? (
                <Link2 className="h-4 w-4" />
              ) : (
                <Link2Off className="h-4 w-4" />
              )}
            </button>

            {/* Highlight differences toggle */}
            <button
              onClick={() => setHighlightDifferences(!highlightDifferences)}
              className={cn(
                'px-3 py-2 rounded-lg transition-colors text-sm',
                highlightDifferences
                  ? 'bg-primary text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              )}
            >
              Highlight Differences
            </button>

            {/* Export button */}
            <button
              onClick={handleExport}
              className={cn(
                'p-2 rounded-lg transition-colors',
                'bg-gray-200 dark:bg-gray-700',
                'hover:bg-gray-300 dark:hover:bg-gray-600',
                'text-gray-600 dark:text-gray-400'
              )}
              title="Export comparison"
            >
              <Download className="h-4 w-4" />
            </button>

            {/* Fullscreen toggle */}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className={cn(
                'p-2 rounded-lg transition-colors',
                'bg-gray-200 dark:bg-gray-700',
                'hover:bg-gray-300 dark:hover:bg-gray-600',
                'text-gray-600 dark:text-gray-400'
              )}
              title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </button>

            {/* Close button */}
            {onClose && (
              <button
                onClick={onClose}
                className={cn(
                  'p-2 rounded-lg transition-colors',
                  'bg-gray-200 dark:bg-gray-700',
                  'hover:bg-gray-300 dark:hover:bg-gray-600',
                  'text-gray-600 dark:text-gray-400'
                )}
                title="Close comparison"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Split panes */}
      <div className="flex h-[600px]">
        {/* Left pane */}
        <div className="flex-1 border-r border-gray-200 dark:border-gray-700">
          {renderBranchPane(selectedBranches[0], 'left')}
        </div>

        {/* Right pane */}
        <div className="flex-1">
          {renderBranchPane(selectedBranches[1], 'right')}
        </div>
      </div>
    </div>
  );
}

export default ConversationBranchComparison;
