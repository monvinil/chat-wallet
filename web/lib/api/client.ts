/**
 * API Client
 * Core HTTP client for FastAPI backend with JWT token management
 */

import type {
  APIResponse,
  APIError,
  TokenPair,
  WalletCreateRequest,
  WalletCreateResponse,
  WalletLoginRequest,
  WalletLoginResponse,
  WalletImportRequest,
  WalletBalances,
  WalletAddress,
  TransactionPreviewRequest,
  TransactionPreviewResponse,
  TransactionSendRequest,
  TransactionSendResponse,
  TransactionHistory,
  YieldStatus,
  YieldDepositRequest,
  YieldWithdrawRequest,
  Schedule,
  ScheduleCreateRequest,
  EarningsSummary,
  EarningsHistory,
} from './types';

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Token storage keys
const ACCESS_TOKEN_KEY = 'usdchat_access_token';
const REFRESH_TOKEN_KEY = 'usdchat_refresh_token';

// ============================================================================
// Token Management
// ============================================================================

export const tokenManager = {
  getAccessToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setTokens: (accessToken: string, refreshToken: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  clearTokens: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  isAuthenticated: (): boolean => {
    return !!tokenManager.getAccessToken();
  },

  // Decode JWT to check expiration (without verification)
  isTokenExpired: (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() >= exp - 60000; // 1 minute buffer
    } catch {
      return true;
    }
  },
};

// ============================================================================
// HTTP Client
// ============================================================================

class APIClient {
  private baseUrl: string;
  private refreshPromise: Promise<boolean> | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async refreshTokens(): Promise<boolean> {
    const refreshToken = tokenManager.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/wallet/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        tokenManager.clearTokens();
        return false;
      }

      const data: TokenPair = await response.json();
      tokenManager.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      tokenManager.clearTokens();
      return false;
    }
  }

  private async getValidAccessToken(): Promise<string | null> {
    const accessToken = tokenManager.getAccessToken();

    if (!accessToken) return null;

    if (!tokenManager.isTokenExpired(accessToken)) {
      return accessToken;
    }

    // Token expired, try to refresh
    // Use single refresh promise to avoid race conditions
    if (!this.refreshPromise) {
      this.refreshPromise = this.refreshTokens().finally(() => {
        this.refreshPromise = null;
      });
    }

    const refreshed = await this.refreshPromise;
    return refreshed ? tokenManager.getAccessToken() : null;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requireAuth = false
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (requireAuth) {
      const token = await this.getValidAccessToken();
      if (!token) {
        throw new Error('Authentication required');
      }
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: APIError = await response.json().catch(() => ({
        detail: `HTTP error ${response.status}`,
      }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  // GET request
  async get<T>(endpoint: string, requireAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, requireAuth);
  }

  // POST request
  async post<T>(endpoint: string, data?: unknown, requireAuth = false): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      requireAuth
    );
  }

  // PATCH request
  async patch<T>(endpoint: string, data?: unknown, requireAuth = false): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      requireAuth
    );
  }

  // DELETE request
  async delete<T>(endpoint: string, requireAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, requireAuth);
  }
}

// Singleton instance
export const apiClient = new APIClient(API_BASE_URL);

// ============================================================================
// API Methods
// ============================================================================

