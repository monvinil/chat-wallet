"""
Scheduled Tasks - LangChain tools for creating and managing scheduled actions.

Supports:
- One-time scheduled tasks (run at specific time)
- Recurring tasks (daily, weekly, monthly via cron)
- Conditional triggers (balance-based, price-based)

Task types: transfer, gift_card, swap, bridge
"""

import json
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from scheduler_manager import SchedulerManager


@tool
def create_scheduled_transfer(
    to_address: str,
    amount: float,
    schedule_type: str = "once",
    schedule_time: Optional[str] = None,
    cron_expression: Optional[str] = None,
    description: Optional[str] = None,
    max_runs: Optional[int] = None
) -> str:
    """
    Create a scheduled USDC transfer.

    Args:
        to_address: Recipient wallet address (0x...)
        amount: Amount in USDC to send
        schedule_type: "once" for one-time, "recurring" for repeated
        schedule_time: For one-time: ISO datetime or natural language ("tomorrow 9am", "next Monday")
        cron_expression: For recurring: cron format ("0 9 * * 1" = every Monday 9am)
        description: Human-readable description (e.g., "Weekly allowance to Alice")
        max_runs: For recurring: max number of times to run (None = unlimited)

    Returns:
        Confirmation with task ID and schedule details

    Examples:
        - "Send $50 to 0x... every Friday at 5pm" -> recurring with cron
        - "Send $100 to 0x... tomorrow at 9am" -> once with schedule_time
        - "Send $25 to mom weekly" -> recurring weekly
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to create scheduled tasks"

    # Validate address
    if not to_address or not to_address.startswith("0x") or len(to_address) != 42:
        return "Error: Invalid recipient address. Must be a valid 0x... address"

    if amount <= 0:
        return "Error: Amount must be greater than 0"

    # Build task params
    task_params = {
        "to_address": to_address,
        "amount": amount,
        "currency": "USDC",
        "chain": "base-mainnet"  # Default chain
    }

    # Create the scheduled task
    result = SchedulerManager.create_task(
        user_id=user_id,
        task_type="transfer",
        task_params=task_params,
        schedule_type=schedule_type,
        schedule_time=schedule_time,
        cron_expression=cron_expression,
        description=description or f"Send ${amount} USDC to {to_address[:10]}...",
        max_runs=max_runs
    )

    return result


@tool
def create_scheduled_gift_card(
    product_id: str,
    amount: float,
    schedule_type: str = "once",
    schedule_time: Optional[str] = None,
    cron_expression: Optional[str] = None,
    description: Optional[str] = None,
    max_runs: Optional[int] = None
) -> str:
    """
    Create a scheduled gift card purchase.

    Args:
        product_id: Bitrefill product ID (e.g., "amazon-us", "starbucks-us")
        amount: Amount in USD
        schedule_type: "once" for one-time, "recurring" for repeated
        schedule_time: For one-time: when to execute
        cron_expression: For recurring: cron format
        description: Human-readable description
        max_runs: For recurring: max number of times to run

    Returns:
        Confirmation with task ID and schedule details

    Examples:
        - "Buy a $25 Starbucks card every Monday" -> recurring weekly
        - "Get a $50 Amazon card on the 1st of each month" -> recurring monthly
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to create scheduled tasks"

    if amount <= 0:
        return "Error: Amount must be greater than 0"

    task_params = {
        "product_id": product_id,
        "amount": amount
    }

    result = SchedulerManager.create_task(
        user_id=user_id,
        task_type="gift_card",
        task_params=task_params,
        schedule_type=schedule_type,
        schedule_time=schedule_time,
        cron_expression=cron_expression,
        description=description or f"Buy ${amount} {product_id} gift card",
        max_runs=max_runs
    )

    return result


