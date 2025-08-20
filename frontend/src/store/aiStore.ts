import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AISettings {
  enabled: boolean;
  model: string;
  api_key?: string;
  base_url?: string;
  max_tokens?: number;
  temperature?: number;
}

interface AIState {
  // Local UI state for AI features
  showGenerationModal: boolean;
  generationMode: 'metadata' | 'content';

  // Local settings cache (synced with server via hooks)
  localSettings: AISettings;

  // Actions
  setShowGenerationModal: (show: boolean) => void;
  setGenerationMode: (mode: 'metadata' | 'content') => void;
  updateLocalSettings: (settings: Partial<AISettings>) => void;
  resetLocalSettings: () => void;
}

const DEFAULT_SETTINGS: AISettings = {
  enabled: false,
  model: 'claude-3-sonnet-20240229',
  max_tokens: 4096,
  temperature: 0.7,
};

export const useAIStore = create<AIState>()(
  devtools(
    persist(
      (set) => ({
        // State
        showGenerationModal: false,
        generationMode: 'metadata',
        localSettings: DEFAULT_SETTINGS,

        // Actions
        setShowGenerationModal: (show) =>
          set(() => ({
            showGenerationModal: show,
          })),

        setGenerationMode: (mode) =>
          set(() => ({
            generationMode: mode,
          })),

        updateLocalSettings: (settings) =>
          set((state) => ({
            localSettings: { ...state.localSettings, ...settings },
          })),

        resetLocalSettings: () =>
          set(() => ({
            localSettings: DEFAULT_SETTINGS,
          })),
      }),
      {
        name: 'claudelens-ai-storage',
        partialize: (state) => ({
          generationMode: state.generationMode,
          localSettings: state.localSettings,
        }),
      }
    )
  )
);
