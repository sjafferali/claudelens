import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  ArrowLeft,
  Search,
  Copy,
  ChevronDown,
  ChevronUp,
  Check,
  Wrench,
  GitBranch,
  PanelRightClose,
  PanelRightOpen,
  Map as MapIcon,
  Share2,
  Bug,
  BookmarkPlus,
} from 'lucide-react';
import { format } from 'date-fns';
import {
  useSession,
  useSessionMessages,
  useGenerateSessionSummary,
} from '@/hooks/useSessions';
import { useMessageCosts } from '@/hooks/useMessageCosts';
import { cn } from '@/utils/cn';
import { Message } from '@/api/types';
import {
  SessionStatCards,
  SessionCostCard,
} from '@/components/SessionStatCards';
import ToolUsageDetails from '@/components/ToolUsageDetails';
import ErrorDetailsPanel from '@/components/ErrorDetailsPanel';
import TokenDetailsPanel from '@/components/TokenDetailsPanel';
import CostDetailsPanel from '@/components/CostDetailsPanel';
import SessionTopics from '@/components/SessionTopics';
import { getMessageUuid, getMessageCost } from '@/types/message-extensions';
import { getSessionTitle } from '@/utils/session';
import { ToolDisplay } from '@/components/ToolDisplay';
import { ToolResultDisplay } from '@/components/ToolResultDisplay';
import { copyToClipboard } from '@/utils/clipboard';
import {
  calculateBranchCounts,
  getBranchAlternatives,
} from '@/utils/branch-detection';
import { BranchSelector } from '@/components/BranchSelector';
import { ConversationBreadcrumbs } from '@/components/ConversationBreadcrumbs';
import { useMessageNavigation } from '@/hooks/useMessageNavigation';
import ConversationTree from '@/components/ConversationTree';
import { SidechainPanel } from '@/components/SidechainPanel';
import { ConversationMiniMap } from '@/components/ConversationMiniMap';
import {
  copyMessageLink,
  getMessageLinkDescription,
} from '@/utils/message-linking';
import { MessageDebugModal } from '@/components/MessageDebugModal';
import toast from 'react-hot-toast';
import { PageSkeleton } from '@/components/common/LoadingSkeleton';
import Tooltip from '@/components/common/Tooltip';
import HelpPanel from '@/components/HelpPanel';
import { HelpCircle } from 'lucide-react';
import { highlightSearchMatches } from '@/utils/search-highlighting';
import {
  PromptEditor,
  PromptFormData,
} from '@/components/prompts/PromptEditor';

