import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket';
import {
  animateValue,
  formatStatValue,
  addPulseClass,
} from '@/utils/animations';
import { MessageSquare, Wrench, Coins, DollarSign } from 'lucide-react';

interface StatCardData {
  messages: number;
  tools: number;
  tokens: number;
  cost: number;
}

interface LiveStatCardsProps {
  sessionId?: string;
  projectId?: string;
  className?: string;
  enableWebSocket?: boolean;
}

interface StatUpdateEvent {
  type: 'stat_update';
  stat_type: 'messages' | 'tools' | 'tokens' | 'cost';
  session_id: string;
  update: {
    new_value: number;
    formatted_value: string;
    delta: number;
    animation: 'increment' | 'none';
  };
}

interface ConnectionStatusProps {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
}

function ConnectionStatus({
  isConnected,
  isConnecting,
  error,
}: ConnectionStatusProps) {
  let statusText = 'Offline';
  let dotClass = 'status-dot';

  if (error) {
    statusText = 'Error';
    dotClass = 'status-dot error';
  } else if (isConnecting) {
    statusText = 'Connecting';
    dotClass = 'status-dot connecting';
  } else if (isConnected) {
    statusText = 'Live';
    dotClass = 'status-dot active';
  }

  return (
    <div className="connection-status">
      <span className={dotClass}></span>
      <span className="text-xs">{statusText}</span>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  formattedValue: string;
  icon: React.ReactNode;
  type: 'messages' | 'tools' | 'tokens' | 'cost';
  isUpdating: boolean;
  className?: string;
}

function StatCard({
  title,
  formattedValue,
  icon,
  isUpdating,
  className = '',
}: StatCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const valueRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isUpdating && cardRef.current) {
      addPulseClass(cardRef.current, 'updating');
    }
  }, [isUpdating]);

  return (
    <div
      ref={cardRef}
      className={`live-stat-card bg-layer-primary border border-secondary-c rounded-lg p-4 text-center relative ${className}`}
    >
      <div className="flex items-center justify-center mb-2 text-muted-c">
        {icon}
      </div>
      <div
        ref={valueRef}
        className={`text-2xl font-semibold text-primary stat-value font-mono ${isUpdating ? 'updating' : ''}`}
      >
        {formattedValue}
      </div>
      <div className="text-xs text-muted-c stat-label">{title}</div>
    </div>
  );
}

