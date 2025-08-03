import { Message } from '@/api/types';

// Type to handle messages that might have additional fields from the backend
interface MessageWithBackendFields {
  costUsd?: number;
  [key: string]: unknown;
}

// Helper function to get message UUID
export function getMessageUuid(message: Message): string | undefined {
  return message.uuid || message.messageUuid;
}

// Helper function to get message cost
export function getMessageCost(message: Message): number | undefined {
  // Check for cost_usd (frontend field), costUsd (backend field), or totalCost
  const messageWithBackend = message as Message & MessageWithBackendFields;
  return message.cost_usd || messageWithBackend.costUsd || message.totalCost;
}

// Helper function to get message usage
export function getMessageUsage(
  message: Message
): Message['usage'] | undefined {
  return message.usage;
}
