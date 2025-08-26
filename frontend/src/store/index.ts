import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
}

interface AuthState {
  apiKey: string | null; // For programmatic API access
  accessToken: string | null; // JWT token for UI authentication
}

interface AppState {
  ui: UIState;
  auth: AuthState;
  toggleSidebar: () => void;
  toggleTheme: () => void;
  setApiKey: (key: string | null) => void;
  setAccessToken: (token: string | null) => void;
}

export const useStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // State
        ui: {
          sidebarOpen: true,
          theme: 'dark',
        },
        auth: {
          apiKey: null,
          accessToken: null,
        },
        // Actions
        toggleSidebar: () =>
          set((state) => ({
            ui: { ...state.ui, sidebarOpen: !state.ui.sidebarOpen },
          })),
        toggleTheme: () =>
          set((state) => ({
            ui: {
              ...state.ui,
              theme: state.ui.theme === 'light' ? 'dark' : 'light',
            },
          })),
        setApiKey: (key) =>
          set((state) => ({
            auth: { ...state.auth, apiKey: key },
          })),
        setAccessToken: (token) =>
          set((state) => ({
            auth: { ...state.auth, accessToken: token },
          })),
      }),
      {
        name: 'claudelens-storage',
        partialize: (state) => ({
          ui: state.ui,
          auth: state.auth,
        }),
      }
    )
  )
);
