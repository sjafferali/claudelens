import type { Message } from '@/api/types';
import { getMessageCost, getMessageUuid } from '@/types/message-extensions';
import { apiClient } from '@/api/client';

/**
 * Calculate cost for messages using the backend API
 */
export async function calculateMessageCost(
  message: Message
): Promise<number | null> {
  // Only calculate costs for assistant messages
  if (message.type !== 'assistant' || !message.model) {
    return null;
  }

  // If message already has a cost, return it
  const existingCost = getMessageCost(message);
  if (existingCost && existingCost > 0) {
    return existingCost;
  }

  // For single message, we'll use the batch endpoint with session_id
  // This is more efficient as the backend can calculate all messages at once
  return null;
}

/**
 * Calculate costs for all messages in a session
 */
export async function calculateSessionCosts(
  sessionId: string
): Promise<{ success: boolean; calculated: number; updated: number }> {
  try {
    const response = await apiClient.post<{
      success: boolean;
      messages_processed: number;
      messages_skipped: number;
      costs_calculated: number;
      costs_updated: number;
    }>(`/messages/calculate-costs?session_id=${sessionId}`);

    return {
      success: response.success,
      calculated: response.costs_calculated,
      updated: response.costs_updated,
    };
  } catch (error) {
    console.error('Error calculating session costs:', error);
    return { success: false, calculated: 0, updated: 0 };
  }
}

/**
 * Calculate costs for specific messages
 */
export async function calculateMessagesCosts(
  messageIds: string[]
): Promise<{ success: boolean; calculated: number; updated: number }> {
  if (messageIds.length === 0) {
    return { success: true, calculated: 0, updated: 0 };
  }

  try {
    const response = await apiClient.post<{
      success: boolean;
      messages_processed: number;
      messages_skipped: number;
      costs_calculated: number;
      costs_updated: number;
    }>('/messages/calculate-costs', {
      message_ids: messageIds,
    });

    return {
      success: response.success,
      calculated: response.costs_calculated,
      updated: response.costs_updated,
    };
  } catch (error) {
    console.error('Error calculating message costs:', error);
    return { success: false, calculated: 0, updated: 0 };
  }
}

/**
 * Calculate total cost for a session from messages
 * This is a client-side calculation based on existing message costs
 */
export function calculateSessionCost(messages: Message[]): number {
  let totalCost = 0;

  for (const message of messages) {
    const cost = getMessageCost(message);
    if (cost !== null && cost !== undefined && cost > 0) {
      totalCost += cost;
    }
  }

  return totalCost;
}

/**
 * Get costs map from messages
 * This creates a map of message UUIDs to their costs for quick lookup
 */
export function getMessagesCostsMap(messages: Message[]): Map<string, number> {
  const costs = new Map<string, number>();

  messages.forEach((message) => {
    const cost = getMessageCost(message);
    const messageId = getMessageUuid(message);
    if (cost !== null && cost !== undefined && cost > 0 && messageId) {
      costs.set(messageId, cost);
    }
  });

  return costs;
}
