import { format, formatDistanceToNow } from 'date-fns';

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'PPP');
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'PPP p');
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(amount);
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num);
}

export function formatTokenCount(count: number): string {
  /**
   * Format token count for display with smart formatting.
   * Examples: 45000 -> "45K", 1200000 -> "1.2M", 500 -> "500"
   */
  if (count >= 1_000_000) {
    return `${(count / 1_000_000).toFixed(1)}M`;
  }
  if (count >= 1_000) {
    return `${(count / 1_000).toFixed(0)}K`;
  }
  return count.toString();
}

export function formatCost(cost: number): string {
  /**
   * Format cost for display according to ClaudeLens requirements.
   * Examples: 0 -> "$0.00", 0.005 -> "<$0.01", 0.45 -> "$0.45", 12.30 -> "$12.30"
   */
  if (cost === 0) {
    return '$0.00';
  }
  if (cost < 0.01) {
    return '<$0.01';
  }
  if (cost < 1) {
    return `$${cost.toFixed(2)}`;
  }
  if (cost < 100) {
    return `$${cost.toFixed(2)}`;
  }
  return `$${cost.toFixed(0)}`;
}
