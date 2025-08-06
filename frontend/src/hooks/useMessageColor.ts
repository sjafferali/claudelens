import { useColorBlind } from '@/contexts/ColorBlindContext';

// Utility hook for getting color with fallback
export const useMessageColor = (messageType: string): string => {
  const { colors } = useColorBlind();

  switch (messageType) {
    case 'user':
      return colors.user;
    case 'assistant':
      return colors.assistant;
    case 'tool_use':
    case 'tool_result':
      return colors.tool;
    case 'system':
    case 'summary':
      return colors.system;
    default:
      return colors.system;
  }
};
