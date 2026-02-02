/**
 * Auth Store
 * Zustand store for authentication state management
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { api, tokenManager } from '@/lib/api';
import type { User, WalletLoginResponse, WalletCreateResponse } from '@/lib/api';

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  mnemonic: string | null; // Temporary storage for new wallet creation

  // Actions
  login: (email: string, password: string) => Promise<WalletLoginResponse>;
  signup: (email: string, password: string) => Promise<WalletCreateResponse>;
  importWallet: (email: string, password: string, recoveryPhrase: string) => Promise<WalletCreateResponse>;
  logout: () => void;
  clearError: () => void;
  clearMnemonic: () => void;
  setUser: (user: User) => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      mnemonic: null,

      // Login with email/password
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.wallet.login({ email, password });
          const user: User = {
            id: response.user_id,
            email: response.email,
            evm_address: response.evm_address,
            solana_address: response.solana_address,
          };
          set({ user, isAuthenticated: true, isLoading: false });
          return response;
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      // Create new wallet
      signup: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.wallet.create({ email, password });
          const user: User = {
            id: response.user_id,
            email,
            evm_address: response.evm_address,
            solana_address: response.solana_address,
          };
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            mnemonic: response.mnemonic, // Store temporarily for user to backup
          });
          return response;
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Signup failed';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      // Import existing wallet
      importWallet: async (email: string, password: string, recoveryPhrase: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.wallet.import({ email, password, recovery_phrase: recoveryPhrase });
          const user: User = {
            id: response.user_id,
            email,
            evm_address: response.evm_address,
            solana_address: response.solana_address,
          };
          set({ user, isAuthenticated: true, isLoading: false });
          return response;
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Import failed';
          set({ error: message, isLoading: false });
          throw err;
        }
      },

      // Logout
      logout: () => {
        api.wallet.logout();
        set({
          user: null,
          isAuthenticated: false,
          mnemonic: null,
          error: null,
        });
      },

      // Clear error
      clearError: () => set({ error: null }),

      // Clear mnemonic (after user has backed it up)
      clearMnemonic: () => set({ mnemonic: null }),

      // Set user (for hydration)
      setUser: (user: User) => set({ user, isAuthenticated: true }),

      // Check if authenticated (for hydration)
      checkAuth: () => {
        const isAuth = tokenManager.isAuthenticated();
        if (!isAuth && get().isAuthenticated) {
          // Token was cleared externally
          set({ user: null, isAuthenticated: false });
        }
        return isAuth;
      },
    }),
    {
      name: 'usdchat-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
