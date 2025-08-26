// Test setup file for Vitest
import '@testing-library/jest-dom';
import { beforeAll, afterAll, vi } from 'vitest';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Suppress console warnings in tests
const originalWarn = console.warn;
beforeAll(() => {
  console.warn = (...args: unknown[]) => {
    // Suppress React Router future flag warnings in tests
    const firstArg = args[0];
    if (
      typeof firstArg === 'string' &&
      firstArg.includes('React Router Future Flag Warning')
    ) {
      return;
    }
    originalWarn(...args);
  };
});

afterAll(() => {
  console.warn = originalWarn;
});

// Mock useAuth hook globally to prevent network calls in tests
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    currentUser: null,
    isAuthenticated: false,
    isAdmin: false,
    hasPermission: () => false,
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
  }),
}));
