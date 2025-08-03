import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  calculateMessagesCosts,
  calculateSessionCost,
} from '@/services/costCalculation';
import { sessionsApi } from '@/api/sessions';
import type { Message } from '@/api/types';
import { getMessageUuid, getMessageCost } from '@/types/message-extensions';

/**
 * Hook to calculate and update message costs
 */
export function useMessageCosts(messages: Message[] | undefined) {
  const [calculatingCosts, setCalculatingCosts] = useState(false);
  const [costMap, setCostMap] = useState<Map<string, number>>(new Map());
  const queryClient = useQueryClient();

  const updateCostsMutation = useMutation({
    mutationFn: async (costs: Record<string, number>) => {
      return sessionsApi.batchUpdateMessageCosts(costs);
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['messages'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  useEffect(() => {
    if (!messages || messages.length === 0) return;

    const calculateCosts = async () => {
      setCalculatingCosts(true);
      try {
        // Calculate costs for all messages
        const costs = await calculateMessagesCosts(messages);
        setCostMap(costs);

        // Filter out messages that already have costs or failed to calculate
        const costUpdates: Record<string, number> = {};
        let hasUpdates = false;

        for (const [uuid, cost] of costs) {
          const message = messages.find((m) => {
            const messageId = getMessageUuid(m);
            return messageId === uuid;
          });
          const existingCost = message ? getMessageCost(message) : null;
          if (message && (!existingCost || existingCost === 0)) {
            costUpdates[uuid] = cost;
            hasUpdates = true;
          }
        }

        // Update costs in the backend if there are new calculations
        if (hasUpdates) {
          await updateCostsMutation.mutateAsync(costUpdates);
        }
      } catch (error) {
        console.error('Error calculating costs:', error);
      } finally {
        setCalculatingCosts(false);
      }
    };

    calculateCosts();
  }, [messages, updateCostsMutation]);

  return {
    calculatingCosts,
    costMap,
    updateCostsMutation,
  };
}

/**
 * Hook to calculate total session cost
 */
export function useSessionCost(messages: Message[] | undefined) {
  const [totalCost, setTotalCost] = useState<number>(0);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    if (!messages || messages.length === 0) {
      setTotalCost(0);
      return;
    }

    const calculate = async () => {
      setCalculating(true);
      try {
        const cost = await calculateSessionCost(messages);
        setTotalCost(cost);
      } catch (error) {
        console.error('Error calculating session cost:', error);
      } finally {
        setCalculating(false);
      }
    };

    calculate();
  }, [messages]);

  return { totalCost, calculating };
}
