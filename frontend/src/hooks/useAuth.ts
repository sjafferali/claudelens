import { useState, useEffect, useCallback } from 'react';
import { useStore } from '@/store';
import { UserRole } from '@/api/types';
import { apiClient } from '@/api/client';

// Mock user data structure for now
// In a real implementation, this would come from an API call
interface CurrentUser {
  id: string;
  username: string;
  email: string;
  role: UserRole;
}

interface UserInfoResponse {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface AuthHook {
  currentUser: CurrentUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  hasPermission: (requiredRole: UserRole) => boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

// Role hierarchy for permission checking
const ROLE_HIERARCHY = {
  // REMOVED: [UserRole.VIEWER]: 0,
  [UserRole.USER]: 1,
  [UserRole.ADMIN]: 2,
};

export const useAuth = (): AuthHook => {
  const { auth, setApiKey, setAccessToken } = useStore();
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Get current user info from the API
  const getCurrentUser = useCallback(async (): Promise<CurrentUser | null> => {
    try {
      // Only try to fetch if we have authentication
      if (!auth.accessToken && !auth.apiKey && !import.meta.env.VITE_API_KEY) {
        return null;
      }

      const userInfo = await apiClient.get<UserInfoResponse>('/auth/me');
      return {
        id: userInfo.id,
        username: userInfo.username,
        email: userInfo.email,
        role: userInfo.role as UserRole,
      };
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }, [auth.accessToken, auth.apiKey]);

  // Initialize authentication state
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);

      // Check if we have any authentication
      const hasAuth =
        auth.accessToken || auth.apiKey || import.meta.env.VITE_API_KEY;

      if (hasAuth) {
        const user = await getCurrentUser();
        setCurrentUser(user);
      }

      setIsLoading(false);
    };

    initAuth();
  }, [auth.accessToken, auth.apiKey, getCurrentUser]);

  const login = useCallback(
    async (username: string, password: string): Promise<boolean> => {
      setIsLoading(true);

      try {
        // Login with username/password to get JWT token
        const response = await apiClient.post<LoginResponse>(
          '/auth/login',
          new URLSearchParams({
            username,
            password,
            grant_type: 'password',
          }),
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          }
        );

        if (response.access_token) {
          setAccessToken(response.access_token);

          // Now get the user info
          const user = await getCurrentUser();
          if (user) {
            setCurrentUser(user);
            return true;
          }
        }

        return false;
      } catch (error) {
        console.error('Login error:', error);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [getCurrentUser, setAccessToken]
  );

  const logout = useCallback(() => {
    setCurrentUser(null);
    setApiKey(null);
    setAccessToken(null);
  }, [setApiKey, setAccessToken]);

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
