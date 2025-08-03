import { describe, it, expect, vi } from 'vitest';
import { render } from '@/test/utils';
import App from './App';

// Mock the analytics API to prevent network calls in tests
vi.mock('@/api/analytics', () => ({
  analyticsApi: {
    getSummary: vi.fn().mockResolvedValue({
      total_messages: 100,
      total_sessions: 25,
      total_projects: 5,
      total_cost: 12.5,
      messages_trend: 15.5,
      cost_trend: 8.2,
      most_active_project: 'Test Project',
      most_used_model: 'claude-3-opus',
      time_range: '30d',
      generated_at: new Date().toISOString(),
    }),
  },
  TimeRange: {
    LAST_24_HOURS: '24h',
    LAST_7_DAYS: '7d',
    LAST_30_DAYS: '30d',
    LAST_90_DAYS: '90d',
    LAST_YEAR: '1y',
    ALL_TIME: 'all',
  },
}));

describe('App', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });
});