export default function LiveStatCards({
  sessionId,
  className = '',
  enableWebSocket = true,
}: LiveStatCardsProps) {
  const [stats, setStats] = useState<StatCardData>({
    messages: 0,
    tools: 0,
    tokens: 0,
    cost: 0,
  });

  const [formattedStats, setFormattedStats] = useState({
    messages: '0',
    tools: '0',
    tokens: '0',
    cost: '$0.00',
  });

  const [updatingStats, setUpdatingStats] = useState({
    messages: false,
    tools: false,
    tokens: false,
    cost: false,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // WebSocket connection for real-time updates
  const wsUrl = enableWebSocket && sessionId ? `/ws/stats/${sessionId}` : null;

  const handleStatUpdate = useCallback(async (event: StatUpdateEvent) => {
    const { stat_type, update } = event;

    // Mark this stat as updating
    setUpdatingStats((prev) => ({ ...prev, [stat_type]: true }));

    // Update the raw value
    const newValue =
      stat_type === 'cost' ? update.new_value / 100 : update.new_value;

    setStats((prev) => {
      const oldValue = prev[stat_type];
      const updated = { ...prev, [stat_type]: newValue };

      // Animate the value change if there's a significant difference
      if (Math.abs(newValue - oldValue) > 0) {
        animateValue(oldValue, newValue, {
          duration: 300,
          onUpdate: (currentValue) => {
            const formatted = formatStatValue(currentValue, stat_type);
            setFormattedStats((prevFormatted) => ({
              ...prevFormatted,
              [stat_type]: formatted,
            }));
          },
        });
      } else {
        // If no animation needed, just update the formatted value
        setFormattedStats((prevFormatted) => ({
          ...prevFormatted,
          [stat_type]: update.formatted_value,
        }));
      }

      return updated;
    });

    // Clear the updating state after a delay
    setTimeout(() => {
      setUpdatingStats((prev) => ({ ...prev, [stat_type]: false }));
    }, 500);
  }, []);

  const {
    isConnected,
    isConnecting,
    error: wsError,
  } = useWebSocket(wsUrl, {
    onMessage: useCallback(
      (message: WebSocketMessage) => {
        if (message.type === 'stat_update') {
          handleStatUpdate(message as unknown as StatUpdateEvent);
        }
      },
      [handleStatUpdate]
    ),
    onConnect: useCallback(() => {
      console.log('WebSocket connected for live stats');
    }, []),
    onDisconnect: useCallback(() => {
      console.log('WebSocket disconnected for live stats');
    }, []),
    onError: useCallback((error: Event) => {
      console.error('WebSocket error:', error);
    }, []),
  });

  // Fetch initial stats
  const fetchInitialStats = useCallback(async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/ws/session/live?session_id=${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch live stats');
      }

      const data = await response.json();

      const newStats = {
        messages: data.message_count || 0,
        tools: data.tool_usage_count || 0,
        tokens: data.token_count || 0,
        cost: data.cost || 0,
      };

      setStats(newStats);
      setFormattedStats({
        messages: formatStatValue(newStats.messages, 'messages'),
        tools: formatStatValue(newStats.tools, 'tools'),
        tokens: formatStatValue(newStats.tokens, 'tokens'),
        cost: formatStatValue(newStats.cost, 'cost'),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
      console.error('Error fetching initial stats:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Fetch initial stats on mount and when sessionId changes
  useEffect(() => {
    fetchInitialStats();
  }, [fetchInitialStats]);

  // Loading state
  if (isLoading) {
    return (
      <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-4 ${className}`}>
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="bg-layer-primary border border-secondary-c rounded-lg p-4 text-center animate-pulse"
          >
            <div className="h-6 w-6 bg-layer-tertiary rounded mx-auto mb-2"></div>
            <div className="h-8 bg-layer-tertiary rounded mb-2"></div>
            <div className="h-4 bg-layer-tertiary rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  // Error state with fallback to regular display
  if (error) {
    console.warn('LiveStatCards error:', error);
    // Still show the stats even if there's an error
  }

  return (
    <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-4 ${className}`}>
      {/* Messages Stat Card */}
      <div className="relative">
        {enableWebSocket && (
          <ConnectionStatus
            isConnected={isConnected}
            isConnecting={isConnecting}
            error={wsError}
          />
        )}
        <StatCard
          title="Messages"
          value={stats.messages}
          formattedValue={formattedStats.messages}
          icon={<MessageSquare className="h-5 w-5" />}
          type="messages"
          isUpdating={updatingStats.messages}
        />
      </div>

      {/* Tools Stat Card */}
      <div className="relative">
        <StatCard
          title="Tools Used"
          value={stats.tools}
          formattedValue={formattedStats.tools}
          icon={<Wrench className="h-5 w-5" />}
          type="tools"
          isUpdating={updatingStats.tools}
        />
      </div>

      {/* Tokens Stat Card */}
      <div className="relative">
        <StatCard
          title="Tokens"
          value={stats.tokens}
          formattedValue={formattedStats.tokens}
          icon={<Coins className="h-5 w-5" />}
          type="tokens"
          isUpdating={updatingStats.tokens}
        />
      </div>

      {/* Cost Stat Card */}
      <div className="relative">
        <StatCard
          title="Cost"
          value={stats.cost}
          formattedValue={formattedStats.cost}
          icon={<DollarSign className="h-5 w-5" />}
          type="cost"
          isUpdating={updatingStats.cost}
        />
      </div>
    </div>
  );
}
