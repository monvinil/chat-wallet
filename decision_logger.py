"""
Decision Logger for AI Training Data

Logs all AI agent decisions for future model fine-tuning.
Captures:
- User context (balance, settings, history)
- User message
- AI reasoning/response
- Tool calls made
- Outcome (success/failure)

Data is stored in Supabase for later export to training datasets.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st

from utils.logger import logger


class DecisionLogger:
    """Logs AI decisions for training data collection"""

    @staticmethod
    def log_decision(
        user_id: str,
        user_message: str,
        ai_response: str,
        tool_calls: List[Dict[str, Any]] = None,
        user_context: Dict[str, Any] = None,
        outcome: str = None,
        outcome_details: Dict[str, Any] = None,
        session_id: str = None
    ) -> Optional[str]:
        """
        Log an AI decision for training data.

        Args:
            user_id: User identifier
            user_message: The user's input message
            ai_response: The AI's text response
            tool_calls: List of tools called and their results
            user_context: User's financial context (balance, positions, etc.)
            outcome: "success", "failure", "pending", "user_cancelled"
            outcome_details: Additional outcome information
            session_id: Session identifier for grouping conversations

        Returns:
            Decision log ID if successful, None otherwise
        """
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                logger.debug("No Supabase connection for decision logging")
                return None

            # Build log entry
            log_entry = {
                "user_id": user_id,
                "session_id": session_id or st.session_state.get("session_token", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "user_message": user_message,
                "ai_response": ai_response,
                "tool_calls": json.dumps(tool_calls) if tool_calls else None,
                "user_context": json.dumps(user_context) if user_context else None,
                "outcome": outcome,
                "outcome_details": json.dumps(outcome_details) if outcome_details else None,
                "model": st.session_state.get("_current_model", "unknown"),
                "app_version": "v12"
            }

            result = supabase.table("decision_logs").insert(log_entry).execute()

            if result.data:
                return result.data[0].get("id")
            return None

        except Exception as e:
            logger.debug(f"Failed to log decision: {e}")
            return None

    @staticmethod
    def update_outcome(
        log_id: str,
        outcome: str,
        outcome_details: Dict[str, Any] = None
    ) -> bool:
        """
        Update the outcome of a previously logged decision.

        Use this when the result of a decision becomes known after the fact.
        """
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return False

            updates = {
                "outcome": outcome,
                "outcome_updated_at": datetime.utcnow().isoformat()
            }
            if outcome_details:
                updates["outcome_details"] = json.dumps(outcome_details)

            supabase.table("decision_logs").update(updates).eq("id", log_id).execute()
            return True

        except Exception as e:
            logger.debug(f"Failed to update decision outcome: {e}")
            return False

    @staticmethod
    def get_user_context(wallet_address: str = None) -> Dict[str, Any]:
        """
        Build user context for decision logging.

        Captures relevant financial state without sensitive data.
        """
        context = {
            "has_wallet": bool(st.session_state.get("wallet_address")),
            "wallet_unlocked": st.session_state.get("wallet_locked") == False,
            "has_balances": bool(st.session_state.get("balances")),
        }

        # Add balance summary (not exact amounts for privacy)
        balances = st.session_state.get("balances", {})
        if balances:
            total = sum(
                b.get("usdc", 0) for b in balances.values()
                if isinstance(b, dict)
            )
            # Bucket the balance for privacy
            if total == 0:
                context["balance_bucket"] = "zero"
            elif total < 100:
                context["balance_bucket"] = "under_100"
            elif total < 1000:
                context["balance_bucket"] = "100_to_1000"
            elif total < 10000:
                context["balance_bucket"] = "1000_to_10000"
            else:
                context["balance_bucket"] = "over_10000"

            context["active_networks"] = list(balances.keys())

        # Add settings context
        user_id = st.session_state.get("user_id")
        if user_id:
            from settings_manager import SettingsManager
            settings = SettingsManager.get_user_settings(user_id)
            context["daily_limit"] = settings.get("daily_spend_limit", 100)
            context["approval_threshold"] = settings.get("approval_threshold", 50)

        return context

    @staticmethod
    def extract_tool_calls(agent_response: Any) -> List[Dict[str, Any]]:
        """
        Extract tool calls from an agent response.

        Works with LangChain agent executor outputs.
        """
        tool_calls = []

        try:
            # Handle different response formats
            if hasattr(agent_response, "intermediate_steps"):
                for step in agent_response.intermediate_steps:
                    if len(step) >= 2:
                        action, result = step[0], step[1]
                        tool_calls.append({
                            "tool": getattr(action, "tool", str(action)),
                            "input": getattr(action, "tool_input", {}),
                            "output_preview": str(result)[:500]  # Truncate for storage
                        })
            elif isinstance(agent_response, dict):
                if "intermediate_steps" in agent_response:
                    for step in agent_response["intermediate_steps"]:
                        if len(step) >= 2:
                            tool_calls.append({
                                "tool": str(step[0]),
                                "output_preview": str(step[1])[:500]
                            })
        except Exception as e:
            logger.debug(f"Failed to extract tool calls: {e}")

        return tool_calls


# Convenience function for quick logging
def log_ai_decision(
    user_message: str,
    ai_response: str,
    tool_calls: List[Dict[str, Any]] = None,
    outcome: str = None
) -> Optional[str]:
    """
    Quick helper to log an AI decision.

    Call this after each AI response in the chat flow.
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None

    wallet_address = st.session_state.get("wallet_address")
    user_context = DecisionLogger.get_user_context(wallet_address)

    return DecisionLogger.log_decision(
        user_id=user_id,
        user_message=user_message,
        ai_response=ai_response,
        tool_calls=tool_calls,
        user_context=user_context,
        outcome=outcome
    )


# SQL Migration for decision_logs table
DECISION_LOGS_MIGRATION = """
-- Decision Logs table for AI training data
CREATE TABLE IF NOT EXISTS decision_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    tool_calls JSONB,
    user_context JSONB,
    outcome VARCHAR(50),  -- 'success', 'failure', 'pending', 'user_cancelled'
    outcome_details JSONB,
    outcome_updated_at TIMESTAMPTZ,
    model VARCHAR(100),
    app_version VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decision_logs_user ON decision_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_decision_logs_timestamp ON decision_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_decision_logs_outcome ON decision_logs(outcome);

-- RLS
ALTER TABLE decision_logs ENABLE ROW LEVEL SECURITY;

-- Service role can access all (for training data export)
CREATE POLICY "Service role full access" ON decision_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Users can view their own logs (optional, for transparency)
CREATE POLICY "Users can view own logs" ON decision_logs
    FOR SELECT USING (auth.uid() = user_id);
"""
