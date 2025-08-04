import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  calculateSessionCosts,
  calculateSessionCost,
  getMessagesCostsMap,
} from '@/services/costCalculation';
import type { Message } from '@/api/types';

/**
 * Hook to calculate and update message costs for a session
 */
export function useMessageCosts(
  sessionId: string | undefined,
  messages: Message[] | undefined
) {
  const [calculatingCosts, setCalculatingCosts] = useState(false);
  const [costMap, setCostMap] = useState<Map<string, number>>(new Map());
  const [hasCalculated, setHasCalculated] = useState(false);
  const queryClient = useQueryClient();

  // Create cost map from existing message costs
  useEffect(() => {
    if (messages && messages.length > 0) {
      const costs = getMessagesCostsMap(messages);
      setCostMap(costs);
    }
  }, [messages]);

  // Function to trigger cost calculation
  const calculateCosts = useCallback(async () => {
    if (!sessionId || calculatingCosts || hasCalculated) return;

    setCalculatingCosts(true);
    try {
      const result = await calculateSessionCosts(sessionId);

      if (result.success && result.calculated > 0) {
        // Invalidate queries to refresh data with new costs
        await queryClient.invalidateQueries({ queryKey: ['sessions'] });
        await queryClient.invalidateQueries({ queryKey: ['messages'] });
        await queryClient.invalidateQueries({ queryKey: ['analytics'] });
        setHasCalculated(true);
      }
    } catch (error) {
      console.error('Error calculating costs:', error);
    } finally {
      setCalculatingCosts(false);
    }
  }, [sessionId, calculatingCosts, hasCalculated, queryClient]);

  // Auto-calculate costs when session is loaded
  useEffect(() => {
    if (sessionId && messages && messages.length > 0 && !hasCalculated) {
      // Check if any messages are missing costs
      const needsCalculation = messages.some(
        (msg) =>
          msg.type === 'assistant' &&
          msg.model &&
          (!msg.cost_usd || msg.cost_usd === 0)
      );

      if (needsCalculation) {
        calculateCosts();
      }
    }
  }, [sessionId, messages, hasCalculated, calculateCosts]);

  return {
    calculatingCosts,
    costMap,
    calculateCosts,
  };
}

/**
 * Hook to calculate total session cost from messages
 */
export function useSessionCost(messages: Message[] | undefined) {
  const [totalCost, setTotalCost] = useState<number>(0);

  useEffect(() => {
    if (!messages || messages.length === 0) {
      setTotalCost(0);
      return;
    }

    // This is a synchronous calculation based on existing costs
    const cost = calculateSessionCost(messages);
    setTotalCost(cost);
  }, [messages]);

  return { totalCost, calculating: false };
}
