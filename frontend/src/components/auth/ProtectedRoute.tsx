import React from 'react';
import { Navigate } from 'react-router-dom';
import { useStore } from '@/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const apiKey = useStore((state) => state.auth.apiKey);

  // Check if we have an API key (either from store or environment)
  const hasAuth = apiKey || import.meta.env.VITE_API_KEY;

  if (!hasAuth) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
