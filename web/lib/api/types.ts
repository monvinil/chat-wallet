/**
 * API Types
 * Type definitions for all API request/response payloads
 */

// ============================================================================
// Common Types
// ============================================================================

export interface APIResponse<T> {
  data: T;
  error?: string;
  message?: string;
}

export interface APIError {
  detail: string;
  status_code?: number;
}

// ============================================================================
// Auth Types
// ============================================================================

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  evm_address: string;
  solana_address?: string | null;
}

// ============================================================================
// Wallet Types
// ============================================================================

export interface WalletCreateRequest {
  email: string;
  password: string;
}

export interface WalletCreateResponse {
  user_id: string;
  evm_address: string;
  solana_address?: string | null;
  mnemonic: string;
  access_token: string;
  refresh_token: string;
  message?: string;
}

export interface WalletLoginRequest {
  email: string;
  password: string;
}

export interface WalletLoginResponse {
  user_id: string;
  email: string;
  evm_address: string;
  solana_address?: string | null;
  access_token: string;
  refresh_token: string;
  wallet_locked: boolean;
}

export interface WalletImportRequest {
  email: string;
  password: string;
  recovery_phrase: string;
}

export interface WalletBalance {
  chain: string;
  chain_name: string;
  usdc_balance: number;
  usdc_balance_formatted: string;
  native_balance: number;
  native_symbol: string;
}

export interface WalletBalances {
  total_usdc: number;
  total_usdc_formatted: string;
  evm_address: string;
  solana_address?: string | null;
  balances: WalletBalance[];
}

export interface WalletAddress {
  chain: string;
  chain_name: string;
  address: string;
  address_short: string;
  explorer_url?: string;
  usdc_contract?: string;
  qr_code?: string;
}

// ============================================================================
// Transaction Types
// ============================================================================

export interface TransactionPreviewRequest {
  to_address: string;
  amount: number;
  chain?: string;
  token?: string;
}

export interface TransactionPreviewResponse {
  from_address: string;
  to_address: string;
  amount: number;
  amount_formatted: string;
  chain: string;
  chain_name: string;
  token: string;
  estimated_gas: number;
  estimated_gas_usd: string;
  total_cost: number;
  total_cost_formatted: string;
  has_sufficient_balance: boolean;
  has_sufficient_gas: boolean;
}

export interface TransactionSendRequest {
  to_address: string;
  amount: number;
  chain?: string;
  token?: string;
  password: string;
}

export interface TransactionSendResponse {
  transaction_hash: string;
  explorer_url: string;
  status: 'pending' | 'confirmed' | 'failed';
  from_address: string;
  to_address: string;
  amount: number;
  amount_formatted: string;
  chain: string;
  token: string;
}

export interface Transaction {
  id: string;
  hash: string;
  from_address: string;
  to_address: string;
  amount: number;
  amount_formatted: string;
  chain: string;
  token: string;
  status: 'pending' | 'confirmed' | 'failed';
  timestamp: string;
  explorer_url?: string;
  type: 'send' | 'receive' | 'swap' | 'yield' | 'dca';
}

export interface TransactionHistory {
  transactions: Transaction[];
  total: number;
  page: number;
  per_page: number;
}

// ============================================================================
// Yield Types (Phase 1)
// ============================================================================

export interface YieldStatus {
  enabled: boolean;
  protocol: string;
  apy: number;
  deposited_amount: number;
  deposited_amount_formatted: string;
  earned_amount: number;
  earned_amount_formatted: string;
  projected_daily: number;
  projected_monthly: number;
  projected_yearly: number;
}

export interface YieldDepositRequest {
  amount: number;
  password: string;
}

export interface YieldWithdrawRequest {
  amount?: number; // undefined = withdraw all
  password: string;
}

// ============================================================================
// Scheduler/DCA Types (Phase 1)
// ============================================================================

export interface ScheduleCreateRequest {
  type: 'dca';
  amount: number;
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly';
  target_token: string; // 'ETH' | 'BTC' | 'WBTC'
  source_token?: string; // defaults to 'USDC'
  chain?: string;
}

export interface Schedule {
  id: string;
  type: 'dca';
  amount: number;
  amount_formatted: string;
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly';
  target_token: string;
  source_token: string;
  chain: string;
  next_execution: string;
  last_execution?: string;
  total_executed: number;
  total_invested: number;
  status: 'active' | 'paused' | 'cancelled';
  created_at: string;
}

// ============================================================================
// Earnings Types (Phase 1)
// ============================================================================

export interface EarningsSummary {
  today: number;
  today_formatted: string;
  this_week: number;
  this_week_formatted: string;
  this_month: number;
  this_month_formatted: string;
  all_time: number;
  all_time_formatted: string;
  breakdown: EarningsBreakdown[];
}

export interface EarningsBreakdown {
  source: 'yield' | 'dca_gains' | 'referral';
  amount: number;
  amount_formatted: string;
  percentage: number;
}

export interface EarningsHistoryItem {
  date: string;
  amount: number;
  source: 'yield' | 'dca_gains' | 'referral';
}

export interface EarningsHistory {
  items: EarningsHistoryItem[];
  period: 'daily' | 'weekly' | 'monthly';
}
