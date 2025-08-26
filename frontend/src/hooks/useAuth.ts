import { useState, useEffect, useCallback } from 'react';
import { useStore } from '@/store';
import { UserRole } from '@/api/types';

// Mock user data structure for now
// In a real implementation, this would come from an API call
interface CurrentUser {
  id: string;
  username: string;
  email: string;
  role: UserRole;
}

interface AuthHook {
  currentUser: CurrentUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  hasPermission: (requiredRole: UserRole) => boolean;
  login: (apiKey: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

// Role hierarchy for permission checking
const ROLE_HIERARCHY = {
  [UserRole.VIEWER]: 0,
  [UserRole.USER]: 1,
  [UserRole.ADMIN]: 2,
};

export const useAuth = (): AuthHook => {
  const { auth, setApiKey } = useStore();
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Mock function to get current user info from API key
  // In a real implementation, this would make an API call to validate the key and get user info
  const getCurrentUserFromApiKey = useCallback(
    async (apiKey: string): Promise<CurrentUser | null> => {
      try {
        // This is a mock implementation
        // In reality, you'd make an API call to validate the key and get user info
        if (apiKey === 'admin-key') {
          return {
            id: '1',
            username: 'admin',
            email: 'admin@example.com',
            role: UserRole.ADMIN,
          };
        } else if (apiKey === 'user-key') {
          return {
            id: '2',
            username: 'user',
            email: 'user@example.com',
            role: UserRole.USER,
          };
        } else if (apiKey === 'viewer-key') {
          return {
            id: '3',
            username: 'viewer',
            email: 'viewer@example.com',
            role: UserRole.VIEWER,
          };
        }

        // For real implementation, you might decode the API key or make an API call
        // For now, we'll assume any other key is a valid user
        if (apiKey && apiKey.length > 0) {
          return {
            id: 'default',
            username: 'user',
            email: 'user@example.com',
            role: UserRole.USER,
          };
        }

        return null;
      } catch (error) {
        console.error('Error validating API key:', error);
        return null;
      }
    },
    []
  );

  // Initialize authentication state
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);

      // Check for API key in environment or store
      const apiKey = import.meta.env.VITE_API_KEY || auth.apiKey;

      if (apiKey) {
        const user = await getCurrentUserFromApiKey(apiKey);
        setCurrentUser(user);
      }

      setIsLoading(false);
    };

    initAuth();
  }, [auth.apiKey, getCurrentUserFromApiKey]);

  const login = useCallback(
    async (apiKey: string): Promise<boolean> => {
      setIsLoading(true);

      try {
        const user = await getCurrentUserFromApiKey(apiKey);

        if (user) {
          setCurrentUser(user);
          setApiKey(apiKey);
          return true;
        }

        return false;
      } catch (error) {
        console.error('Login error:', error);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getCurrentUserFromApiKey, setApiKey]
  );

  const logout = useCallback(() => {
    setCurrentUser(null);
    setApiKey(null);
  }, [setApiKey]);

  const hasPermission = useCallback(
    (requiredRole: UserRole): boolean => {
      if (!currentUser) return false;

      const userLevel = ROLE_HIERARCHY[currentUser.role];
      const requiredLevel = ROLE_HIERARCHY[requiredRole];

      return userLevel >= requiredLevel;
    },
    [currentUser]
  );

  const isAuthenticated = !!currentUser;
  const isAdmin = currentUser?.role === UserRole.ADMIN;

  return {
    currentUser,
    isAuthenticated,
    isAdmin,
    hasPermission,
    login,
    logout,
    isLoading,
  };
};
