"""
API Key Usage Tracker

Tracks per-request token usage, costs, and aggregates daily statistics
for users' own API keys. Provides usage summaries for the settings dashboard.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from utils.logger import logger


# Cost per 1M tokens (USD) by provider/model
# Prices as of early 2026 - update as needed
TOKEN_COSTS = {
    "anthropic": {
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
        "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
        "claude-haiku-4-20250514": {"input": 0.80, "output": 4.00},
    },
    "openai": {
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    },
    "google": {
        "gemini-2.5-flash": {"input": 0.0, "output": 0.0},  # Free tier
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-2.5-flash-lite": {"input": 0.0, "output": 0.0},
    },
}


def _estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD based on provider, model, and token counts."""
    provider_costs = TOKEN_COSTS.get(provider, {})
    model_costs = provider_costs.get(model)
    if not model_costs:
        return 0.0
    input_cost = (input_tokens / 1_000_000) * model_costs["input"]
    output_cost = (output_tokens / 1_000_000) * model_costs["output"]
    return round(input_cost + output_cost, 6)


class APIKeyUsageTracker:
    """Track and query API key usage statistics."""

    @staticmethod
    def record_usage(
        user_id: str,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        request_type: str = "chat",
    ) -> bool:
        """
        Record a single API request's usage.

        Called after each LLM invocation with token counts from the response.
        Also updates the daily aggregation table.
        """
        from supabase_client import get_supabase_client

        total_tokens = input_tokens + output_tokens
        estimated_cost = _estimate_cost(provider, model, input_tokens, output_tokens)

        try:
            client = get_supabase_client(use_service_key=True)
            if not client:
                return False

            # Insert per-request record
            client.table("api_key_usage").insert({
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "request_type": request_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": float(estimated_cost),
                "success": success,
                "error_message": error_message,
            }).execute()

            # Upsert daily aggregate
            today = date.today().isoformat()
            client.table("api_key_usage_daily").upsert({
                "user_id": user_id,
                "usage_date": today,
                "provider": provider,
                "model": model,
                "request_count": 1,
                "total_input_tokens": input_tokens,
                "total_output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "total_estimated_cost": float(estimated_cost),
                "error_count": 0 if success else 1,
                "updated_at": datetime.utcnow().isoformat(),
            }, on_conflict="user_id,usage_date,provider,model").execute()

            return True
        except Exception as e:
            logger.error(f"Failed to record API usage: {e}")
            return False

    @staticmethod
    def get_usage_summary(user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get usage summary for a user over the last N days.

        Returns:
            Dict with today, this_week, this_month stats, and daily breakdown.
        """
        from supabase_client import get_supabase_client

        try:
            client = get_supabase_client(use_service_key=True)
            if not client:
                return _empty_summary()

            since = (date.today() - timedelta(days=days)).isoformat()
            result = client.table("api_key_usage_daily").select("*").eq(
                "user_id", user_id
            ).gte("usage_date", since).order("usage_date", desc=True).execute()

            if not result.data:
                return _empty_summary()

            rows = result.data
            today_str = date.today().isoformat()
            week_start = (date.today() - timedelta(days=7)).isoformat()

            today_stats = {"requests": 0, "tokens": 0, "cost": 0.0}
            week_stats = {"requests": 0, "tokens": 0, "cost": 0.0}
            month_stats = {"requests": 0, "tokens": 0, "cost": 0.0}
            by_model: Dict[str, Dict[str, Any]] = {}
            daily_breakdown: List[Dict[str, Any]] = []

            for row in rows:
                req_count = row.get("request_count", 0)
                tokens = row.get("total_tokens", 0)
                cost = float(row.get("total_estimated_cost", 0))
                usage_date = row.get("usage_date", "")
                model = row.get("model", "unknown")
                provider = row.get("provider", "unknown")

                # Month totals (all rows within range)
                month_stats["requests"] += req_count
                month_stats["tokens"] += tokens
                month_stats["cost"] += cost

                # Week totals
                if usage_date >= week_start:
                    week_stats["requests"] += req_count
                    week_stats["tokens"] += tokens
                    week_stats["cost"] += cost

                # Today totals
                if usage_date == today_str:
                    today_stats["requests"] += req_count
                    today_stats["tokens"] += tokens
                    today_stats["cost"] += cost

                # By model breakdown
                key = f"{provider}/{model}"
                if key not in by_model:
                    by_model[key] = {"provider": provider, "model": model, "requests": 0, "tokens": 0, "cost": 0.0}
                by_model[key]["requests"] += req_count
                by_model[key]["tokens"] += tokens
                by_model[key]["cost"] += cost

                # Daily breakdown (aggregate per date)
                existing_day = next((d for d in daily_breakdown if d["date"] == usage_date), None)
                if existing_day:
                    existing_day["requests"] += req_count
                    existing_day["tokens"] += tokens
                    existing_day["cost"] += cost
                else:
                    daily_breakdown.append({
                        "date": usage_date,
                        "requests": req_count,
                        "tokens": tokens,
                        "cost": cost,
                    })

            return {
                "today": today_stats,
                "this_week": week_stats,
                "this_month": month_stats,
                "by_model": list(by_model.values()),
                "daily": daily_breakdown[:30],
            }

        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return _empty_summary()

    @staticmethod
    def get_recent_requests(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent individual API requests for a user."""
        from supabase_client import get_supabase_client

        try:
            client = get_supabase_client(use_service_key=True)
            if not client:
                return []

            result = client.table("api_key_usage").select(
                "provider, model, input_tokens, output_tokens, total_tokens, "
                "estimated_cost, success, created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get recent requests: {e}")
            return []


def _empty_summary() -> Dict[str, Any]:
    """Return an empty usage summary structure."""
    empty = {"requests": 0, "tokens": 0, "cost": 0.0}
    return {
        "today": dict(empty),
        "this_week": dict(empty),
        "this_month": dict(empty),
        "by_model": [],
        "daily": [],
    }
