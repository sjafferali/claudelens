/**
 * Field mapping utilities for converting between snake_case and camelCase
 * Used to maintain backward compatibility while transitioning to snake_case
 */

/**
 * Map of camelCase to snake_case field names for Message type
 */
export const messageFieldMap: Record<string, string> = {
  sessionId: 'session_id',
  parentUuid: 'parent_uuid',
  costUsd: 'cost_usd',
  createdAt: 'created_at',
  messageUuid: 'uuid', // messageUuid is deprecated, use uuid
};

/**
 * Convert a message object from camelCase to snake_case
 */
export function toSnakeCase<T extends Record<string, any>>(obj: T): T {
  const result: any = {};

  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      const snakeKey = messageFieldMap[key] || key;
      result[snakeKey] = obj[key];
    }
  }

  return result;
}

/**
 * Convert a message object from snake_case to camelCase
 * This is primarily for backward compatibility
 */
export function toCamelCase<T extends Record<string, any>>(obj: T): T {
  const result: any = {};
  const reverseMap: Record<string, string> = {};

  // Create reverse mapping
  for (const [camel, snake] of Object.entries(messageFieldMap)) {
    reverseMap[snake] = camel;
  }

  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      const camelKey = reverseMap[key] || key;
      result[camelKey] = obj[key];
    }
  }

  return result;
}

/**
 * Get the snake_case field name for a given camelCase field
 */
export function getSnakeField(camelField: string): string {
  return messageFieldMap[camelField] || camelField;
}

/**
 * Get the camelCase field name for a given snake_case field
 */
export function getCamelField(snakeField: string): string {
  const reverseMap: Record<string, string> = {};
  for (const [camel, snake] of Object.entries(messageFieldMap)) {
    reverseMap[snake] = camel;
  }
  return reverseMap[snakeField] || snakeField;
}
