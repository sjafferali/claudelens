import { PricingFetcher } from 'ccusage/pricing-fetcher';
import type { Message } from '@/api/types';
import {
  getMessageCost,
  getMessageUsage,
  getMessageUuid,
} from '@/types/message-extensions';

// Initialize the pricing fetcher
const pricingFetcher = new PricingFetcher();

/**
 * Calculate cost for a message based on its token usage
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

  // Check if we have token information
  const usage = getMessageUsage(message);
  if (!usage) {
    return null;
  }

  const {
    input_tokens,
    output_tokens,
    cache_creation_input_tokens,
    cache_read_input_tokens,
  } = usage;

  if (!input_tokens && !output_tokens) {
    return null;
  }

  try {
    // Map model names to ccusage format
    const modelName = mapModelName(message.model);

    // Calculate cost using ccusage - the library returns a Result type
    const costResult = await pricingFetcher.calculateCostFromTokens(
      {
        input_tokens: input_tokens || 0,
        output_tokens: output_tokens || 0,
        cache_creation_input_tokens: cache_creation_input_tokens || 0,
        cache_read_input_tokens: cache_read_input_tokens || 0,
      },
      modelName
    );

    // The ccusage library uses Result type - extract the value
    if (typeof costResult === 'object' && costResult !== null) {
      // Check if it's a Result type with unwrap method
      if ('unwrap' in costResult && typeof costResult.unwrap === 'function') {
        return costResult.unwrap();
      }
      // Check if it's a Result type with value property
      if ('value' in costResult) {
        return costResult.value as number;
      }
      // Check if it has success and data properties
      if (
        'success' in costResult &&
        'data' in costResult &&
        costResult.success
      ) {
        return costResult.data as number;
      }
    }

    // If it's already a number, return it
    if (typeof costResult === 'number') {
      return costResult;
    }

    return null;
  } catch (error) {
    console.error('Error calculating cost:', error);
    return null;
  }
}

/**
 * Map model names from the API to ccusage format
 */
function mapModelName(model: string): string {
  // Remove any provider prefix like "anthropic/"
  const cleanModel = model.replace(/^anthropic\//, '');

  // Map common model names to ccusage format
  const modelMap: Record<string, string> = {
    'claude-3-5-sonnet-20241022': 'claude-sonnet-3.5-20241022',
    'claude-3-5-haiku-20241022': 'claude-haiku-3.5-20241022',
    'claude-3-opus-20240229': 'claude-opus-3-20240229',
    'claude-3-sonnet-20240229': 'claude-sonnet-3-20240229',
    'claude-3-haiku-20240307': 'claude-haiku-3-20240307',
    // Claude 4 models
    'claude-4-sonnet-20250514': 'claude-sonnet-4-20250514',
    'claude-4-opus-20250514': 'claude-opus-4-20250514',
  };

  return modelMap[cleanModel] || cleanModel;
}

/**
 * Calculate total cost for a session
 */
export async function calculateSessionCost(
  messages: Message[]
): Promise<number> {
  let totalCost = 0;

  for (const message of messages) {
    const cost = await calculateMessageCost(message);
    if (cost !== null) {
      totalCost += cost;
    }
  }

  return totalCost;
}

/**
 * Batch calculate costs for multiple messages
 */
export async function calculateMessagesCosts(
  messages: Message[]
): Promise<Map<string, number>> {
  const costs = new Map<string, number>();

  await Promise.all(
    messages.map(async (message) => {
      const cost = await calculateMessageCost(message);
      const messageId = getMessageUuid(message);
      if (cost !== null && messageId) {
        costs.set(messageId, cost);
      }
    })
  );

  return costs;
}
