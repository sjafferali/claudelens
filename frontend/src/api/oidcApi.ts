import { apiClient } from './client';

// OIDC Settings Types
export interface OIDCSettings {
  _id?: string;
  enabled: boolean;
  client_id: string;
  client_secret?: string;
  discovery_endpoint: string;
  redirect_uri: string;
  scopes: string[];
  auto_create_users: boolean;
  default_role: string;
  api_key_configured?: boolean;
  created_at?: string;
  updated_at?: string;
  updated_by?: string;
}

export interface OIDCTestConnectionRequest {
  discovery_endpoint?: string;
}

export interface OIDCTestConnectionResponse {
  success: boolean;
  message: string;
  issuer?: string;
  authorization_endpoint?: string;
  token_endpoint?: string;
  userinfo_endpoint?: string;
  jwks_uri?: string;
  error?: string;
}

export interface OIDCStatus {
  enabled: boolean;
  configured: boolean;
  provider?: string;
}

// Get OIDC settings
export async function getOIDCSettings(): Promise<OIDCSettings> {
  return apiClient.get<OIDCSettings>('/admin/oidc-settings');
}

// Update OIDC settings
export async function updateOIDCSettings(
  settings: Partial<OIDCSettings>
): Promise<OIDCSettings> {
  return apiClient.put<OIDCSettings>('/admin/oidc-settings', settings);
}

// Test OIDC connection
export async function testOIDCConnection(
  request: OIDCTestConnectionRequest = {}
): Promise<OIDCTestConnectionResponse> {
  return apiClient.post<OIDCTestConnectionResponse>(
    '/admin/oidc-settings/test',
    request
  );
}

// Delete OIDC settings
export async function deleteOIDCSettings(): Promise<void> {
  await apiClient.delete('/admin/oidc-settings');
}

// Get OIDC status
export async function getOIDCStatus(): Promise<OIDCStatus> {
  return apiClient.get<OIDCStatus>('/auth/oidc/status');
}

// Initiate OIDC login
export async function initiateOIDCLogin(): Promise<{
  authorization_url: string;
}> {
  return apiClient.get<{ authorization_url: string }>('/auth/oidc/login');
}

// Handle OIDC callback - exchange authorization code for token
export async function handleOIDCCallback(
  code: string,
  state: string
): Promise<{
  access_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    email: string;
    role: string;
    auth_method: string;
  };
}> {
  // Build the redirect URI that was used in the authorization request
  const redirectUri = `${window.location.origin}/auth/oidc/callback`;

  return apiClient.post<{
    access_token: string;
    token_type: string;
    user: {
      id: string;
      username: string;
      email: string;
      role: string;
      auth_method: string;
    };
  }>('/auth/oidc/callback', null, {
    params: { code, state, redirect_uri: redirectUri },
  });
}

// Logout from OIDC
export async function oidcLogout(): Promise<{ message: string }> {
  return apiClient.post<{ message: string }>('/auth/oidc/logout');
}
