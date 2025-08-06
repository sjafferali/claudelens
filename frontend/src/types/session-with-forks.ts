import { Session } from '@/api/types';

export interface SessionWithForks extends Session {
  isFork?: boolean;
  forkedFrom?: {
    sessionId: string;
    messageId: string;
    description?: string;
  };
  forks?: Array<{
    sessionId: string;
    messageId: string;
    timestamp: string;
    description?: string;
  }>;
}
