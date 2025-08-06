import { Message } from '@/api/types';

export interface MessageLinkOptions {
  branchIndex?: number;
  includeTimestamp?: boolean;
}

/**
 * Generate a shareable URL for a message
 */
export function generateMessageLink(
  message: Message,
  sessionId: string,
  options: MessageLinkOptions = {}
): string {
  const messageId = message.uuid || message.messageUuid || message._id;
  const baseUrl = window.location.origin;
  const url = new URL(`${baseUrl}/sessions/${sessionId}`);

  // Add messageId parameter
  url.searchParams.set('messageId', messageId);

  // Add branch information if available and specified
  if (options.branchIndex && message.branchCount && message.branchCount > 1) {
    url.searchParams.set('branchIndex', options.branchIndex.toString());
  }

  // Add timestamp for precise linking (optional)
  if (options.includeTimestamp && message.timestamp) {
    url.searchParams.set('t', message.timestamp);
  }

  return url.toString();
}

/**
 * Get a user-friendly link description for the message
 */
export function getMessageLinkDescription(message: Message): string {
  const messageType =
    message.type === 'user'
      ? 'User'
      : message.type === 'assistant'
        ? 'Assistant'
        : message.type === 'tool_use'
          ? 'Tool Use'
          : message.type === 'tool_result'
            ? 'Tool Result'
            : 'Message';

  // Get first few words of content for context
  const contentPreview = message.content
    .replace(/\n+/g, ' ')
    .trim()
    .substring(0, 50);

  const preview =
    contentPreview.length > 50
      ? contentPreview.substring(0, 47) + '...'
      : contentPreview;

  return preview ? `${messageType}: ${preview}` : messageType;
}

/**
 * Copy a message link to clipboard and return success status
 */
export async function copyMessageLink(
  message: Message,
  sessionId: string,
  options: MessageLinkOptions = {}
): Promise<boolean> {
  try {
    const link = generateMessageLink(message, sessionId, options);
    await navigator.clipboard.writeText(link);
    return true;
  } catch (error) {
    // Fallback for older browsers
    try {
      const link = generateMessageLink(message, sessionId, options);
      const textArea = document.createElement('textarea');
      textArea.value = link;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const result = document.execCommand('copy');
      document.body.removeChild(textArea);
      return result;
    } catch (fallbackError) {
      console.error('Failed to copy message link:', fallbackError);
      return false;
    }
  }
}

/**
 * Parse message link parameters from URL search params
 */
export function parseMessageLinkParams(searchParams: URLSearchParams) {
  return {
    messageId: searchParams.get('messageId'),
    branchIndex: searchParams.get('branchIndex')
      ? parseInt(searchParams.get('branchIndex')!, 10)
      : undefined,
    timestamp: searchParams.get('t'),
  };
}