@tool
def create_conditional_task(
    task_type: str,
    task_params: str,
    condition_type: str,
    condition_value: float,
    condition_asset: str = "USDC",
    description: Optional[str] = None
) -> str:
    """
    Create a task that triggers when a condition is met.

    Args:
        task_type: "transfer", "gift_card", "swap"
        task_params: JSON string with task-specific parameters
        condition_type: "balance_below", "balance_above", "price_below", "price_above"
        condition_value: Threshold value for the condition
        condition_asset: Asset to monitor (USDC, ETH, BTC)
        description: Human-readable description

    Returns:
        Confirmation with task ID and condition details

    Examples:
        - "If my balance drops below $100, buy $50 Starbucks" -> balance_below
        - "If ETH drops below $3000, swap $500 to ETH" -> price_below
        - "When balance exceeds $1000, send $100 to savings" -> balance_above
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to create conditional tasks"

    # Parse task params
    try:
        params = json.loads(task_params)
    except json.JSONDecodeError:
        return "Error: task_params must be valid JSON"

    valid_conditions = ["balance_below", "balance_above", "price_below", "price_above"]
    if condition_type not in valid_conditions:
        return f"Error: condition_type must be one of {valid_conditions}"

    result = SchedulerManager.create_task(
        user_id=user_id,
        task_type=task_type,
        task_params=params,
        schedule_type="conditional",
        condition_type=condition_type,
        condition_value=condition_value,
        condition_asset=condition_asset,
        description=description or f"When {condition_asset} {condition_type.replace('_', ' ')} ${condition_value}"
    )

    return result


@tool
def list_scheduled_tasks(status: str = "active") -> str:
    """
    List all scheduled tasks for the current user.

    Args:
        status: Filter by status - "active", "paused", "completed", "all"

    Returns:
        List of scheduled tasks with their details
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to view scheduled tasks"

    tasks = SchedulerManager.get_user_tasks(user_id, status)

    if not tasks:
        return f"No {status} scheduled tasks found. Create one using 'schedule a transfer' or 'set up recurring payment'."

    result = f"**Your {status} scheduled tasks:**\n\n"

    for task in tasks:
        task_id = task.get("id", "")[:8]
        task_type = task.get("task_type", "unknown")
        description = task.get("description", "No description")
        schedule_type = task.get("schedule_type", "")
        next_run = task.get("next_run_at", "Not scheduled")
        run_count = task.get("run_count", 0)
        status_emoji = {"active": "🟢", "paused": "⏸️", "completed": "✅", "failed": "❌"}.get(task.get("status"), "⚪")

        result += f"{status_emoji} **{description}**\n"
        result += f"   ID: `{task_id}` | Type: {task_type} | Schedule: {schedule_type}\n"

        if schedule_type == "recurring":
            cron = task.get("cron_expression", "")
            result += f"   Cron: `{cron}` | Runs: {run_count}\n"
        elif schedule_type == "conditional":
            cond = task.get("condition_type", "")
            cond_val = task.get("condition_value", 0)
            cond_asset = task.get("condition_asset", "USDC")
            result += f"   Trigger: {cond_asset} {cond.replace('_', ' ')} ${cond_val}\n"

        if next_run and next_run != "Not scheduled":
            result += f"   Next run: {next_run}\n"

        result += "\n"

    return result


@tool
def pause_scheduled_task(task_id: str) -> str:
    """
    Pause a scheduled task (can be resumed later).

    Args:
        task_id: The task ID (can be partial, e.g., first 8 characters)

    Returns:
        Confirmation message
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to manage scheduled tasks"

    return SchedulerManager.update_task_status(user_id, task_id, "paused")


@tool
def resume_scheduled_task(task_id: str) -> str:
    """
    Resume a paused scheduled task.

    Args:
        task_id: The task ID (can be partial, e.g., first 8 characters)

    Returns:
        Confirmation message
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to manage scheduled tasks"

    return SchedulerManager.update_task_status(user_id, task_id, "active")


@tool
def cancel_scheduled_task(task_id: str) -> str:
    """
    Cancel and delete a scheduled task.

    Args:
        task_id: The task ID (can be partial, e.g., first 8 characters)

    Returns:
        Confirmation message
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to manage scheduled tasks"

    return SchedulerManager.delete_task(user_id, task_id)


@tool
def get_task_history(task_id: str, limit: int = 5) -> str:
    """
    Get execution history for a scheduled task.

    Args:
        task_id: The task ID (can be partial)
        limit: Number of recent runs to show (default 5)

    Returns:
        List of recent task executions with results
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return "Error: Please log in to view task history"

    return SchedulerManager.get_task_runs(user_id, task_id, limit)


def get_scheduler_tools() -> List:
    """Get list of scheduler tools for AI agent"""
    return [
        create_scheduled_transfer,
        create_scheduled_gift_card,
        create_conditional_task,
        list_scheduled_tasks,
        pause_scheduled_task,
        resume_scheduled_task,
        cancel_scheduled_task,
        get_task_history
    ]
