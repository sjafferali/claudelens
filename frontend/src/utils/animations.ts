/**
 * Animation utilities for smooth number transitions and visual effects
 */

// Easing functions
export const easeOutQuad = (t: number): number => t * (2 - t);
export const easeInOutQuad = (t: number): number =>
  t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
export const easeOutCubic = (t: number): number => --t * t * t + 1;

export interface AnimationOptions {
  duration?: number;
  easing?: (t: number) => number;
  onUpdate?: (value: number) => void;
  onComplete?: () => void;
}

/**
 * Animates a number value from start to end over a duration
 */
export function animateValue(
  from: number,
  to: number,
  options: AnimationOptions = {}
): Promise<void> {
  const {
    duration = 300,
    easing = easeOutQuad,
    onUpdate,
    onComplete,
  } = options;

  return new Promise((resolve) => {
    const start = Date.now();
    const delta = to - from;

    const animate = () => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easing(progress);
      const current = Math.round(from + delta * easedProgress);

      onUpdate?.(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        onComplete?.();
        resolve();
      }
    };

    requestAnimationFrame(animate);
  });
}

/**
 * Triggers a pulse animation on an element
 */
export function pulseElement(element: HTMLElement, duration = 300): void {
  element.style.transition = `transform ${duration}ms ease, color ${duration}ms ease`;
  element.style.transform = 'scale(1.05)';

  // Add a subtle color change to indicate update
  const originalColor = element.style.color;
  element.style.color = 'var(--accent-hover, #3b82f6)';

  setTimeout(() => {
    element.style.transform = 'scale(1)';
    element.style.color = originalColor;

    // Clean up after animation
    setTimeout(() => {
      element.style.transition = '';
    }, duration);
  }, duration / 2);
}

/**
 * Triggers a pulse animation using CSS classes
 */
export function addPulseClass(
  element: HTMLElement,
  className = 'updating'
): void {
  element.classList.add(className);

  // Remove the class after animation duration
  setTimeout(() => {
    element.classList.remove(className);
  }, 300);
}

/**
 * Debounces rapid updates to prevent UI thrashing
 */
export function debounce<T extends (...args: unknown[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

/**
 * Throttles function calls to limit frequency
 */
export function throttle<T extends (...args: unknown[]) => void>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Formats numbers for display with appropriate suffixes
 */
export function formatStatValue(
  value: number,
  type: 'messages' | 'tools' | 'tokens' | 'cost'
): string {
  if (type === 'cost') {
    return `$${value.toFixed(2)}`;
  }

  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }

  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }

  return value.toString();
}

/**
 * Creates a staggered animation delay for multiple elements
 */
export function getStaggerDelay(index: number, baseDelay = 100): number {
  return index * baseDelay;
}

/**
 * Animates multiple stat cards with staggered timing
 */
export async function animateStatCards(
  updates: Array<{
    element: HTMLElement;
    from: number;
    to: number;
    type: 'messages' | 'tools' | 'tokens' | 'cost';
  }>
): Promise<void> {
  const animations = updates.map((update, index) => {
    return new Promise<void>((resolve) => {
      setTimeout(
        () => {
          addPulseClass(update.element);

          animateValue(update.from, update.to, {
            duration: 300,
            onUpdate: (value) => {
              const formatted = formatStatValue(value, update.type);
              const valueElement = update.element.querySelector('.stat-value');
              if (valueElement) {
                valueElement.textContent = formatted;
              }
            },
            onComplete: resolve,
          });
        },
        getStaggerDelay(index, 50)
      );
    });
  });

  await Promise.all(animations);
}