export default function SessionDetail() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const targetMessageId = searchParams.get('messageId');
  const selectedBranchId = searchParams.get('branch');
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const MESSAGES_PER_PAGE = 100;

  // Prompt editor state
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [promptInitialData, setPromptInitialData] = useState<
    Partial<PromptFormData> | undefined
  >(undefined);

  // Branch navigation state
  const [activeBranches, setActiveBranches] = useState<Map<string, string>>(
    new Map()
  );

  // Reset pagination when session changes
  useEffect(() => {
    setCurrentPage(0);
    setAllMessages([]);
    setHasLoadedInitial(false);
  }, [sessionId]);

  const { data: session, isLoading: sessionLoading } = useSession(sessionId!);
  const {
    data: messages,
    isLoading: messagesLoading,
    isFetching,
  } = useSessionMessages(
    sessionId!,
    currentPage * MESSAGES_PER_PAGE,
    MESSAGES_PER_PAGE
  );
  const generateSummary = useGenerateSessionSummary();

  // State to accumulate all loaded messages
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const [hasLoadedInitial, setHasLoadedInitial] = useState(false);

  // Update accumulated messages when new page loads
  useEffect(() => {
    if (messages?.messages && !messagesLoading) {
      if (currentPage === 0) {
        // First page - replace all messages
        setAllMessages(messages.messages);
        setHasLoadedInitial(true);
      } else {
        // Subsequent pages - append messages
        setAllMessages((prev) => [...prev, ...messages.messages]);
      }
    }
  }, [messages, currentPage, messagesLoading]);

  // Calculate if there are more messages to load
  const hasMoreMessages = session && allMessages.length < session.message_count;
  const canLoadMore = hasMoreMessages && !isFetching && hasLoadedInitial;

  // Handle loading more messages with scroll position preservation
  const handleLoadMore = () => {
    if (!scrollContainerRef.current) {
      setCurrentPage((prev) => prev + 1);
      return;
    }

    // Save current scroll position from bottom
    const container = scrollContainerRef.current;
    const scrollBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    // Set up observer to restore scroll position when content changes
    const observer = new MutationObserver(() => {
      if (scrollContainerRef.current) {
        const newScrollTop =
          scrollContainerRef.current.scrollHeight -
          scrollBottom -
          scrollContainerRef.current.clientHeight;
        scrollContainerRef.current.scrollTop = newScrollTop;
      }
      observer.disconnect();
    });

    // Start observing
    observer.observe(container, { childList: true, subtree: true });

    // Load more messages
    setCurrentPage((prev) => prev + 1);

    // Disconnect observer after timeout as fallback
    setTimeout(() => observer.disconnect(), 1000);
  };

  // Calculate costs for messages
  const { costMap } = useMessageCosts(sessionId, allMessages);

  const [viewMode, setViewMode] = useState<
    'timeline' | 'compact' | 'raw' | 'tree'
  >('timeline');

  // Clear scroll container ref when view mode changes
  useEffect(() => {
    scrollContainerRef.current = null;
  }, [viewMode]);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0);
  const [searchMatches, setSearchMatches] = useState<string[]>([]);
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set()
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [collapsedToolResults, setCollapsedToolResults] = useState<Set<string>>(
    new Set()
  );
  const [expandedToolPairs, setExpandedToolPairs] = useState<Set<string>>(
    new Set()
  );
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(
    null
  );
  const [isSidechainPanelOpen, setIsSidechainPanelOpen] = useState(false);
  const [isMiniMapOpen, setIsMiniMapOpen] = useState(false);
  const [debugMessage, setDebugMessage] = useState<Message | null>(null);
  const [isHelpPanelOpen, setIsHelpPanelOpen] = useState(false);

  // Calculate branch counts for all messages
  const messagesWithBranches = useMemo(
    () => calculateBranchCounts(allMessages),
    [allMessages]
  );

  // Calculate sidechain count for display
  const sidechainCount = useMemo(
    () => messagesWithBranches.filter((m) => m.isSidechain).length,
    [messagesWithBranches]
  );

  // Use message navigation hook
  const { getBreadcrumbPath, navigateToMessage } = useMessageNavigation(
    messagesWithBranches,
    messageRefs
  );

  // Get breadcrumb path for selected message
  const breadcrumbPath = useMemo(() => {
    if (!selectedMessageId) return [];
    const selectedMessage = messagesWithBranches.find(
      (m) =>
        m._id === selectedMessageId ||
        (m.uuid || m.messageUuid) === selectedMessageId
    );
    return selectedMessage ? getBreadcrumbPath(selectedMessage) : [];
  }, [selectedMessageId, messagesWithBranches, getBreadcrumbPath]);

  // Handle message selection
  const handleMessageSelect = useCallback(
    (messageId: string) => {
      setSelectedMessageId(messageId);
      navigateToMessage(messageId);
    },
    [navigateToMessage]
  );

  // Handle branch selection
  const handleSelectBranch = useCallback(
    (messageUuid: string, parent_uuid?: string) => {
      if (!parent_uuid) {
        // Find the parent UUID from the message
        const message = messagesWithBranches.find(
          (m) => (m.uuid || m.messageUuid) === messageUuid
        );
        if (message) {
          parent_uuid = message.parent_uuid;
        }
      }

      if (parent_uuid) {
        // Update active branches map
        setActiveBranches((prev) => {
          const newMap = new Map(prev);
          newMap.set(parent_uuid, messageUuid);
          return newMap;
        });

        // Update URL params
        const newParams = new URLSearchParams(searchParams);
        newParams.set('branch', messageUuid);
        setSearchParams(newParams, { replace: true });

        // Scroll to the selected branch message
        setTimeout(() => {
          const element = messageRefs.current[messageUuid];
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Add temporary highlight
            element.classList.add('ring-2', 'ring-amber-500', 'ring-offset-2');
            setTimeout(() => {
              element.classList.remove(
                'ring-2',
                'ring-amber-500',
                'ring-offset-2'
              );
            }, 1500);
          }
        }, 100);
      }
    },
    [messagesWithBranches, searchParams, setSearchParams]
  );

  // Get filtered messages based on active branches
  const filteredMessagesWithBranches = useMemo(() => {
    if (activeBranches.size === 0) {
      return messagesWithBranches;
    }

    // Build a set of messages to show based on active branches
    const messagesToShow = new Set<string>();

    // Process each message
    messagesWithBranches.forEach((message) => {
      const messageId = message.uuid || message.messageUuid;
      const parentId = message.parent_uuid;

      if (!messageId) return; // Skip messages without IDs

      // If this message has siblings (branches)
      if (message.branchCount && message.branchCount > 1 && parentId) {
        // Check if there's an active branch selection for this parent
        const selectedBranch = activeBranches.get(parentId);
        if (selectedBranch) {
          // Only show the selected branch
          if (messageId === selectedBranch) {
            messagesToShow.add(messageId);
          }
        } else {
          // No selection made, show the first branch (default)
          if (message.branchIndex === 1) {
            messagesToShow.add(messageId);
          }
        }
      } else {
        // Not a branched message, always show
        messagesToShow.add(messageId);
      }
    });

    return messagesWithBranches.filter((m) => {
      const id = m.uuid || m.messageUuid;
      return id && messagesToShow.has(id);
    });
  }, [messagesWithBranches, activeBranches]);

  // Filter messages based on search and track matches
  const filteredMessages = filteredMessagesWithBranches.filter((msg) => {
    // Handle null or undefined content
    const content = msg.content || '';
    return content.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // Track all messages that match the search
  useEffect(() => {
    if (searchQuery) {
      // Use filteredMessages which are the actual visible messages after search filtering
      const matches = filteredMessages.map(
        (msg) => msg.uuid || msg.messageUuid || msg._id
      );
      setSearchMatches(matches);
      setCurrentMatchIndex(0);
      // Navigate to first match
      if (matches.length > 0) {
        navigateToMessage(matches[0]);
      }
    } else {
      setSearchMatches([]);
      setCurrentMatchIndex(0);
    }
  }, [searchQuery, filteredMessages, navigateToMessage]);

  // Navigate to next/previous search match
  const navigateToNextMatch = useCallback(() => {
    if (searchMatches.length > 0) {
      const nextIndex = (currentMatchIndex + 1) % searchMatches.length;
      setCurrentMatchIndex(nextIndex);
      navigateToMessage(searchMatches[nextIndex]);
    }
  }, [currentMatchIndex, searchMatches, navigateToMessage]);

  const navigateToPreviousMatch = useCallback(() => {
    if (searchMatches.length > 0) {
      const prevIndex =
        currentMatchIndex === 0
          ? searchMatches.length - 1
          : currentMatchIndex - 1;
      setCurrentMatchIndex(prevIndex);
      navigateToMessage(searchMatches[prevIndex]);
    }
  }, [currentMatchIndex, searchMatches, navigateToMessage]);

  // Auto-collapse tool results on load
  useEffect(() => {
    if (allMessages.length > 0) {
      const toolResultIds = allMessages
        .filter((msg) => msg.content && msg.content.startsWith('[Tool Result:'))
        .map((msg) => msg._id);
      setCollapsedToolResults(new Set(toolResultIds));
    }
  }, [allMessages]);

  // Initialize active branches from URL params
  useEffect(() => {
    if (selectedBranchId && messagesWithBranches.length > 0) {
      const message = messagesWithBranches.find(
        (m) => (m.uuid || m.messageUuid) === selectedBranchId
      );
      if (message && message.parent_uuid) {
        setActiveBranches((prev) => {
          const newMap = new Map(prev);
          newMap.set(message.parent_uuid!, selectedBranchId);
          return newMap;
        });
      }
    }
  }, [selectedBranchId, messagesWithBranches]);

  // Keyboard shortcuts for branch navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Alt + Left/Right arrow for branch navigation
      if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        e.preventDefault();

        // Find the currently focused or visible message with branches
        const visibleMessages = filteredMessages.filter(
          (m) => m.branchCount && m.branchCount > 1
        );
        if (visibleMessages.length === 0) return;

        // For simplicity, navigate branches of the first visible branched message
        // In a more sophisticated implementation, you'd track the focused message
        const targetMessage = visibleMessages[0];
        if (!targetMessage.branches || !targetMessage.parent_uuid) return;

        const currentIndex = targetMessage.branchIndex || 1;
        const totalBranches = targetMessage.branchCount || 1;

        if (e.key === 'ArrowLeft' && currentIndex > 1) {
          // Navigate to previous branch
          const prevBranch = targetMessage.branches[currentIndex - 2];
          handleSelectBranch(prevBranch, targetMessage.parent_uuid);
        } else if (e.key === 'ArrowRight' && currentIndex < totalBranches) {
          // Navigate to next branch
          const nextBranch = targetMessage.branches[currentIndex];
          handleSelectBranch(nextBranch, targetMessage.parent_uuid);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredMessages, handleSelectBranch]);

  // Scroll to target message when navigating from search
  useEffect(() => {
    if (targetMessageId && messages && !messagesLoading) {
      // Give the DOM time to render
      setTimeout(() => {
        const targetElement = messageRefs.current[targetMessageId];
        if (targetElement) {
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // Highlight the message temporarily
          targetElement.classList.add(
            'ring-2',
            'ring-primary',
            'ring-offset-2'
          );
          setTimeout(() => {
            targetElement.classList.remove(
              'ring-2',
              'ring-primary',
              'ring-offset-2'
            );
          }, 2000);
        }
      }, 100);
    }
  }, [targetMessageId, messages, messagesLoading]);

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

  const toggleToolResult = (messageId: string) => {
    setCollapsedToolResults((prev) => {
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

  const handleCopyToClipboard = async (text: string, messageId: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleShareMessage = useCallback(
    async (message: Message) => {
      if (!sessionId) {
        toast.error('Session ID not available');
        return;
      }

      const success = await copyMessageLink(message, sessionId, {
        branchIndex: message.branchIndex,
      });

      if (success) {
        const description = getMessageLinkDescription(message);
        toast.success(`Message link copied! ${description}`, {
          duration: 3000,
          icon: '🔗',
        });
      } else {
        toast.error('Failed to copy message link');
      }
    },
    [sessionId]
  );

  const handleSaveToPromptLibrary = useCallback((message: Message) => {
    // Generate a suggested name from the first line or first 50 chars
    const content = message.content || '';
    const firstLine = content.split('\n')[0].trim();
    const suggestedName =
      firstLine.length > 50
        ? firstLine.substring(0, 50) + '...'
        : firstLine || 'New Prompt';

    // Prepare initial data for the prompt editor
    setPromptInitialData({
      name: suggestedName,
      content: message.content,
      description: `Saved from ${message.type === 'user' ? 'user message' : 'assistant response'} on ${format(new Date(message.timestamp), 'MMM d, yyyy')}`,
      tags: ['saved-from-session', message.type],
    });

    // Open the prompt editor
    setShowPromptEditor(true);
  }, []);

  const handlePromptEditorClose = useCallback(() => {
    setShowPromptEditor(false);
    setPromptInitialData(undefined);
  }, []);

  const handleOpenDebugModal = (message: Message) => {
    setDebugMessage(message);
  };

  const handleCloseDebugModal = () => {
    setDebugMessage(null);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Alt+Up/Down for search navigation
      if (e.altKey && e.key === 'ArrowUp') {
        e.preventDefault();
        navigateToPreviousMatch();
      } else if (e.altKey && e.key === 'ArrowDown') {
        e.preventDefault();
        navigateToNextMatch();
      }
      // Cmd/Ctrl+Shift+L to copy link to currently selected message
      else if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'L') {
        e.preventDefault();

        // Find the currently selected message or the first visible message
        let targetMessage: Message | null = null;

        if (selectedMessageId && filteredMessages) {
          targetMessage =
            filteredMessages.find(
              (m) => (m.uuid || m.messageUuid || m._id) === selectedMessageId
            ) || null;
        }

        // If no selected message, use the first message in view
        if (!targetMessage && filteredMessages && filteredMessages.length > 0) {
          targetMessage = filteredMessages[0];
        }

        if (targetMessage) {
          handleShareMessage(targetMessage);
        } else {
          toast.error('No message available to share');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    selectedMessageId,
    filteredMessages,
    sessionId,
    handleShareMessage,
    navigateToNextMatch,
    navigateToPreviousMatch,
  ]);

  const getMessageColors = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return {
          avatar: 'bg-gradient-to-br from-secondary to-purple-600',
          bg: 'bg-layer-secondary',
        };
      case 'assistant':
        return {
          avatar: 'bg-gradient-to-br from-primary to-primary-hover',
          bg: 'bg-layer-secondary',
        };
      case 'tool_use':
      case 'tool_result':
        return {
          avatar: 'bg-gradient-to-br from-primary to-primary-hover',
          bg: 'bg-layer-secondary',
        };
      default:
        return {
          avatar: 'bg-gradient-to-br from-gray-500 to-gray-600',
          bg: 'bg-layer-secondary',
        };
    }
  };

  const getMessageLabel = (type: Message['type'], content?: string) => {
    // Special handling for legacy tool result messages
    if (
      type === 'user' &&
      content &&
      content.trim().startsWith('--- Tool Result ---')
    ) {
      return 'System';
    }

    switch (type) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Claude';
      case 'tool_use':
        return 'Claude';
      case 'tool_result':
        return 'System';
      default:
        return type;
    }
  };

  const getAvatarText = (type: Message['type']) => {
    switch (type) {
      case 'user':
        return 'Y';
      case 'assistant':
      case 'tool_use':
      case 'tool_result':
        return 'C';
      default:
        return '?';
    }
  };

  if (sessionLoading || messagesLoading) {
    return <PageSkeleton title={true} filters={false} content="messages" />;
  }

  if (!session || !messages) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h2 className="text-2xl font-bold text-primary-c mb-2">
          Session Not Found
        </h2>
        <p className="text-muted-c mb-4">This session could not be found.</p>
        <button
          onClick={() => navigate('/sessions')}
          className="text-primary hover:text-primary-hover"
        >
          ← Back to sessions
        </button>
      </div>
    );
  }

  const duration = session.ended_at
    ? Math.floor(
        (new Date(session.ended_at).getTime() -
          new Date(session.started_at).getTime()) /
          1000
      )
    : 0;
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = duration % 60;

  return (
    <div className="flex flex-col h-screen bg-layer-primary overflow-hidden">
      {/* Header */}
      <div className="bg-layer-secondary border-b border-primary-c px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-muted-c text-sm mb-2">
              <button
                onClick={() => navigate('/sessions')}
                className="flex items-center gap-1 hover:text-primary-c transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to sessions
              </button>
            </div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-medium text-primary-c">
                {getSessionTitle(session)}
              </h2>
              {!session.summary && (
                <button
                  onClick={() => generateSummary.mutate(sessionId!)}
                  disabled={generateSummary.isPending}
                  className="text-xs px-2 py-1 bg-primary text-white rounded hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generateSummary.isPending
                    ? 'Generating...'
                    : 'Generate Title'}
                </button>
              )}
            </div>
            {session.summary && (
              <div className="mt-2">
                <p className="text-sm text-secondary-c max-w-4xl">
                  {session.summary}
                </p>
              </div>
            )}
            <div className="flex items-center gap-4 mt-1 text-sm text-muted-c">
              <span>
                {format(new Date(session.started_at), 'MMM d, yyyy')} at{' '}
                {format(new Date(session.started_at), 'h:mm a')}
              </span>
              <span>•</span>
              <span>{session.message_count} messages</span>
              <span>•</span>
              <span>
                {session.total_cost
                  ? `$${session.total_cost.toFixed(2)}`
                  : 'No cost data'}
              </span>
            </div>
          </div>
          <div className="flex items-center bg-layer-tertiary border border-primary-c rounded-lg px-3 py-2">
            <Search className="h-4 w-4 text-muted-c mr-2" />
            <input
              type="text"
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none outline-none text-primary-c placeholder-muted-c flex-1"
            />
            {searchQuery && searchMatches.length > 0 && (
              <div className="flex items-center gap-1 ml-2">
                <span className="text-xs text-muted-c">
                  {currentMatchIndex + 1}/{searchMatches.length}
                </span>
                <button
                  onClick={navigateToPreviousMatch}
                  className="p-1 hover:bg-layer-secondary rounded transition-colors"
                  title="Previous match (Alt+Up)"
                >
                  <ChevronUp className="h-4 w-4 text-muted-c" />
                </button>
                <button
                  onClick={navigateToNextMatch}
                  className="p-1 hover:bg-layer-secondary rounded transition-colors"
                  title="Next match (Alt+Down)"
                >
                  <ChevronDown className="h-4 w-4 text-muted-c" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden min-h-0">
        {/* Conversation Panel */}
        <div className="flex-1 flex flex-col bg-layer-primary overflow-hidden">
          <div className="bg-layer-secondary px-6 py-4 border-b border-primary-c flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h3 className="text-base font-medium text-primary-c">
                Conversation
              </h3>
              {filteredMessages.length > 0 && (
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Showing {filteredMessages.length} message
                  {filteredMessages.length !== 1 ? 's' : ''}
                  {allMessages.length !== filteredMessages.length && (
                    <span> of {allMessages.length} total</span>
                  )}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <Tooltip content="Show messages in chronological order">
                  <button
                    onClick={() => setViewMode('timeline')}
                    className={cn(
                      'px-3 py-1.5 text-sm rounded-md transition-all',
                      viewMode === 'timeline'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    Timeline
                  </button>
                </Tooltip>
                <Tooltip content="Condensed view with less spacing">
                  <button
                    onClick={() => setViewMode('compact')}
                    className={cn(
                      'px-3 py-1.5 text-sm rounded-md transition-all',
                      viewMode === 'compact'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    Compact
                  </button>
                </Tooltip>
                <Tooltip content="Plain text view without formatting">
                  <button
                    onClick={() => setViewMode('raw')}
                    className={cn(
                      'px-3 py-1.5 text-sm rounded-md transition-all',
                      viewMode === 'raw'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    Raw
                  </button>
                </Tooltip>
                <Tooltip content="Interactive tree visualization of conversation flow">
                  <button
                    onClick={() => setViewMode('tree')}
                    className={cn(
                      'px-3 py-1.5 text-sm rounded-md transition-all',
                      viewMode === 'tree'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    Tree
                  </button>
                </Tooltip>
              </div>

              {/* Mini-map toggle */}
              <div className="border-l border-secondary-c pl-4">
                <Tooltip
                  content={
                    isMiniMapOpen
                      ? 'Hide conversation overview map'
                      : 'Show conversation overview map for quick navigation'
                  }
                >
                  <button
                    onClick={() => setIsMiniMapOpen(!isMiniMapOpen)}
                    className={cn(
                      'flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-all',
                      isMiniMapOpen
                        ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    <MapIcon className="h-4 w-4" />
                    <span>Map</span>
                  </button>
                </Tooltip>
              </div>

              {/* Sidechain panel toggle */}
              <div className="border-l border-secondary-c pl-4">
                <Tooltip
                  content={
                    isSidechainPanelOpen
                      ? 'Hide tool operations and auxiliary messages'
                      : 'Show tool operations and auxiliary messages in a separate panel'
                  }
                >
                  <button
                    onClick={() =>
                      setIsSidechainPanelOpen(!isSidechainPanelOpen)
                    }
                    className={cn(
                      'flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-all',
                      isSidechainPanelOpen
                        ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/30'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    {isSidechainPanelOpen ? (
                      <PanelRightClose className="h-4 w-4" />
                    ) : (
                      <PanelRightOpen className="h-4 w-4" />
                    )}
                    <span>Sidechains</span>
                    {sidechainCount > 0 && (
                      <span className="ml-1 px-1.5 py-0.5 text-xs bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded-full">
                        {sidechainCount}
                      </span>
                    )}
                  </button>
                </Tooltip>
              </div>

              {/* Help button */}
              <div className="border-l border-secondary-c pl-4">
                <Tooltip content="Open help and documentation">
                  <button
                    onClick={() => setIsHelpPanelOpen(!isHelpPanelOpen)}
                    className={cn(
                      'flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-all',
                      isHelpPanelOpen
                        ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/30'
                        : 'bg-layer-tertiary text-tertiary-c hover:text-primary-c'
                    )}
                  >
                    <HelpCircle className="h-4 w-4" />
                    <span>Help</span>
                  </button>
                </Tooltip>
              </div>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Breadcrumb Navigation */}
            {selectedMessageId && breadcrumbPath.length > 0 && (
              <div className="px-6 py-3 border-b border-secondary-c bg-layer-secondary">
                <ConversationBreadcrumbs
                  path={breadcrumbPath}
                  onNavigate={handleMessageSelect}
                  currentMessageId={selectedMessageId}
                />
              </div>
            )}

            {viewMode === 'timeline' && (
              <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin"
              >
                <TimelineView
                  messages={filteredMessages}
                  expandedMessages={expandedMessages}
                  collapsedToolResults={collapsedToolResults}
                  expandedToolPairs={expandedToolPairs}
                  copiedId={copiedId}
                  costMap={costMap}
                  onToggleExpanded={toggleExpanded}
                  onToggleToolResult={toggleToolResult}
                  onToggleToolPairExpanded={toggleToolPairExpanded}
                  onCopy={handleCopyToClipboard}
                  onSelectBranch={handleSelectBranch}
                  onMessageSelect={handleMessageSelect}
                  onShareMessage={handleShareMessage}
                  onDebugMessage={handleOpenDebugModal}
                  onSaveToPromptLibrary={handleSaveToPromptLibrary}
                  selectedMessageId={selectedMessageId}
                  activeBranches={activeBranches}
                  allMessages={messagesWithBranches}
                  messageRefs={messageRefs}
                  getMessageColors={getMessageColors}
                  getMessageLabel={getMessageLabel}
                  getAvatarText={getAvatarText}
                  searchQuery={searchQuery}
                />
                {canLoadMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={handleLoadMore}
                      disabled={isFetching}
                      className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isFetching ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                          Loading...
                        </span>
                      ) : (
                        `Load More (${allMessages.length} of ${session.message_count})`
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
            {viewMode === 'compact' && (
              <div
                ref={scrollContainerRef}
                className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin"
              >
                <CompactView
                  messages={filteredMessages}
                  getMessageLabel={getMessageLabel}
                  getMessageColors={getMessageColors}
                />
                {canLoadMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={handleLoadMore}
                      disabled={isFetching}
                      className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isFetching ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                          Loading...
                        </span>
                      ) : (
                        `Load More (${allMessages.length} of ${session.message_count})`
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
            {viewMode === 'raw' && (
              <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
                <RawView
                  messages={filteredMessages}
                  onCopy={handleCopyToClipboard}
                  copiedId={copiedId}
                />
                {canLoadMore && (
                  <div className="flex justify-center py-6">
                    <button
                      onClick={handleLoadMore}
                      disabled={isFetching}
                      className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                      {isFetching ? (
                        <span className="flex items-center gap-2">
                          <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></span>
                          Loading...
                        </span>
                      ) : (
                        `Load More (${allMessages.length} of ${session.message_count})`
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
            {viewMode === 'tree' && (
              <div className="flex-1 overflow-hidden">
                <ConversationTree
                  messages={allMessages}
                  activeMessageId={selectedMessageId || undefined}
                  onMessageSelect={handleMessageSelect}
                  className="w-full h-full"
                />
              </div>
            )}
          </div>
        </div>

        {/* Sidechain Panel */}
        {isSidechainPanelOpen && (
          <SidechainPanel
            messages={messagesWithBranches}
            isOpen={isSidechainPanelOpen}
            onClose={() => setIsSidechainPanelOpen(false)}
            onNavigateToParent={(parent_uuid) => {
              // Navigate to the parent message
              const parentMessage = messagesWithBranches.find(
                (m) => (m.uuid || m.messageUuid) === parent_uuid
              );
              if (parentMessage) {
                handleMessageSelect(parentMessage._id);
              }
            }}
          />
        )}

        {/* Details Panel */}
        <div
          className={cn(
            'bg-layer-secondary border-l border-primary-c flex flex-col min-h-0',
            isSidechainPanelOpen ? 'w-64' : 'w-80'
          )}
        >
          <div className="flex-1 overflow-y-auto scrollbar-thin min-h-0">
            <div className="space-y-6">
              {/* Session Details */}
              <div className="px-6 pt-6">
                <h3 className="text-lg font-semibold text-primary-c mb-4 flex items-center gap-2">
                  <div className="w-1 h-5 bg-blue-500 rounded-full"></div>
                  Session Details
                </h3>
                <div className="space-y-3">
                  <div className="py-2 border-b border-secondary-c">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-muted-c">Session ID</span>
                      <button
                        onClick={() =>
                          handleCopyToClipboard(
                            session.session_id,
                            'session-id'
                          )
                        }
                        className="p-1 hover:bg-layer-tertiary rounded transition-colors"
                        title="Copy Session ID"
                      >
                        {copiedId === 'session-id' ? (
                          <Check className="h-3 w-3 text-green-500" />
                        ) : (
                          <Copy className="h-3 w-3 text-muted-c" />
                        )}
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-xs text-secondary-c font-mono truncate block w-full"
                        title={session.session_id}
                      >
                        {session.session_id}
                      </span>
                    </div>
                  </div>
                  {session.working_directory && (
                    <div className="py-2 border-b border-secondary-c">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-muted-c">Directory</span>
                        <button
                          onClick={() =>
                            handleCopyToClipboard(
                              session.working_directory!,
                              'working-directory'
                            )
                          }
                          className="p-1 hover:bg-layer-tertiary rounded transition-colors"
                          title="Copy Directory Path"
                        >
                          {copiedId === 'working-directory' ? (
                            <Check className="h-3 w-3 text-green-500" />
                          ) : (
                            <Copy className="h-3 w-3 text-muted-c" />
                          )}
                        </button>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className="text-xs text-secondary-c font-mono truncate block w-full"
                          title={session.working_directory}
                        >
                          {session.working_directory}
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="py-2 border-b border-secondary-c">
                    <div className="flex justify-between items-start">
                      <span className="text-sm text-muted-c">Started</span>
                      <span className="text-sm text-secondary-c text-right">
                        {format(new Date(session.started_at), 'M/d/yyyy')}
                        <br />
                        <span className="text-xs">
                          {format(new Date(session.started_at), 'h:mm:ss a')}
                        </span>
                      </span>
                    </div>
                  </div>
                  {session.ended_at && (
                    <div className="py-2 border-b border-secondary-c">
                      <div className="flex justify-between items-start">
                        <span className="text-sm text-muted-c">Ended</span>
                        <span className="text-sm text-secondary-c text-right">
                          {format(new Date(session.ended_at), 'M/d/yyyy')}
                          <br />
                          <span className="text-xs">
                            {format(new Date(session.ended_at), 'h:mm:ss a')}
                          </span>
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="py-2 border-b border-secondary-c">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-c">Duration</span>
                      <span className="text-sm text-secondary-c font-medium">
                        {hours}h {minutes}m {seconds}s
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Statistics */}
              <div className="px-6">
                <h3 className="text-lg font-semibold text-primary-c mb-4 flex items-center gap-2">
                  <div className="w-1 h-5 bg-green-500 rounded-full"></div>
                  Statistics
                </h3>
                <div className="bg-layer-tertiary rounded-lg p-4 space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <SessionStatCards session={session} />
                  </div>

                  {/* Additional Stats */}
                  <div className="pt-3 border-t border-secondary-c">
                    <SessionCostCard session={session} />
                  </div>
                </div>
              </div>

              {/* Tools Used */}
              <div className="px-6">
                <ToolUsageDetails sessionId={sessionId || undefined} />
              </div>

              {/* Token Usage Details */}
              <div className="px-6">
                <TokenDetailsPanel sessionId={sessionId || undefined} />
              </div>

              {/* Cost Details */}
              <div className="px-6">
                <CostDetailsPanel sessionId={sessionId || undefined} />
              </div>

              {/* Error Details */}
              <div className="px-6">
                <ErrorDetailsPanel sessionId={sessionId || undefined} />
              </div>

              {/* Topics */}
              <div className="px-6 pb-6">
                <SessionTopics sessionId={sessionId || ''} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Conversation MiniMap */}
      <ConversationMiniMap
        messages={messagesWithBranches}
        activeMessageId={selectedMessageId}
        onNavigate={handleMessageSelect}
        isOpen={isMiniMapOpen}
        onToggle={() => setIsMiniMapOpen(!isMiniMapOpen)}
        scrollContainerRef={scrollContainerRef}
      />

      {/* Debug Modal */}
      {debugMessage && (
        <MessageDebugModal
          message={debugMessage}
          isOpen={true}
          onClose={handleCloseDebugModal}
        />
      )}

      {/* Help Panel */}
      <HelpPanel
        isOpen={isHelpPanelOpen}
        onClose={() => setIsHelpPanelOpen(false)}
      />

      {/* Prompt Editor Modal */}
      <PromptEditor
        isOpen={showPromptEditor}
        onClose={handlePromptEditorClose}
        initialData={promptInitialData}
      />
    </div>
  );
}

// Timeline View Component
interface TimelineViewProps {
  messages: Message[];
  expandedMessages: Set<string>;
  collapsedToolResults: Set<string>;
  expandedToolPairs: Set<string>;
  copiedId: string | null;
  costMap?: Map<string, number>;
  onToggleExpanded: (messageId: string) => void;
  onToggleToolResult: (messageId: string) => void;
  onToggleToolPairExpanded: (pairId: string) => void;
  onCopy: (text: string, messageId: string) => void;
  onSelectBranch?: (messageUuid: string, parent_uuid?: string) => void;
  onMessageSelect?: (messageId: string) => void;
  onShareMessage?: (message: Message) => void;
  onDebugMessage?: (message: Message) => void;
  onSaveToPromptLibrary?: (message: Message) => void;
  selectedMessageId?: string | null;
  activeBranches?: Map<string, string>;
  allMessages?: Message[];
  getMessageColors: (type: Message['type']) => { avatar: string; bg: string };
  getMessageLabel: (type: Message['type'], content?: string) => string;
  getAvatarText: (type: Message['type']) => string;
  messageRefs: React.MutableRefObject<{ [key: string]: HTMLDivElement | null }>;
  searchQuery?: string;
}

function TimelineView({
  messages,
  expandedMessages,
  collapsedToolResults,
  expandedToolPairs,
  copiedId,
  costMap,
  onToggleExpanded,
  onToggleToolResult,
  onToggleToolPairExpanded,
  onCopy,
  onSelectBranch,
  onMessageSelect,
  onShareMessage,
  onDebugMessage,
  onSaveToPromptLibrary,
  selectedMessageId,
  activeBranches,
  allMessages,
  getMessageColors,
  getMessageLabel,
  getAvatarText,
  messageRefs,
  searchQuery = '',
}: TimelineViewProps) {
  // Format message content based on type and content
  const formatMessageContent = (message: Message) => {
    // Handle tool_result messages
    if (message.type === 'tool_result') {
      // Try to identify the tool type from content
      const content = (message.content || '').trim();

      // TodoWrite results
      if (content.startsWith('Todos have been modified successfully')) {
        return '✅ Todo list updated successfully';
      }

      // Read tool results (file contents)
      else if (
        content.includes('File contents:') ||
        content.includes('cat -n') ||
        /^\s*\d+→/.test(content)
      ) {
        const lines = content.split('\n');
        const preview = lines.slice(0, 5).join('\n');
        return `📄 File contents:\n${preview}${lines.length > 5 ? '\n...' : ''}`;
      }

      // Write/Edit tool results
      else if (
        content.includes('File created successfully') ||
        content.includes('has been updated') ||
        content.includes('File written successfully')
      ) {
        return `✅ File operation completed`;
      }

      // Grep/Glob search results
      else if (
        content.startsWith('Found') &&
        (content.includes('files') || content.includes('matches'))
      ) {
        const lines = content.split('\n');
        if (lines.length > 10) {
          return `🔍 Search results:\n${lines.slice(0, 10).join('\n')}\n... and ${lines.length - 10} more`;
        }
        return `🔍 Search results:\n${content}`;
      } else if (
        content === 'No matches found' ||
        content === 'No files found'
      ) {
        return '❌ No matches found';
      }

      // LS results
      else if (
        content.includes('total') &&
        (content.includes('drwx') || content.includes('-rw'))
      ) {
        const lines = content.split('\n');
        const fileCount = lines.filter(
          (l) => l.trim() && !l.startsWith('total')
        ).length;
        return `📁 Directory listing: ${fileCount} items`;
      }

      // Bash command results
      else if (
        content.includes('npm install') ||
        content.includes('poetry install')
      ) {
        return '📦 Dependencies installed successfully';
      } else if (
        content.includes('npm run') ||
        content.includes('poetry run')
      ) {
        return '🚀 Command executed successfully';
      } else if (
        content.includes('git') &&
        (content.includes('commit') || content.includes('branch'))
      ) {
        return '🔧 Git operation completed';
      } else if (
        content.includes('docker') &&
        (content.includes('built') || content.includes('Started'))
      ) {
        return '🐳 Docker operation completed';
      } else if (
        content.match(/^\s*\w+\s+\w+\s+\w+\s+\w+\s+\w+/) &&
        content.includes('ago')
      ) {
        // Docker ps output
        return '🐳 Container status retrieved';
      } else if (
        content.includes('pip install') ||
        content.includes('Successfully installed')
      ) {
        return '📦 Python packages installed';
      } else if (content.includes('chmod') || content.includes('permissions')) {
        return '🔐 Permissions updated';
      } else if (content.includes('mkdir') && content.includes('created')) {
        return '📁 Directory created';
      } else if (
        content.includes('curl') &&
        (content.includes('200') || content.includes('OK'))
      ) {
        return '🌐 HTTP request successful';
      }

      // Error handling
      else if (
        content.includes('Error') ||
        content.includes('error') ||
        content.includes('ERROR')
      ) {
        const firstLine = content.split('\n')[0];
        return `❌ Error: ${firstLine}`;
      } else if (
        content.includes('command not found') ||
        content.includes('No such file or directory')
      ) {
        const firstLine = content.split('\n')[0];
        return `⚠️ Warning: ${firstLine}`;
      }

      // Task results
      else if (
        content.includes('Task completed') ||
        content.includes('Agent task completed')
      ) {
        return '🤖 Task completed successfully';
      }

      // WebFetch/WebSearch results
      else if (content.includes('<!DOCTYPE') || content.includes('<html')) {
        return '🌐 Web content fetched successfully';
      } else if (
        content.includes('search results') ||
        content.includes('Search Results')
      ) {
        return '🔍 Web search completed';
      }

      // Notebook operations
      else if (content.includes('cells') && content.includes('notebook')) {
        return '📓 Notebook operation completed';
      }

      // Generic success patterns
      else if (
        content.includes('Successfully') ||
        content.includes('successfully') ||
        content.includes('Success')
      ) {
        const firstLine = content.split('\n')[0];
        return `✅ ${firstLine}`;
      }

      // Plan mode results
      else if (
        content.includes('Plan approved') ||
        content.includes('Exiting plan mode')
      ) {
        return '📋 Plan mode completed';
      }

      // Long results - show preview
      else if (content.length > 200) {
        const preview = content.substring(0, 200);
        const lineCount = content.split('\n').length;
        return `📥 Tool Result (${lineCount} lines):\n${preview}...`;
      }

      // Default
      else {
        return `📥 Tool Result:\n${content}`;
      }
    }

    // Handle tool_use messages with JSON content
    if (message.type === 'tool_use') {
      try {
        const parsed = JSON.parse(message.content);
        if (parsed.name) {
          // Format tool use more nicely
          let toolInfo = `🔧 Tool: ${parsed.name}`;

          // Add specific formatting for each tool type
          switch (parsed.name) {
            // File Operations
            case 'Read':
              if (parsed.input?.file_path) {
                toolInfo += `\n📄 Reading: ${parsed.input.file_path}`;
                if (parsed.input.offset || parsed.input.limit) {
                  toolInfo += ` (lines ${parsed.input.offset || 0}-${(parsed.input.offset || 0) + (parsed.input.limit || 'end')})`;
                }
              }
              break;

            case 'Write':
              if (parsed.input?.file_path) {
                toolInfo += `\n✏️ Writing to: ${parsed.input.file_path}`;
                if (parsed.input.content) {
                  const lines = parsed.input.content.split('\n').length;
                  toolInfo += ` (${lines} line${lines > 1 ? 's' : ''})`;
                }
              }
              break;

            case 'Edit':
              if (parsed.input?.file_path) {
                toolInfo += `\n✏️ Editing: ${parsed.input.file_path}`;
                if (parsed.input.replace_all) {
                  toolInfo += ' (replace all occurrences)';
                }
              }
              break;

            case 'MultiEdit':
              if (parsed.input?.file_path) {
                toolInfo += `\n✏️ Multiple edits to: ${parsed.input.file_path}`;
                if (parsed.input.edits && Array.isArray(parsed.input.edits)) {
                  toolInfo += ` (${parsed.input.edits.length} edit${parsed.input.edits.length > 1 ? 's' : ''})`;
                }
              }
              break;

            // Directory Operations
            case 'LS':
              if (parsed.input?.path) {
                toolInfo += `\n📁 Listing: ${parsed.input.path}`;
                if (parsed.input.ignore && parsed.input.ignore.length > 0) {
                  toolInfo += ` (ignoring ${parsed.input.ignore.length} pattern${parsed.input.ignore.length > 1 ? 's' : ''})`;
                }
              }
              break;

            case 'Glob':
              if (parsed.input?.pattern) {
                toolInfo += `\n🔍 Pattern: ${parsed.input.pattern}`;
                if (parsed.input.path) {
                  toolInfo += ` in ${parsed.input.path}`;
                }
              }
              break;

            // Search Operations
            case 'Grep':
              if (parsed.input?.pattern) {
                toolInfo += `\n🔍 Searching for: ${parsed.input.pattern}`;
                if (parsed.input.path) {
                  toolInfo += ` in ${parsed.input.path}`;
                }
                if (parsed.input.glob) {
                  toolInfo += ` (files matching ${parsed.input.glob})`;
                }
                if (parsed.input.type) {
                  toolInfo += ` (${parsed.input.type} files)`;
                }
              }
              break;

            // Command Execution
            case 'Bash':
              if (parsed.input?.command) {
                const cmd = parsed.input.command;
                toolInfo += `\n💻 Command: ${cmd.length > 60 ? cmd.substring(0, 60) + '...' : cmd}`;
                if (parsed.input.timeout) {
                  toolInfo += ` (timeout: ${parsed.input.timeout}ms)`;
                }
              }
              break;

            // Web Operations
            case 'WebSearch':
              if (parsed.input?.query) {
                toolInfo += `\n🌐 Searching web for: "${parsed.input.query}"`;
                if (
                  parsed.input.allowed_domains &&
                  parsed.input.allowed_domains.length > 0
                ) {
                  toolInfo += ` (only ${parsed.input.allowed_domains.join(', ')})`;
                }
              }
              break;

            case 'WebFetch':
              if (parsed.input?.url) {
                toolInfo += `\n🌐 Fetching: ${parsed.input.url}`;
                if (parsed.input.prompt) {
                  toolInfo += `\n💭 Purpose: ${parsed.input.prompt.substring(0, 50)}${parsed.input.prompt.length > 50 ? '...' : ''}`;
                }
              }
              break;

            // Notebook Operations
            case 'NotebookRead':
              if (parsed.input?.notebook_path) {
                toolInfo += `\n📓 Reading notebook: ${parsed.input.notebook_path}`;
                if (parsed.input.cell_id) {
                  toolInfo += ` (cell ${parsed.input.cell_id})`;
                }
              }
              break;

            case 'NotebookEdit':
              if (parsed.input?.notebook_path) {
                toolInfo += `\n📓 Editing notebook: ${parsed.input.notebook_path}`;
                if (parsed.input.edit_mode) {
                  toolInfo += ` (${parsed.input.edit_mode})`;
                }
                if (parsed.input.cell_type) {
                  toolInfo += ` - ${parsed.input.cell_type} cell`;
                }
              }
              break;

            // Task Management
            case 'TodoWrite':
              if (parsed.input?.todos) {
                const todos = parsed.input.todos;
                if (Array.isArray(todos) && todos.length > 0) {
                  const pending = todos.filter(
                    (t) => t.status === 'pending'
                  ).length;
                  const inProgress = todos.filter(
                    (t) => t.status === 'in_progress'
                  ).length;
                  const completed = todos.filter(
                    (t) => t.status === 'completed'
                  ).length;
                  toolInfo += `\n📝 Todo list: ${todos.length} item${todos.length > 1 ? 's' : ''}`;
                  toolInfo += `\n  ⏳ Pending: ${pending} | 🔄 In Progress: ${inProgress} | ✅ Completed: ${completed}`;

                  // Show actual todo items
                  toolInfo += '\n\n  Tasks:';
                  todos.forEach((todo, index) => {
                    const statusIcon =
                      todo.status === 'completed'
                        ? '✅'
                        : todo.status === 'in_progress'
                          ? '🔄'
                          : '⏳';
                    const priority =
                      todo.priority === 'high'
                        ? '🔴'
                        : todo.priority === 'medium'
                          ? '🟡'
                          : '🟢';

                    // Truncate long todo content
                    const content =
                      todo.content && todo.content.length > 60
                        ? todo.content.substring(0, 60) + '...'
                        : todo.content || 'No description';

                    toolInfo += `\n  ${index + 1}. ${statusIcon} ${priority} ${content}`;
                  });

                  // Limit display to first 10 todos if there are many
                  if (todos.length > 10) {
                    toolInfo += `\n  ... and ${todos.length - 10} more tasks`;
                  }
                }
              }
              break;

            case 'Task':
              if (parsed.input?.description) {
                toolInfo += `\n🤖 Agent task: ${parsed.input.description}`;
                if (parsed.input.subagent_type) {
                  toolInfo += ` (${parsed.input.subagent_type})`;
                }
              }
              break;

            case 'ExitPlanMode':
            case 'exit_plan_mode': // Handle lowercase variant
              toolInfo += '\n📋 Exiting plan mode';
              if (parsed.input?.plan) {
                const planLines = parsed.input.plan.split('\n').length;
                toolInfo += ` (${planLines} line plan)`;
              }
              break;

            default:
              // For any unknown tools, show basic info
              if (parsed.input) {
                const keys = Object.keys(parsed.input);
                if (keys.length > 0) {
                  toolInfo += `\n📦 Parameters: ${keys.join(', ')}`;
                }
              }
          }

          return toolInfo;
        }
      } catch {
        // If not JSON, return as is
      }
    }

    // Handle assistant messages with tool uses
    if (
      message.type === 'assistant' &&
      message.content &&
      (message.content.startsWith('Reading file:') ||
        message.content.startsWith('Writing to file:') ||
        message.content.startsWith('Editing file:') ||
        message.content.startsWith('Running command:') ||
        message.content.startsWith('Updating todo list') ||
        message.content.startsWith('Searching for:') ||
        message.content.startsWith('Using tool:'))
    ) {
      // These are already nicely formatted by the backend
      return `🔧 ${message.content}`;
    }

    // Only try to extract JSON content for specific cases where we know it's needed
    // For example, only for tool_use messages or messages that start with pure JSON
    if (
      message.type === 'tool_use' &&
      message.content &&
      message.content.trim().startsWith('{') &&
      message.content.includes('"type":')
    ) {
      try {
        const parsed = JSON.parse(message.content);
        if (parsed.content) {
          if (typeof parsed.content === 'string') {
            return parsed.content;
          } else if (Array.isArray(parsed.content)) {
            const textParts = parsed.content
              .filter((part: { type?: string }) => part.type === 'text')
              .map((part: { text?: string }) => part.text || '')
              .join('\n');
            return textParts || message.content;
          }
        }
      } catch {
        // If parsing fails, return original content
      }
    }

    return message.content;
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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {messageGroups.map((group) => {
        if (group.type === 'single') {
          const message = group.messages[0];
          const isExpanded = expandedMessages.has(message._id);
          const isToolResultCollapsed = collapsedToolResults.has(message._id);
          const colors = getMessageColors(message.type);
          const isActiveBranch =
            message.parent_uuid &&
            activeBranches?.get(message.parent_uuid) ===
              (message.uuid || message.messageUuid);
          const isAlternativeBranch =
            message.branchCount &&
            message.branchCount > 1 &&
            message.branchIndex !== 1 &&
            !isActiveBranch;

          return (
            <div
              key={message._id}
              className="group"
              ref={(el) => {
                const messageId =
                  message.uuid || message.messageUuid || message._id;
                messageRefs.current[messageId] = el;
              }}
            >
              <div
                onClick={() => {
                  if (onMessageSelect) {
                    const messageId =
                      message.uuid || message.messageUuid || message._id;
                    onMessageSelect(messageId);
                  }
                }}
                className={cn(
                  'rounded-xl p-4 cursor-pointer',
                  colors.bg,
                  'border transition-all',
                  selectedMessageId ===
                    (message.uuid || message.messageUuid || message._id)
                    ? 'border-blue-500 ring-2 ring-blue-500/20'
                    : isActiveBranch
                      ? 'border-amber-500 ring-2 ring-amber-500/20'
                      : 'border-secondary-c hover:border-primary-c',
                  isAlternativeBranch && 'opacity-60'
                )}
              >
                <div className="flex gap-4">
                  <div
                    className={cn(
                      'w-9 h-9 rounded-lg flex items-center justify-center text-white font-semibold flex-shrink-0',
                      colors.avatar
                    )}
                  >
                    {getAvatarText(message.type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-primary-c">
                          {getMessageLabel(message.type, message.content)}
                        </span>
                        {message.model && (
                          <span className="text-xs px-2 py-0.5 bg-layer-tertiary rounded-full text-muted-c">
                            {message.model}
                          </span>
                        )}
                        {message.branchCount &&
                          message.branchCount > 1 &&
                          onSelectBranch && (
                            <>
                              <BranchSelector
                                currentMessage={message}
                                branchMessages={
                                  allMessages &&
                                  (message.uuid || message.messageUuid)
                                    ? getBranchAlternatives(
                                        allMessages,
                                        message.uuid || message.messageUuid!
                                      )
                                    : []
                                }
                                onSelectBranch={(uuid) =>
                                  onSelectBranch(uuid, message.parent_uuid)
                                }
                              />
                            </>
                          )}
                        {/* Sidechain count badge */}
                        {(() => {
                          const messageUuid =
                            message.uuid || message.messageUuid;
                          const sidechainChildren =
                            allMessages?.filter(
                              (m) =>
                                m.parent_uuid === messageUuid && m.isSidechain
                            ) || [];
                          if (sidechainChildren.length > 0) {
                            return (
                              <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-purple-500/10 text-purple-600 dark:text-purple-400 rounded-full border border-purple-500/30">
                                <GitBranch className="h-3 w-3" />
                                {sidechainChildren.length} sidechain
                                {sidechainChildren.length !== 1 ? 's' : ''}
                              </span>
                            );
                          }
                          return null;
                        })()}
                      </div>
                      <div className="flex items-center gap-3">
                        {getMessageCost(message) ||
                        (costMap &&
                          costMap.get(getMessageUuid(message) || '')) ? (
                          <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                            $
                            {(
                              getMessageCost(message) ||
                              costMap?.get(getMessageUuid(message) || '') ||
                              0
                            ).toFixed(4)}
                          </span>
                        ) : null}
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                            #{messages.indexOf(message) + 1} of{' '}
                            {messages.length}
                          </span>
                          <span className="text-slate-300 dark:text-slate-600">
                            •
                          </span>
                          <span className="text-xs text-dim-c">
                            {format(
                              new Date(message.timestamp),
                              'MMM d, HH:mm:ss'
                            )}
                          </span>
                          {onShareMessage && (
                            <Tooltip content="Copy link to this message (Cmd/Ctrl+Shift+L)">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onShareMessage(message);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-200/50 dark:hover:bg-slate-700/50 transition-all duration-200"
                              >
                                <Share2 className="h-3 w-3 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" />
                              </button>
                            </Tooltip>
                          )}
                          {onDebugMessage && (
                            <Tooltip content="View complete JSON data for this message">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDebugMessage(message);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-200/50 dark:hover:bg-slate-700/50 transition-all duration-200"
                              >
                                <Bug className="h-3 w-3 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" />
                              </button>
                            </Tooltip>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Tool Result - Collapsible */}
                    {message.content &&
                    message.content.startsWith('[Tool Result:') &&
                    isToolResultCollapsed ? (
                      <div className="inline-flex items-center gap-2 bg-layer-tertiary px-3 py-1 rounded-md text-sm text-muted-c">
                        <span>Tool Result</span>
                        <button
                          onClick={() => onToggleToolResult(message._id)}
                          className="text-primary hover:text-primary-hover text-xs"
                        >
                          Show
                        </button>
                      </div>
                    ) : (
                      <div className="text-secondary-c whitespace-pre-wrap break-words">
                        {(() => {
                          const formattedContent =
                            formatMessageContent(message);
                          const contentLength = formattedContent.length;

                          if (contentLength > 500 && !isExpanded) {
                            return (
                              <>
                                {highlightSearchMatches(
                                  formattedContent.slice(0, 500),
                                  searchQuery
                                )}
                                ...
                                <button
                                  onClick={() => onToggleExpanded(message._id)}
                                  className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover"
                                >
                                  <ChevronDown className="h-4 w-4" />
                                  Show more
                                </button>
                              </>
                            );
                          } else {
                            return (
                              <>
                                {highlightSearchMatches(
                                  formattedContent,
                                  searchQuery
                                )}
                                {contentLength > 500 && (
                                  <button
                                    onClick={() =>
                                      onToggleExpanded(message._id)
                                    }
                                    className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover"
                                  >
                                    <ChevronUp className="h-4 w-4" />
                                    Show less
                                  </button>
                                )}
                                {message.content &&
                                  message.content.startsWith(
                                    '[Tool Result:'
                                  ) && (
                                    <button
                                      onClick={() =>
                                        onToggleToolResult(message._id)
                                      }
                                      className="mt-2 ml-4 text-sm text-primary hover:text-primary-hover"
                                    >
                                      Hide
                                    </button>
                                  )}
                              </>
                            );
                          }
                        })()}
                      </div>
                    )}

                    {/* Message Actions */}
                    <div className="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() =>
                          onCopy(formatMessageContent(message), message._id)
                        }
                        className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
                      >
                        {copiedId === message._id ? (
                          <>
                            <Check className="h-3 w-3" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            Copy
                          </>
                        )}
                      </button>
                      {message.type === 'user' && onSaveToPromptLibrary && (
                        <button
                          onClick={() => onSaveToPromptLibrary(message)}
                          className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
                          title="Save to prompt library"
                        >
                          <BookmarkPlus className="h-3 w-3" />
                          Save to Library
                        </button>
                      )}
                    </div>
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

          // Parse tool info
          let toolName = 'Unknown Tool';
          let toolInput = {};
          try {
            const parsed = JSON.parse(toolUseMessage.content);
            toolName = parsed.name || 'Unknown Tool';
            toolInput = parsed.input || {};
          } catch {
            // Fallback to showing raw content
          }

          return (
            <div key={pairId} className="group">
              <div className="rounded-xl p-4 bg-layer-secondary border border-secondary-c hover:border-primary-c transition-all relative overflow-hidden">
                {/* Header with expand/collapse button */}
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white shadow-sm flex-shrink-0">
                      <Wrench className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-primary-c">
                          Tool Operation
                        </span>
                        {toolUseMessage.model && (
                          <span className="text-xs px-2 py-0.5 bg-layer-tertiary rounded-full text-muted-c">
                            {toolUseMessage.model}
                          </span>
                        )}
                      </div>

                      {/* Collapsed state - show compact tool preview */}
                      {!isPairExpanded && (
                        <div className="space-y-2 overflow-hidden">
                          <ToolDisplay
                            toolName={toolName}
                            toolInput={toolInput}
                            isCollapsed={true}
                          />
                          <div className="mt-2">
                            <ToolResultDisplay
                              content={toolResultMessage.content}
                              toolName={toolName}
                              isCollapsed={true}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => onToggleToolPairExpanded(pairId)}
                    className={cn(
                      'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200',
                      isPairExpanded
                        ? 'text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
                        : 'text-primary-c bg-primary/10 hover:bg-primary/20 border border-primary'
                    )}
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
                  <div className="mt-4 space-y-4 border-t border-secondary-c pt-4">
                    {/* Tool use details */}
                    <div>
                      <h4 className="text-sm font-medium text-primary-c mb-2">
                        Tool Call
                      </h4>
                      <ToolDisplay
                        toolName={toolName}
                        toolInput={toolInput}
                        isCollapsed={false}
                      />
                    </div>

                    {/* Tool result */}
                    <div>
                      <h4 className="text-sm font-medium text-primary-c mb-2">
                        Result
                      </h4>
                      <ToolResultDisplay
                        content={toolResultMessage.content}
                        toolName={toolName}
                        isCollapsed={false}
                      />
                    </div>
                  </div>
                )}

                {/* Metadata footer */}
                <div className="flex items-center gap-4 mt-3 text-xs text-dim-c">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                      #{messageGroups.indexOf(group) + 1} of{' '}
                      {messageGroups.length}
                    </span>
                    <span className="text-slate-300 dark:text-slate-600">
                      •
                    </span>
                    <time dateTime={toolUseMessage.timestamp}>
                      {format(
                        new Date(toolUseMessage.timestamp),
                        'MMM d, HH:mm:ss'
                      )}
                    </time>
                    {onShareMessage && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onShareMessage(toolUseMessage);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-200/50 dark:hover:bg-slate-700/50 transition-all duration-200"
                        title="Copy link to this tool operation"
                      >
                        <Share2 className="h-3 w-3 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" />
                      </button>
                    )}
                    {onDebugMessage && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDebugMessage(toolUseMessage);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-200/50 dark:hover:bg-slate-700/50 transition-all duration-200"
                        title="View tool message debug information"
                      >
                        <Bug className="h-3 w-3 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200" />
                      </button>
                    )}
                  </div>
                  {(getMessageCost(toolUseMessage) ||
                    (costMap &&
                      costMap.get(getMessageUuid(toolUseMessage) || '')) ||
                    getMessageCost(toolResultMessage) ||
                    (costMap &&
                      costMap.get(
                        getMessageUuid(toolResultMessage) || ''
                      ))) && (
                    <span className="text-green-600 dark:text-green-400 font-medium">
                      $
                      {(
                        (getMessageCost(toolUseMessage) ||
                          costMap?.get(getMessageUuid(toolUseMessage) || '') ||
                          0) +
                        (getMessageCost(toolResultMessage) ||
                          costMap?.get(
                            getMessageUuid(toolResultMessage) || ''
                          ) ||
                          0)
                      ).toFixed(4)}
                    </span>
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

// Compact View Component
interface CompactViewProps {
  messages: Message[];
  getMessageLabel: (type: Message['type'], content?: string) => string;
  getMessageColors: (type: Message['type']) => { avatar: string; bg: string };
}

function CompactView({
  messages,
  getMessageLabel,
  getMessageColors,
}: CompactViewProps) {
  return (
    <div className="space-y-2 max-w-4xl mx-auto">
      {messages.map((message: Message) => {
        const colors = getMessageColors(message.type);
        const label = getMessageLabel(message.type, message.content);
        const isUser = message.type === 'user';

        return (
          <div
            key={message._id}
            className={cn(
              'bg-layer-secondary border border-secondary-c rounded-lg p-3 hover:border-primary-c transition-all',
              colors.bg
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className={cn(
                  'text-sm font-medium',
                  isUser ? 'text-secondary' : 'text-primary'
                )}
              >
                {label}
              </span>
              <span className="text-xs text-dim-c">
                {format(new Date(message.timestamp), 'MMM d, HH:mm:ss')}
              </span>
            </div>
            <div className="text-sm text-tertiary-c line-clamp-2">
              {message.content}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Raw View Component
interface RawViewProps {
  messages: Message[];
  onCopy: (text: string, messageId: string) => void;
  copiedId: string | null;
}

function RawView({ messages, onCopy, copiedId }: RawViewProps) {
  const [scrollRef, setScrollRef] = useState<HTMLDivElement | null>(null);

  const rawContent = messages
    .map((msg: Message) => {
      const model = msg.model ? ` (${msg.model})` : '';
      return `[${format(
        new Date(msg.timestamp),
        'yyyy-MM-dd HH:mm:ss'
      )}] ${msg.type}${model}: ${msg.content}`;
    })
    .join('\n\n');

  const scrollToEnd = () => {
    if (scrollRef) {
      scrollRef.scrollTop = scrollRef.scrollHeight;
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 overflow-hidden">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-medium text-primary-c">
          Raw Conversation Data
        </h4>
        <div className="flex gap-2">
          <button
            onClick={scrollToEnd}
            className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
          >
            <ChevronDown className="h-3 w-3" />
            Jump to End
          </button>
          <button
            onClick={() => onCopy(rawContent, 'raw-content')}
            className="px-3 py-1 bg-layer-tertiary border border-primary-c rounded-md text-xs text-muted-c hover:bg-border hover:text-primary-c transition-all flex items-center gap-1"
          >
            {copiedId === 'raw-content' ? (
              <>
                <Check className="h-3 w-3" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                Copy All
              </>
            )}
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden bg-layer-tertiary border border-secondary-c rounded-lg relative">
        <div
          ref={setScrollRef}
          className="h-full overflow-auto scrollbar-thin scroll-smooth"
        >
          <pre className="p-6 text-secondary-c font-mono text-sm whitespace-pre-wrap break-words min-w-0">
            {rawContent}
          </pre>
        </div>
      </div>
    </div>
  );
}
