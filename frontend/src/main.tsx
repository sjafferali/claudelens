import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './App';
import './styles/globals.css';

// Clear old localStorage format (temporary fix)
if (typeof window !== 'undefined') {
  const oldStorage = localStorage.getItem('claudelens-storage');
  if (oldStorage) {
    try {
      const parsed = JSON.parse(oldStorage);
      // Check if the old format has functions in ui object
      if (parsed?.state?.ui?.toggleTheme !== undefined) {
        localStorage.removeItem('claudelens-storage');
      }
    } catch (e) {
      // Ignore parse errors
    }
  }
}

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
);
