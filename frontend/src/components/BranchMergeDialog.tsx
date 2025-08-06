import { useState, useMemo } from 'react';
import { Message } from '@/api/types';
import { cn } from '@/utils/cn';
import {
  GitMerge,
  Check,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Zap,
  List,
  Cherry,
  Loader2,
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { getBranchAlternatives } from '@/utils/branch-detection';
import { format } from 'date-fns';

interface BranchMergeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  messages: Message[];
  targetMessage: Message;
  onMerge: (mergedContent: MergeResult) => void;
  className?: string;
}

export interface MergeResult {
  strategy: MergeStrategy;
  mergedMessages: Message[];
  summary: string;
  selectedBranches: string[];
  conflicts?: MergeConflict[];
}

interface MergeConflict {
  branchUuids: string[];
  conflictType: 'content' | 'timing' | 'dependency';
  resolution?: 'first' | 'last' | 'manual' | 'ai';
  description: string;
}

type MergeStrategy = 'sequential' | 'intelligent' | 'cherry-pick';

interface BranchSelection {
  uuid: string;
  selected: boolean;
  message: Message;
  order?: number;
}

interface CherryPickSelection {
  branchUuid: string;
  messageUuids: string[];
}

export function BranchMergeDialog({
  open,
  onOpenChange,
  messages,
  targetMessage,
  onMerge,
  className,
}: BranchMergeDialogProps) {
  const [selectedStrategy, setSelectedStrategy] =
    useState<MergeStrategy>('sequential');
  const [branchSelections, setBranchSelections] = useState<BranchSelection[]>(
    []
  );
  const [cherryPickSelections, setCherryPickSelections] = useState<
    CherryPickSelection[]
  >([]);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isMerging, setIsMerging] = useState(false);
  const [conflicts, setConflicts] = useState<MergeConflict[]>([]);
  const [mergePreview, setMergePreview] = useState<Message[]>([]);

  // Get all branch alternatives
  const branchAlternatives = useMemo(() => {
    if (!targetMessage.branches) return [];
    return getBranchAlternatives(
      messages,
      targetMessage.uuid || targetMessage.messageUuid
    );
  }, [messages, targetMessage]);

  // Initialize branch selections
  useMemo(() => {
    const selections: BranchSelection[] = branchAlternatives.map((branch) => ({
      uuid: branch.uuid || branch.messageUuid,
      selected: false,
      message: branch,
    }));
    setBranchSelections(selections);
  }, [branchAlternatives]);

  // Toggle branch selection
  const toggleBranchSelection = (uuid: string) => {
    setBranchSelections((prev) =>
      prev.map((sel) =>
        sel.uuid === uuid ? { ...sel, selected: !sel.selected } : sel
      )
    );
  };

  // Toggle all branches
  const toggleAllBranches = () => {
    const allSelected = branchSelections.every((sel) => sel.selected);
    setBranchSelections((prev) =>
      prev.map((sel) => ({ ...sel, selected: !allSelected }))
    );
  };

  // Get selected branch count
  const selectedBranchCount = branchSelections.filter(
    (sel) => sel.selected
  ).length;

  // Get descendant messages for a branch
  const getDescendantMessages = (branchUuid: string): Message[] => {
    const descendants: Message[] = [];
    const queue = [branchUuid];
    const visited = new Set<string>();

    while (queue.length > 0) {
      const currentUuid = queue.shift()!;
      if (visited.has(currentUuid)) continue;
      visited.add(currentUuid);

      const children = messages.filter((msg) => msg.parentUuid === currentUuid);
      descendants.push(...children);
      queue.push(...children.map((c) => c.uuid || c.messageUuid));
    }

    return descendants;
  };

  // Generate merge preview
  const generateMergePreview = async () => {
    setIsPreviewOpen(true);
    setIsMerging(true);

    const selectedBranches = branchSelections.filter((sel) => sel.selected);

    if (selectedBranches.length === 0) {
      setIsMerging(false);
      return;
    }

    try {
      let merged: Message[] = [];
      let detectedConflicts: MergeConflict[] = [];

      switch (selectedStrategy) {
        case 'sequential':
          // Merge branches in order they appear
          merged = mergeSequential(selectedBranches);
          break;

        case 'intelligent': {
          // AI-powered merge to combine best parts
          const {
            messages: intelligentMerged,
            conflicts: intelligentConflicts,
          } = await mergeIntelligent(selectedBranches);
          merged = intelligentMerged;
          detectedConflicts = intelligentConflicts;
          break;
        }

        case 'cherry-pick':
          // Merge only selected messages from each branch
          merged = mergeCherryPick(selectedBranches, cherryPickSelections);
          break;
      }

      setMergePreview(merged);
      setConflicts(detectedConflicts);
    } finally {
      setIsMerging(false);
    }
  };

  // Sequential merge strategy
  const mergeSequential = (branches: BranchSelection[]): Message[] => {
    const merged: Message[] = [];

    branches.forEach((branch, index) => {
      const branchMessage = branch.message;
      const descendants = getDescendantMessages(branch.uuid);

      // Add branch message with modified parentUuid if not first
      if (index === 0) {
        merged.push(branchMessage);
      } else {
        // Connect to the last message of previous branch
        const lastMessage = merged[merged.length - 1];
        merged.push({
          ...branchMessage,
          parentUuid: lastMessage.uuid || lastMessage.messageUuid,
        });
      }

      // Add descendants
      merged.push(...descendants);
    });

    return merged;
  };

  // Intelligent merge strategy (simplified - would call backend AI)
  const mergeIntelligent = async (
    branches: BranchSelection[]
  ): Promise<{ messages: Message[]; conflicts: MergeConflict[] }> => {
    // This would normally call a backend endpoint that uses AI to merge
    // For now, we'll simulate with a simple heuristic

    const conflicts: MergeConflict[] = [];
    const merged: Message[] = [];

    // Analyze branches for conflicts
    branches.forEach((branch, i) => {
      branches.slice(i + 1).forEach((otherBranch) => {
        // Check for content similarity (simplified)
        if (
          branch.message.content.length > 100 &&
          otherBranch.message.content.length > 100
        ) {
          const overlap = checkContentOverlap(
            branch.message.content,
            otherBranch.message.content
          );

          if (overlap > 0.5) {
            conflicts.push({
              branchUuids: [branch.uuid, otherBranch.uuid],
              conflictType: 'content',
              description: 'Similar content detected between branches',
              resolution: 'ai',
            });
          }
        }
      });
    });

    // Create merged content (simplified)
    const primaryBranch = branches[0];
    merged.push(primaryBranch.message);

    // Add unique content from other branches
    branches.slice(1).forEach((branch) => {
      const descendants = getDescendantMessages(branch.uuid);
      const uniqueMessages = descendants.filter(
        (msg) => !hasSimularContent(merged, msg)
      );
      merged.push(...uniqueMessages);
    });

    return { messages: merged, conflicts };
  };

  // Cherry-pick merge strategy
  const mergeCherryPick = (
    branches: BranchSelection[],
    selections: CherryPickSelection[]
  ): Message[] => {
    const merged: Message[] = [];
    let lastParentUuid: string | undefined = targetMessage.parentUuid;

    selections.forEach((selection) => {
      const branch = branches.find((b) => b.uuid === selection.branchUuid);
      if (!branch) return;

      // Add selected messages from this branch
      selection.messageUuids.forEach((msgUuid) => {
        const message = messages.find(
          (m) => (m.uuid || m.messageUuid) === msgUuid
        );
        if (message) {
          // Update parent UUID to maintain chain
          merged.push({
            ...message,
            parentUuid: lastParentUuid,
          });
          lastParentUuid = message.uuid || message.messageUuid;
        }
      });
    });

    return merged;
  };

  // Toggle cherry-pick message selection
  const toggleCherryPickMessage = (branchUuid: string, messageUuid: string) => {
    setCherryPickSelections((prev) => {
      const existing = prev.find((sel) => sel.branchUuid === branchUuid);

      if (existing) {
        const messageIndex = existing.messageUuids.indexOf(messageUuid);
        if (messageIndex > -1) {
          // Remove message
          return prev.map((sel) =>
            sel.branchUuid === branchUuid
              ? {
                  ...sel,
                  messageUuids: sel.messageUuids.filter(
                    (id) => id !== messageUuid
                  ),
                }
              : sel
          );
        } else {
          // Add message
          return prev.map((sel) =>
            sel.branchUuid === branchUuid
              ? {
                  ...sel,
                  messageUuids: [...sel.messageUuids, messageUuid],
                }
              : sel
          );
        }
      } else {
        // Create new selection
        return [...prev, { branchUuid, messageUuids: [messageUuid] }];
      }
    });
  };

  // Check content overlap (simplified)
  const checkContentOverlap = (content1: string, content2: string): number => {
    const words1 = new Set(content1.toLowerCase().split(/\s+/));
    const words2 = new Set(content2.toLowerCase().split(/\s+/));
    const intersection = new Set([...words1].filter((x) => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    return intersection.size / union.size;
  };

  // Check if similar content exists
  const hasSimularContent = (
    messages: Message[],
    newMessage: Message
  ): boolean => {
    return messages.some(
      (msg) => checkContentOverlap(msg.content, newMessage.content) > 0.8
    );
  };

  // Handle merge execution
  const handleMerge = () => {
    const selectedBranchUuids = branchSelections
      .filter((sel) => sel.selected)
      .map((sel) => sel.uuid);

    const result: MergeResult = {
      strategy: selectedStrategy,
      mergedMessages: mergePreview,
      summary: generateMergeSummary(),
      selectedBranches: selectedBranchUuids,
      conflicts: conflicts.length > 0 ? conflicts : undefined,
    };

    onMerge(result);
    onOpenChange(false);
  };

  // Generate merge summary
  const generateMergeSummary = (): string => {
    const branchCount = selectedBranchCount;
    const messageCount = mergePreview.length;
    const conflictCount = conflicts.length;

    let summary = `Merged ${branchCount} branches using ${selectedStrategy} strategy. `;
    summary += `Created ${messageCount} messages in the merged branch. `;

    if (conflictCount > 0) {
      summary += `Resolved ${conflictCount} conflicts. `;
    }

    return summary;
  };

  // Render strategy selector
  const renderStrategySelector = () => (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Merge Strategy
      </label>
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => setSelectedStrategy('sequential')}
          className={cn(
            'p-3 rounded-lg border-2 transition-all',
            'flex flex-col items-center gap-2',
            selectedStrategy === 'sequential'
              ? 'border-primary bg-primary/10'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          )}
        >
          <List className="h-5 w-5" />
          <span className="text-xs font-medium">Sequential</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Append in order
          </span>
        </button>

        <button
          onClick={() => setSelectedStrategy('intelligent')}
          className={cn(
            'p-3 rounded-lg border-2 transition-all',
            'flex flex-col items-center gap-2',
            selectedStrategy === 'intelligent'
              ? 'border-primary bg-primary/10'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          )}
        >
          <Zap className="h-5 w-5" />
          <span className="text-xs font-medium">Intelligent</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            AI-powered merge
          </span>
        </button>

        <button
          onClick={() => setSelectedStrategy('cherry-pick')}
          className={cn(
            'p-3 rounded-lg border-2 transition-all',
            'flex flex-col items-center gap-2',
            selectedStrategy === 'cherry-pick'
              ? 'border-primary bg-primary/10'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
          )}
        >
          <Cherry className="h-5 w-5" />
          <span className="text-xs font-medium">Cherry-pick</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Select messages
          </span>
        </button>
      </div>
    </div>
  );

  // Render branch selector
  const renderBranchSelector = () => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Select Branches to Merge ({selectedBranchCount} selected)
        </label>
        <button
          onClick={toggleAllBranches}
          className="text-xs text-primary hover:underline"
        >
          {branchSelections.every((sel) => sel.selected)
            ? 'Deselect All'
            : 'Select All'}
        </button>
      </div>

      <div className="max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
        {branchSelections.map((selection, index) => (
          <div
            key={selection.uuid}
            className={cn(
              'flex items-center gap-3 p-3',
              'border-b border-gray-100 dark:border-gray-800 last:border-0',
              'hover:bg-gray-50 dark:hover:bg-gray-800/50',
              'cursor-pointer',
              selection.selected && 'bg-primary/5'
            )}
            onClick={() => toggleBranchSelection(selection.uuid)}
          >
            <input
              type="checkbox"
              checked={selection.selected}
              onChange={() => {}}
              className="h-4 w-4 text-primary rounded"
            />
            <div className="flex-1">
              <div className="font-medium text-sm">Branch {index + 1}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {format(new Date(selection.message.timestamp), 'MMM d, h:mm a')}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 mt-1">
                {selection.message.content.substring(0, 100)}...
              </div>
            </div>
            {selectedStrategy === 'sequential' && selection.selected && (
              <input
                type="number"
                min="1"
                max={selectedBranchCount}
                placeholder="Order"
                className={cn(
                  'w-16 px-2 py-1 text-xs',
                  'border border-gray-300 dark:border-gray-600 rounded',
                  'bg-white dark:bg-gray-800'
                )}
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => {
                  const order = parseInt(e.target.value);
                  setBranchSelections((prev) =>
                    prev.map((sel) =>
                      sel.uuid === selection.uuid ? { ...sel, order } : sel
                    )
                  );
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );

  // Render merge preview
  const renderMergePreview = () => (
    <div className="space-y-2">
      <button
        onClick={() => setIsPreviewOpen(!isPreviewOpen)}
        className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        {isPreviewOpen ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        Merge Preview
        {mergePreview.length > 0 && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ({mergePreview.length} messages)
          </span>
        )}
      </button>

      {isPreviewOpen && (
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 max-h-48 overflow-y-auto">
          {isMerging ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                Generating preview...
              </span>
            </div>
          ) : mergePreview.length > 0 ? (
            <div className="space-y-2">
              {conflicts.length > 0 && (
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded p-2 mb-3">
                  <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-xs font-medium">
                      {conflicts.length} conflict
                      {conflicts.length !== 1 ? 's' : ''} detected
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                    {conflicts.map((conflict, i) => (
                      <div key={i}>
                        • {conflict.description} (resolved by{' '}
                        {conflict.resolution})
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Merged conversation flow:
              </div>
              {mergePreview.slice(0, 10).map((msg, index) => (
                <div key={index} className="flex items-start gap-2 text-xs">
                  <span className="text-gray-400 dark:text-gray-500 mt-0.5">
                    {index + 1}.
                  </span>
                  <div className="flex-1">
                    <span
                      className={cn(
                        'inline-block px-1.5 py-0.5 rounded text-xs',
                        msg.type === 'user'
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                          : msg.type === 'assistant'
                            ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                            : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                      )}
                    >
                      {msg.type}
                    </span>
                    <span className="ml-2 text-gray-600 dark:text-gray-400 line-clamp-1">
                      {msg.content.substring(0, 80)}...
                    </span>
                  </div>
                </div>
              ))}
              {mergePreview.length > 10 && (
                <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  ... and {mergePreview.length - 10} more messages
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
              Select branches and click "Generate Preview" to see merge result
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('max-w-2xl', className)}>
        <DialogHeader>
          <DialogTitle>
            <div className="flex items-center gap-2">
              <GitMerge className="h-5 w-5 text-primary" />
              Merge Conversation Branches
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Strategy selector */}
          {renderStrategySelector()}

          {/* Branch selector */}
          {renderBranchSelector()}

          {/* Cherry-pick message selector (if strategy is cherry-pick) */}
          {selectedStrategy === 'cherry-pick' && selectedBranchCount > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Select Messages to Cherry-pick
              </label>
              <div className="max-h-64 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
                {branchSelections
                  .filter((sel) => sel.selected)
                  .map((branch, branchIndex) => {
                    const branchMessages = [
                      branch.message,
                      ...getDescendantMessages(branch.uuid),
                    ];
                    const selection = cherryPickSelections.find(
                      (s) => s.branchUuid === branch.uuid
                    );

                    return (
                      <div
                        key={branch.uuid}
                        className="border-b border-gray-100 dark:border-gray-800 last:border-0"
                      >
                        <div className="px-3 py-2 bg-gray-50 dark:bg-gray-800/50 font-medium text-sm">
                          Branch {branchIndex + 1}
                          <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                            ({selection?.messageUuids.length || 0}/
                            {branchMessages.length} selected)
                          </span>
                        </div>
                        <div className="p-2 space-y-1">
                          {branchMessages.map((msg) => {
                            const msgUuid = msg.uuid || msg.messageUuid;
                            const isSelected =
                              selection?.messageUuids.includes(msgUuid);

                            return (
                              <div
                                key={msgUuid}
                                className={cn(
                                  'flex items-start gap-2 p-2 rounded cursor-pointer',
                                  'hover:bg-gray-50 dark:hover:bg-gray-800/50',
                                  isSelected && 'bg-primary/5'
                                )}
                                onClick={() =>
                                  toggleCherryPickMessage(branch.uuid, msgUuid)
                                }
                              >
                                <input
                                  type="checkbox"
                                  checked={isSelected || false}
                                  onChange={() => {}}
                                  className="h-4 w-4 mt-0.5 text-primary rounded"
                                />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span
                                      className={cn(
                                        'inline-block px-1.5 py-0.5 rounded text-xs',
                                        msg.type === 'user'
                                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                                          : msg.type === 'assistant'
                                            ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                                            : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                                      )}
                                    >
                                      {msg.type}
                                    </span>
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
                                      {format(
                                        new Date(msg.timestamp),
                                        'h:mm a'
                                      )}
                                    </span>
                                  </div>
                                  <div className="text-xs text-gray-600 dark:text-gray-300 line-clamp-2 mt-1">
                                    {msg.content}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Merge preview */}
          {renderMergePreview()}

          {/* Action buttons */}
          <div className="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => onOpenChange(false)}
              className={cn(
                'px-4 py-2 rounded-lg',
                'bg-gray-200 dark:bg-gray-700',
                'hover:bg-gray-300 dark:hover:bg-gray-600',
                'text-gray-700 dark:text-gray-300',
                'transition-colors'
              )}
            >
              Cancel
            </button>

            {mergePreview.length === 0 ? (
              <button
                onClick={generateMergePreview}
                disabled={selectedBranchCount < 2 || isMerging}
                className={cn(
                  'px-4 py-2 rounded-lg',
                  'bg-primary text-white',
                  'hover:bg-primary/90',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-colors',
                  'flex items-center gap-2'
                )}
              >
                {isMerging ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>Generate Preview</>
                )}
              </button>
            ) : (
              <button
                onClick={handleMerge}
                className={cn(
                  'px-4 py-2 rounded-lg',
                  'bg-primary text-white',
                  'hover:bg-primary/90',
                  'transition-colors',
                  'flex items-center gap-2'
                )}
              >
                <Check className="h-4 w-4" />
                Execute Merge
              </button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default BranchMergeDialog;
