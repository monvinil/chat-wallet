"""
Balance Service - Internal ledger for financial integrity

This module provides the source of truth for user balances, replacing
direct blockchain queries for balance checks. It prevents double-spending,
tracks pending transactions, and provides an audit trail.

Usage:
    from balance_service import BalanceService

    # Get user's available balance
    balance = BalanceService.get_available_balance(user_id, "base-mainnet", "USDC")

    # Reserve balance for a send (atomic, prevents double-spend)
    success = BalanceService.reserve_for_send(user_id, chain, "USDC", amount, fee)

    # Confirm send after blockchain confirmation
    BalanceService.confirm_send(user_id, chain, "USDC", amount, fee, tx_hash)

    # Or release if transaction failed
    BalanceService.release_reserved(user_id, chain, "USDC", amount, fee)
"""

import uuid
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

from utils.logger import logger


class BalanceService:
    """
    Internal balance ledger service.

    Provides atomic balance operations with double-spend protection.
    All balance modifications go through this service, not direct DB updates.
    """

    @staticmethod
    def _get_client():
        """Get Supabase client with service key (for atomic operations)"""
        from supabase_client import get_supabase_client
        return get_supabase_client(use_service_key=True)

    # =========================================================================
    # BALANCE QUERIES
    # =========================================================================

    @staticmethod
    def get_balance(user_id: str, chain: str, token: str = "USDC") -> Optional[Dict[str, Decimal]]:
        """
        Get full balance breakdown for a user/chain/token.

        Returns:
            {
                "available": Decimal,  # Spendable now
                "pending_in": Decimal, # Incoming (unconfirmed)
                "pending_out": Decimal, # Outgoing (unconfirmed)
                "locked": Decimal,     # In yield/scheduled
                "total": Decimal       # Sum of all
            }
            or None if not found
        """
        client = BalanceService._get_client()
        if not client:
            return None

        try:
            result = client.table("balances").select(
                "available_balance, pending_in, pending_out, locked_balance"
            ).eq("user_id", user_id).eq("chain", chain).eq("token", token).execute()

            if not result.data:
                # No balance record = zero balance
                return {
                    "available": Decimal("0"),
                    "pending_in": Decimal("0"),
                    "pending_out": Decimal("0"),
                    "locked": Decimal("0"),
                    "total": Decimal("0")
                }

            row = result.data[0]
            available = Decimal(str(row["available_balance"]))
            pending_in = Decimal(str(row["pending_in"]))
            pending_out = Decimal(str(row["pending_out"]))
            locked = Decimal(str(row["locked_balance"]))

            return {
                "available": available,
                "pending_in": pending_in,
                "pending_out": pending_out,
                "locked": locked,
                "total": available + pending_in + locked  # pending_out is already subtracted from available
            }

        except Exception as e:
            logger.error(f"BalanceService.get_balance error: {e}")
            return None

    @staticmethod
    def get_available_balance(user_id: str, chain: str, token: str = "USDC") -> Decimal:
        """
        Get spendable balance for a user/chain/token.
        Returns 0 if not found or error.
        """
        balance = BalanceService.get_balance(user_id, chain, token)
        if balance:
            return balance["available"]
        return Decimal("0")

    @staticmethod
    def get_all_balances(user_id: str) -> List[Dict[str, Any]]:
        """
        Get all balances for a user across all chains/tokens.

        Returns list of balance records with chain/token info.
        """
        client = BalanceService._get_client()
        if not client:
            return []

        try:
            result = client.table("balances").select("*").eq("user_id", user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"BalanceService.get_all_balances error: {e}")
            return []

    # =========================================================================
    # SEND OPERATIONS (with double-spend protection)
    # =========================================================================

    @staticmethod
    def reserve_for_send(
        user_id: str,
        chain: str,
        token: str,
        amount: Decimal,
        fee: Decimal = Decimal("0"),
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Atomically reserve balance for a send operation.

        This is the first step in a send flow:
        1. reserve_for_send() - locks funds
        2. Execute blockchain transaction
        3. confirm_send() on success OR release_reserved() on failure

        Args:
            user_id: User ID
            chain: Chain identifier (e.g., "base-mainnet")
            token: Token symbol (e.g., "USDC")
            amount: Amount to send
            fee: Transaction fee
            idempotency_key: Optional key to prevent duplicate operations

        Returns:
            (success: bool, ledger_entry_id: Optional[str])
        """
        client = BalanceService._get_client()
        if not client:
            return False, "Database unavailable"

        try:
            # Check idempotency first
            if idempotency_key:
                existing = client.table("ledger_entries").select("id").eq(
                    "user_id", user_id
                ).eq("idempotency_key", idempotency_key).execute()

                if existing.data:
                    logger.warning(f"Duplicate idempotency key: {idempotency_key}")
                    return False, "Duplicate request"

            # Call atomic reserve function
            result = client.rpc("reserve_balance", {
                "p_user_id": user_id,
                "p_chain": chain,
                "p_token": token,
                "p_amount": float(amount),
                "p_fee": float(fee)
            }).execute()

            if not result.data:
                return False, "Insufficient balance"

            # Create ledger entry
            total = amount + fee
            balance = BalanceService.get_balance(user_id, chain, token)
            balance_after = balance["available"] if balance else Decimal("0")

            entry_data = {
                "user_id": user_id,
                "entry_type": "send",
                "chain": chain,
                "token": token,
                "amount": -float(amount),  # Negative for debit
                "fee_amount": float(fee),
                "balance_before": float(balance_after + total),
                "balance_after": float(balance_after),
                "status": "pending"
            }

            if idempotency_key:
                entry_data["idempotency_key"] = idempotency_key

            entry_result = client.table("ledger_entries").insert(entry_data).execute()

            if entry_result.data:
                return True, entry_result.data[0]["id"]

            return True, None

        except Exception as e:
            logger.error(f"BalanceService.reserve_for_send error: {e}")
            return False, str(e)

    @staticmethod
    def confirm_send(
        user_id: str,
        chain: str,
        token: str,
        amount: Decimal,
        fee: Decimal = Decimal("0"),
        tx_hash: Optional[str] = None,
        ledger_entry_id: Optional[str] = None,
        counterparty_address: Optional[str] = None
    ) -> bool:
        """
        Confirm a send after blockchain confirmation.

        Removes funds from pending_out (they're gone now).
        """
        client = BalanceService._get_client()
        if not client:
            return False

        try:
            # Call atomic confirm function
            result = client.rpc("confirm_send", {
                "p_user_id": user_id,
                "p_chain": chain,
                "p_token": token,
                "p_amount": float(amount),
                "p_fee": float(fee)
            }).execute()

            # Update ledger entry if provided
            if ledger_entry_id:
                update_data = {
                    "status": "confirmed",
                    "confirmed_at": datetime.utcnow().isoformat()
                }
                if tx_hash:
                    update_data["tx_hash"] = tx_hash
                if counterparty_address:
                    update_data["counterparty_address"] = counterparty_address

                client.table("ledger_entries").update(update_data).eq(
                    "id", ledger_entry_id
                ).execute()

            return True

        except Exception as e:
            logger.error(f"BalanceService.confirm_send error: {e}")
            return False

    @staticmethod
    def release_reserved(
        user_id: str,
        chain: str,
        token: str,
        amount: Decimal,
        fee: Decimal = Decimal("0"),
        ledger_entry_id: Optional[str] = None,
        reason: str = "Transaction failed"
    ) -> bool:
        """
        Release reserved balance after a failed transaction.

        Returns funds from pending_out back to available.
        """
        client = BalanceService._get_client()
        if not client:
            return False

        try:
            # Call atomic release function
            result = client.rpc("release_reserved_balance", {
                "p_user_id": user_id,
                "p_chain": chain,
                "p_token": token,
                "p_amount": float(amount),
                "p_fee": float(fee)
            }).execute()

            # Update ledger entry if provided
            if ledger_entry_id:
                client.table("ledger_entries").update({
                    "status": "failed",
                    "description": reason
                }).eq("id", ledger_entry_id).execute()

            return True

        except Exception as e:
            logger.error(f"BalanceService.release_reserved error: {e}")
            return False

    # =========================================================================
    # DEPOSIT OPERATIONS
    # =========================================================================

    @staticmethod
    def credit_deposit(
        user_id: str,
        chain: str,
        token: str,
        amount: Decimal,
        tx_hash: Optional[str] = None,
        from_address: Optional[str] = None
    ) -> bool:
        """
        Credit a confirmed deposit to user's balance.

        Call this when a deposit is confirmed on-chain.
        """
        client = BalanceService._get_client()
        if not client:
            return False

        try:
            # Get balance before for audit
            balance_before = BalanceService.get_available_balance(user_id, chain, token)

            # Call atomic credit function
            result = client.rpc("credit_balance", {
                "p_user_id": user_id,
                "p_chain": chain,
                "p_token": token,
                "p_amount": float(amount)
            }).execute()

            # Create ledger entry
            client.table("ledger_entries").insert({
                "user_id": user_id,
                "entry_type": "deposit",
                "chain": chain,
                "token": token,
                "amount": float(amount),  # Positive for credit
                "tx_hash": tx_hash,
                "counterparty_address": from_address,
                "balance_before": float(balance_before),
                "balance_after": float(balance_before + amount),
                "status": "confirmed",
                "confirmed_at": datetime.utcnow().isoformat()
            }).execute()

            return True

        except Exception as e:
            logger.error(f"BalanceService.credit_deposit error: {e}")
            return False

    # =========================================================================
    # YIELD OPERATIONS
    # =========================================================================

    @staticmethod
    def lock_for_yield(
        user_id: str,
        chain: str,
        token: str,
        amount: Decimal,
        protocol: str = "aave"
    ) -> Tuple[bool, Optional[str]]:
        """
        Lock balance for yield deposit.

        Moves from available to locked.
        """
        client = BalanceService._get_client()
        if not client:
            return False, "Database unavailable"

        try:
            # Get balance before
            balance_before = BalanceService.get_available_balance(user_id, chain, token)

            # Call atomic lock function
            result = client.rpc("lock_balance", {
                "p_user_id": user_id,
                "p_chain": chain,
                "p_token": token,
                "p_amount": float(amount)
            }).execute()

            if not result.data:
                return False, "Insufficient balance"

            # Create ledger entry
            entry = client.table("ledger_entries").insert({
                "user_id": user_id,
                "entry_type": "yield_deposit",
                "chain": chain,
                "token": token,
                "amount": -float(amount),  # Moving out of available
                "balance_before": float(balance_before),
                "balance_after": float(balance_before - amount),
                "status": "pending",
                "metadata": {"protocol": protocol}
            }).execute()

            return True, entry.data[0]["id"] if entry.data else None

        except Exception as e:
            logger.error(f"BalanceService.lock_for_yield error: {e}")
            return False, str(e)

    @staticmethod
    def unlock_from_yield(
        user_id: str,
        chain: str,
        token: str,
        amount: Decimal,
        earnings: Decimal = Decimal("0"),
        protocol: str = "aave"
    ) -> bool:
        """
        Unlock balance from yield + credit earnings.

        Moves from locked back to available, plus any earnings.
        """
        client = BalanceService._get_client()
        if not client:
            return False

        try:
            # Unlock principal
            result = client.rpc("unlock_balance", {
                "p_user_id": user_id,
                "p_chain": chain,
                "p_token": token,
                "p_amount": float(amount)
            }).execute()

            # Credit earnings if any
            if earnings > 0:
                client.rpc("credit_balance", {
                    "p_user_id": user_id,
                    "p_chain": chain,
                    "p_token": token,
                    "p_amount": float(earnings)
                }).execute()

            # Create ledger entry
            client.table("ledger_entries").insert({
                "user_id": user_id,
                "entry_type": "yield_withdraw",
                "chain": chain,
                "token": token,
                "amount": float(amount + earnings),
                "status": "confirmed",
                "confirmed_at": datetime.utcnow().isoformat(),
                "metadata": {"protocol": protocol, "earnings": float(earnings)}
            }).execute()

            return True

        except Exception as e:
            logger.error(f"BalanceService.unlock_from_yield error: {e}")
            return False

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    @staticmethod
    def sync_from_blockchain(
        user_id: str,
        chain: str,
        token: str,
        blockchain_balance: Decimal,
        block_number: Optional[int] = None
    ) -> bool:
        """
        Sync internal balance with blockchain (for reconciliation).

        CAUTION: Use sparingly. This can create balance discrepancies if
        there are pending transactions. Prefer credit_deposit/confirm_send.

        Args:
            user_id: User ID
            chain: Chain identifier
            token: Token symbol
            blockchain_balance: Current balance on blockchain
            block_number: Block number of the query
        """
        client = BalanceService._get_client()
        if not client:
            return False

        try:
            # Get current internal balance
            current = BalanceService.get_balance(user_id, chain, token)

            if current is None:
                # First time - just set the balance
                client.table("balances").insert({
                    "user_id": user_id,
                    "chain": chain,
                    "token": token,
                    "available_balance": float(blockchain_balance),
                    "pending_in": 0,
                    "pending_out": 0,
                    "locked_balance": 0,
                    "last_sync_at": datetime.utcnow().isoformat(),
                    "last_sync_block": block_number
                }).execute()
            else:
                # Existing balance - update sync metadata
                # Don't blindly overwrite - just update sync timestamp
                # Actual balance changes should go through proper channels
                client.table("balances").update({
                    "last_sync_at": datetime.utcnow().isoformat(),
                    "last_sync_block": block_number
                }).eq("user_id", user_id).eq("chain", chain).eq("token", token).execute()

                # Log discrepancy if significant
                internal_total = current["available"] + current["pending_out"] + current["locked"]
                diff = abs(blockchain_balance - internal_total)
                if diff > Decimal("0.01"):  # More than 1 cent difference
                    logger.warning(
                        f"Balance discrepancy for {user_id}/{chain}/{token}: "
                        f"blockchain={blockchain_balance}, internal={internal_total}, diff={diff}"
                    )

            return True

        except Exception as e:
            logger.error(f"BalanceService.sync_from_blockchain error: {e}")
            return False

    # =========================================================================
    # LEDGER QUERIES
    # =========================================================================

    @staticmethod
    def get_ledger_entries(
        user_id: str,
        chain: Optional[str] = None,
        token: Optional[str] = None,
        entry_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get ledger entries (transaction history) for a user.
        """
        client = BalanceService._get_client()
        if not client:
            return []

        try:
            query = client.table("ledger_entries").select("*").eq("user_id", user_id)

            if chain:
                query = query.eq("chain", chain)
            if token:
                query = query.eq("token", token)
            if entry_type:
                query = query.eq("entry_type", entry_type)
            if status:
                query = query.eq("status", status)

            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"BalanceService.get_ledger_entries error: {e}")
            return []

    @staticmethod
    def get_pending_transactions(user_id: str) -> List[Dict[str, Any]]:
        """Get all pending transactions for a user."""
        client = BalanceService._get_client()
        if not client:
            return []

        try:
            result = client.table("pending_transactions").select("*").eq(
                "user_id", user_id
            ).in_("status", ["pending", "confirming"]).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"BalanceService.get_pending_transactions error: {e}")
            return []

    # =========================================================================
    # NONCE MANAGEMENT
    # =========================================================================

    @staticmethod
    def check_and_record_nonce(
        wallet_address: str,
        chain: str,
        nonce: int,
        tx_hash: Optional[str] = None
    ) -> bool:
        """
        Check if nonce was used and record it if not.

        Returns True if nonce is fresh (not used before).
        Returns False if nonce was already used (replay attempt).
        """
        client = BalanceService._get_client()
        if not client:
            return False

        try:
            # Try to insert - will fail if duplicate
            client.table("used_nonces").insert({
                "wallet_address": wallet_address.lower(),
                "chain": chain,
                "nonce": nonce,
                "tx_hash": tx_hash
            }).execute()

            return True

        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                logger.warning(f"Nonce replay attempt: {wallet_address}/{chain}/{nonce}")
                return False
            logger.error(f"BalanceService.check_and_record_nonce error: {e}")
            return False

    @staticmethod
    def get_next_nonce(wallet_address: str, chain: str) -> int:
        """
        Get the next available nonce for a wallet.

        Returns the max recorded nonce + 1, or queries blockchain if no records.
        """
        client = BalanceService._get_client()
        if not client:
            return 0

        try:
            result = client.table("used_nonces").select("nonce").eq(
                "wallet_address", wallet_address.lower()
            ).eq("chain", chain).order("nonce", desc=True).limit(1).execute()

            if result.data:
                return result.data[0]["nonce"] + 1
            return 0

        except Exception as e:
            logger.error(f"BalanceService.get_next_nonce error: {e}")
            return 0


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def generate_idempotency_key() -> str:
    """Generate a unique idempotency key for a transaction."""
    return str(uuid.uuid4())


def format_balance_display(balance: Dict[str, Decimal]) -> str:
    """Format balance for user display."""
    available = balance.get("available", Decimal("0"))
    pending_in = balance.get("pending_in", Decimal("0"))
    pending_out = balance.get("pending_out", Decimal("0"))
    locked = balance.get("locked", Decimal("0"))

    parts = [f"${available:.2f} available"]

    if pending_in > 0:
        parts.append(f"+${pending_in:.2f} incoming")
    if pending_out > 0:
        parts.append(f"-${pending_out:.2f} pending")
    if locked > 0:
        parts.append(f"${locked:.2f} earning")

    return " | ".join(parts)
