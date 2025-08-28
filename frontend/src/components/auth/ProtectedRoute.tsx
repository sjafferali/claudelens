import React from 'react';
import { Navigate } from 'react-router-dom';
import { useStore } from '@/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { apiKey, accessToken } = useStore((state) => state.auth);

  // Check if we have authentication (JWT token for UI, API key for programmatic, or env variable)
  const hasAuth = accessToken || apiKey || import.meta.env.VITE_API_KEY;

  if (!hasAuth) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