export const api = {
  // ------------------
  // Auth / Wallet
  // ------------------

  wallet: {
    create: async (data: WalletCreateRequest): Promise<WalletCreateResponse> => {
      const response = await apiClient.post<WalletCreateResponse>(
        '/api/v1/wallet/create',
        data
      );
      tokenManager.setTokens(response.access_token, response.refresh_token);
      return response;
    },

    login: async (data: WalletLoginRequest): Promise<WalletLoginResponse> => {
      const response = await apiClient.post<WalletLoginResponse>(
        '/api/v1/wallet/login',
        data
      );
      tokenManager.setTokens(response.access_token, response.refresh_token);
      return response;
    },

    import: async (data: WalletImportRequest): Promise<WalletCreateResponse> => {
      const response = await apiClient.post<WalletCreateResponse>(
        '/api/v1/wallet/import',
        data
      );
      tokenManager.setTokens(response.access_token, response.refresh_token);
      return response;
    },

    logout: (): void => {
      tokenManager.clearTokens();
    },

    getBalances: async (): Promise<WalletBalances> => {
      const response = await apiClient.get<APIResponse<WalletBalances>>(
        '/api/v1/wallet/balance',
        true
      );
      return response.data;
    },

    getAddress: async (chain: string): Promise<WalletAddress> => {
      const response = await apiClient.get<APIResponse<WalletAddress>>(
        `/api/v1/wallet/address/${chain}`,
        true
      );
      return response.data;
    },
  },

  // ------------------
  // Transactions
  // ------------------

  transactions: {
    preview: async (data: TransactionPreviewRequest): Promise<TransactionPreviewResponse> => {
      const response = await apiClient.post<APIResponse<TransactionPreviewResponse>>(
        '/api/v1/transactions/preview',
        data,
        true
      );
      return response.data;
    },

    send: async (data: TransactionSendRequest): Promise<TransactionSendResponse> => {
      const response = await apiClient.post<APIResponse<TransactionSendResponse>>(
        '/api/v1/transactions/send',
        data,
        true
      );
      return response.data;
    },

    getHistory: async (page = 1, perPage = 20): Promise<TransactionHistory> => {
      const response = await apiClient.get<APIResponse<TransactionHistory>>(
        `/api/v1/transactions/history?page=${page}&per_page=${perPage}`,
        true
      );
      return response.data;
    },

    getStatus: async (hash: string): Promise<{ status: string; confirmations: number }> => {
      const response = await apiClient.get<APIResponse<{ status: string; confirmations: number }>>(
        `/api/v1/transactions/status/${hash}`,
        true
      );
      return response.data;
    },
  },

  // ------------------
  // Yield (Phase 1)
  // ------------------

  yield: {
    getStatus: async (): Promise<YieldStatus> => {
      const response = await apiClient.get<APIResponse<YieldStatus>>(
        '/api/v1/yield/status',
        true
      );
      return response.data;
    },

    deposit: async (data: YieldDepositRequest): Promise<{ success: boolean; tx_hash: string }> => {
      const response = await apiClient.post<APIResponse<{ success: boolean; tx_hash: string }>>(
        '/api/v1/yield/deposit',
        data,
        true
      );
      return response.data;
    },

    withdraw: async (data: YieldWithdrawRequest): Promise<{ success: boolean; tx_hash: string }> => {
      const response = await apiClient.post<APIResponse<{ success: boolean; tx_hash: string }>>(
        '/api/v1/yield/withdraw',
        data,
        true
      );
      return response.data;
    },
  },

  // ------------------
  // Scheduler/DCA (Phase 1)
  // ------------------

  scheduler: {
    create: async (data: ScheduleCreateRequest): Promise<Schedule> => {
      const response = await apiClient.post<APIResponse<Schedule>>(
        '/api/v1/scheduler/create',
        data,
        true
      );
      return response.data;
    },

    list: async (): Promise<Schedule[]> => {
      const response = await apiClient.get<APIResponse<{ schedules: Schedule[] }>>(
        '/api/v1/scheduler/list',
        true
      );
      return response.data.schedules;
    },

    cancel: async (id: string): Promise<{ success: boolean }> => {
      const response = await apiClient.post<APIResponse<{ success: boolean }>>(
        `/api/v1/scheduler/${id}/cancel`,
        undefined,
        true
      );
      return response.data;
    },

    pause: async (id: string): Promise<{ success: boolean }> => {
      const response = await apiClient.post<APIResponse<{ success: boolean }>>(
        `/api/v1/scheduler/${id}/pause`,
        undefined,
        true
      );
      return response.data;
    },

    resume: async (id: string): Promise<{ success: boolean }> => {
      const response = await apiClient.post<APIResponse<{ success: boolean }>>(
        `/api/v1/scheduler/${id}/resume`,
        undefined,
        true
      );
      return response.data;
    },
  },

  // ------------------
  // Earnings (Phase 1)
  // ------------------

  earnings: {
    getSummary: async (): Promise<EarningsSummary> => {
      const response = await apiClient.get<APIResponse<EarningsSummary>>(
        '/api/v1/earnings/summary',
        true
      );
      return response.data;
    },

    getHistory: async (
      period: 'daily' | 'weekly' | 'monthly' = 'daily',
      days = 30
    ): Promise<EarningsHistory> => {
      const response = await apiClient.get<APIResponse<EarningsHistory>>(
        `/api/v1/earnings/history?period=${period}&days=${days}`,
        true
      );
      return response.data;
    },
  },
};

export default api;
