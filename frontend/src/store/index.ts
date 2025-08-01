import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  toggleTheme: () => void;
}

interface AuthState {
  apiKey: string | null;
  setApiKey: (key: string | null) => void;
}

interface AppState {
  ui: UIState;
  auth: AuthState;
}

export const useStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        ui: {
          sidebarOpen: true,
          theme: 'light',
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
        },
        auth: {
          apiKey: null,
          setApiKey: (key) =>
            set((state) => ({
              auth: { ...state.auth, apiKey: key },
            })),
        },
      }),
      {
        name: 'claudelens-storage',
      }
    )
  )
);