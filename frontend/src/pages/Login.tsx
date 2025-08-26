import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '@/store';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Lock, Shield } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/api/client';
import { getOIDCStatus, initiateOIDCLogin } from '@/api/oidcApi';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isOIDCEnabled, setIsOIDCEnabled] = useState(false);
  const [isOIDCLoading, setIsOIDCLoading] = useState(false);
  const navigate = useNavigate();
  const setAccessToken = useStore((state) => state.setAccessToken);

  useEffect(() => {
    // Check if OIDC is enabled
    const checkOIDCStatus = async () => {
      try {
        const status = await getOIDCStatus();
        setIsOIDCEnabled(status.enabled);
      } catch (error) {
        console.error('Failed to check OIDC status:', error);
      }
    };
    checkOIDCStatus();
  }, []);

  const handleSSOLogin = async () => {
    setIsOIDCLoading(true);
    try {
      const { authorization_url } = await initiateOIDCLogin();
      // Redirect to OIDC provider
      window.location.href = authorization_url;
    } catch (error) {
      toast.error('Failed to initiate SSO login');
      setIsOIDCLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username.trim() || !password.trim()) {
      toast.error('Please enter username and password');
      return;
    }

    setIsLoading(true);

    try {
      // Login with username/password
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

      // Store the access token
      setAccessToken(response.access_token);

      // Navigate to dashboard
      toast.success('Successfully logged in');
      navigate('/dashboard');
    } catch (error: unknown) {
      // Clear any stored token
      setAccessToken(null);

      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 401) {
          toast.error('Invalid username or password');
        } else {
          toast.error('Failed to authenticate. Please try again.');
        }
      } else {
        toast.error('Failed to authenticate. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Lock className="mx-auto h-12 w-12 text-primary" />
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
            Sign in to ClaudeLens
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Enter your username and password to access the dashboard
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Username or Email
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setUsername(e.target.value)
                }
                placeholder="Enter your username or email"
                className="mt-1"
                disabled={isLoading}
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setPassword(e.target.value)
                }
                placeholder="Enter your password"
                className="mt-1"
                disabled={isLoading}
              />
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Contact your administrator if you forgot your password
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <Button
              type="submit"
              variant="default"
              size="lg"
              className="w-full"
              disabled={isLoading || isOIDCLoading}
            >
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </Button>

            {isOIDCEnabled && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300 dark:border-gray-700" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400">
                      Or continue with
                    </span>
                  </div>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  className="w-full flex items-center justify-center gap-2"
                  onClick={handleSSOLogin}
                  disabled={isOIDCLoading || isLoading}
                >
                  <Shield className="w-5 h-5" />
                  {isOIDCLoading ? 'Redirecting...' : 'Login with SSO'}
                </Button>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
