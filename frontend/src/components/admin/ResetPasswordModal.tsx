import React, { useState } from 'react';
import { X, Key, AlertCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { adminApi } from '@/api/admin';
import { Button } from '@/components/common/Button';
import { User } from '@/api/types';

interface ResetPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
}

export const ResetPasswordModal: React.FC<ResetPasswordModalProps> = ({
  isOpen,
  onClose,
  user,
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const resetPasswordMutation = useMutation({
    mutationFn: ({ userId, password }: { userId: string; password: string }) =>
      adminApi.resetUserPassword(userId, password),
    onSuccess: (data) => {
      toast.success(data.message);
      onClose();
      setNewPassword('');
      setConfirmPassword('');
      setErrors([]);
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail || 'Failed to reset password';
      toast.error(message);
    },
  });

  const validatePassword = (): boolean => {
    const validationErrors: string[] = [];

    if (newPassword.length < 8) {
      validationErrors.push('Password must be at least 8 characters long');
    }

    if (!newPassword.match(/[0-9]/)) {
      validationErrors.push('Password must contain at least one number');
    }

    if (!newPassword.match(/[a-zA-Z]/)) {
      validationErrors.push('Password must contain at least one letter');
    }

    if (newPassword !== confirmPassword) {
      validationErrors.push('Passwords do not match');
    }

    setErrors(validationErrors);
    return validationErrors.length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) return;

    if (validatePassword()) {
      resetPasswordMutation.mutate({ userId: user.id, password: newPassword });
    }
  };

  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Overlay */}
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative z-50 w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-xl">
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold">Reset Password</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p className="text-sm">
                Resetting password for user: <strong>{user.username}</strong>
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Email: {user.email}
              </p>
            </div>

            {errors.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-800 dark:text-red-200">
                      Password requirements:
                    </p>
                    <ul className="mt-1 text-xs text-red-700 dark:text-red-300 list-disc list-inside">
                      {errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">
                New Password
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Enter new password"
                required
                minLength={8}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Confirm Password
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Confirm new password"
                required
                minLength={8}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="showPassword"
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="showPassword" className="text-sm">
                Show passwords
              </label>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={resetPasswordMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={
                  resetPasswordMutation.isPending || newPassword.length === 0
                }
              >
                {resetPasswordMutation.isPending
                  ? 'Resetting...'
                  : 'Reset Password'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
