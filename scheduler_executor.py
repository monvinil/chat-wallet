"""
Background Task Executor for Scheduled Payments

This module provides task execution for scheduled transfers, gift cards, and conditional triggers.
Can run as:
1. Standalone worker (for production: python scheduler_executor.py)
2. On-demand check (for MVP: called on page load)

Production deployment: Run as separate process/container on Railway
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from croniter import croniter

from utils.logger import logger


class TaskExecutor:
    """Executes scheduled tasks from Supabase"""

    def __init__(self):
        self.running = False

    def get_due_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch tasks that are due for execution"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                logger.error("No Supabase connection for task executor")
                return []

            now = datetime.utcnow().isoformat()

            # Get active tasks where next_run_at <= now
            result = supabase.table("scheduled_tasks").select("*").eq(
                "status", "active"
            ).lte(
                "next_run_at", now
            ).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to fetch due tasks: {e}")
            return []

    def get_conditional_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch conditional tasks that need checking"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return []

            result = supabase.table("scheduled_tasks").select("*").eq(
                "status", "active"
            ).eq(
                "schedule_type", "conditional"
            ).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to fetch conditional tasks: {e}")
            return []

    def execute_transfer(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a USDC transfer task"""
        from direct_tx import DirectTransactionExecutor
        from wallet_manager import WalletManager
        from supabase_client import get_supabase_client, get_user_encrypted_wallet

        task_params = task.get("task_params", {})
        if isinstance(task_params, str):
            task_params = json.loads(task_params)

        to_address = task_params.get("to_address")
        amount = float(task_params.get("amount", 0))
        chain = task_params.get("chain", "base-mainnet")
        user_id = task.get("user_id")

        if not to_address or amount <= 0:
            return {"success": False, "error": "Invalid transfer parameters"}

        # Get user's encrypted wallet
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            return {"success": False, "error": "No database connection"}

        # For automated tasks, we need the wallet to be pre-authorized
        # This requires the user to have enabled "auto-execution" for scheduled tasks
        # For MVP: Skip actual execution, just log intent
        logger.info(f"Would execute transfer: {amount} USDC to {to_address} on {chain}")

        # TODO: Implement actual execution with pre-authorized wallet
        # For now, return success for demo purposes
        return {
            "success": True,
            "simulated": True,
            "amount": amount,
            "to_address": to_address,
            "chain": chain
        }

    def execute_gift_card(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a gift card purchase task"""
        task_params = task.get("task_params", {})
        if isinstance(task_params, str):
            task_params = json.loads(task_params)

        product_id = task_params.get("product_id")
        amount = float(task_params.get("amount", 0))

        if not product_id or amount <= 0:
            return {"success": False, "error": "Invalid gift card parameters"}

        # TODO: Implement actual Bitrefill purchase
        logger.info(f"Would purchase gift card: ${amount} {product_id}")

        return {
            "success": True,
            "simulated": True,
            "product_id": product_id,
            "amount": amount
        }

    def check_condition(self, task: Dict[str, Any]) -> bool:
        """Check if a conditional task's trigger is met"""
        from chain_utils import ChainUtils

        condition_type = task.get("condition_type")
        condition_value = float(task.get("condition_value", 0))
        condition_asset = task.get("condition_asset", "USDC")
        user_id = task.get("user_id")

        if condition_type in ["balance_below", "balance_above"]:
            # Get user's current balance
            # TODO: Need wallet address from user record
            # For now, skip condition check
            return False

        elif condition_type in ["price_below", "price_above"]:
            # Get current price
            # TODO: Implement price oracle
            return False

        return False

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task based on its type"""
        task_type = task.get("task_type")

        if task_type == "transfer":
            return self.execute_transfer(task)
        elif task_type == "gift_card":
            return self.execute_gift_card(task)
        else:
            return {"success": False, "error": f"Unknown task type: {task_type}"}

    def record_task_run(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Record task execution in history"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return

            run_record = {
                "task_id": task["id"],
                "user_id": task["user_id"],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "status": "success" if result.get("success") else "failed",
                "result": json.dumps(result),
                "error_message": result.get("error"),
                "tx_hash": result.get("tx_hash")
            }

            supabase.table("task_runs").insert(run_record).execute()

        except Exception as e:
            logger.error(f"Failed to record task run: {e}")

    def update_task_after_run(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Update task status and next_run_at after execution"""
        from supabase_client import get_supabase_client

        try:
            supabase = get_supabase_client(use_service_key=True)
            if not supabase:
                return

            updates = {
                "last_run_at": datetime.utcnow().isoformat(),
                "run_count": task.get("run_count", 0) + 1
            }

            if result.get("success"):
                updates["consecutive_failures"] = 0
            else:
                updates["consecutive_failures"] = task.get("consecutive_failures", 0) + 1
                # Pause task after 3 consecutive failures
                if updates["consecutive_failures"] >= 3:
                    updates["status"] = "paused"
                    logger.warning(f"Paused task {task['id']} after 3 failures")

            # Calculate next run for recurring tasks
            if task.get("schedule_type") == "recurring" and task.get("cron_expression"):
                try:
                    cron_iter = croniter(task["cron_expression"], datetime.utcnow())
                    updates["next_run_at"] = cron_iter.get_next(datetime).isoformat()
                except Exception:
                    pass

            # Check if max runs reached
            max_runs = task.get("max_runs")
            if max_runs and updates["run_count"] >= max_runs:
                updates["status"] = "completed"

            # Mark one-time tasks as completed
            if task.get("schedule_type") == "once":
                updates["status"] = "completed"

            supabase.table("scheduled_tasks").update(updates).eq(
                "id", task["id"]
            ).execute()

        except Exception as e:
            logger.error(f"Failed to update task: {e}")

    def process_due_tasks(self) -> int:
        """Process all due tasks. Returns number of tasks processed."""
        tasks = self.get_due_tasks()
        processed = 0

        for task in tasks:
            try:
                logger.info(f"Executing task {task['id'][:8]}: {task.get('description', '')}")
                result = self.execute_task(task)
                self.record_task_run(task, result)
                self.update_task_after_run(task, result)
                processed += 1

                if result.get("success"):
                    logger.info(f"Task {task['id'][:8]} completed successfully")
                else:
                    logger.warning(f"Task {task['id'][:8]} failed: {result.get('error')}")

            except Exception as e:
                logger.error(f"Error executing task {task['id'][:8]}: {e}")
                self.record_task_run(task, {"success": False, "error": str(e)})
                self.update_task_after_run(task, {"success": False})

        return processed

    def process_conditional_tasks(self) -> int:
        """Check and process conditional tasks. Returns number processed."""
        tasks = self.get_conditional_tasks()
        processed = 0

        for task in tasks:
            try:
                if self.check_condition(task):
                    logger.info(f"Condition met for task {task['id'][:8]}")
                    result = self.execute_task(task)
                    self.record_task_run(task, result)
                    self.update_task_after_run(task, result)
                    processed += 1
            except Exception as e:
                logger.error(f"Error checking conditional task {task['id'][:8]}: {e}")

        return processed

    def run_once(self) -> Dict[str, int]:
        """Run one iteration of task processing"""
        scheduled = self.process_due_tasks()
        conditional = self.process_conditional_tasks()
        return {"scheduled": scheduled, "conditional": conditional}

    def run_forever(self, interval_seconds: int = 60):
        """Run continuously (for standalone worker)"""
        logger.info(f"Starting task executor (interval: {interval_seconds}s)")
        self.running = True

        while self.running:
            try:
                result = self.run_once()
                total = result["scheduled"] + result["conditional"]
                if total > 0:
                    logger.info(f"Processed {total} tasks")
            except Exception as e:
                logger.error(f"Error in task executor loop: {e}")

            time.sleep(interval_seconds)

    def stop(self):
        """Stop the executor"""
        self.running = False


# Singleton instance
_executor = None


def get_executor() -> TaskExecutor:
    """Get or create executor instance"""
    global _executor
    if _executor is None:
        _executor = TaskExecutor()
    return _executor


def check_and_execute_due_tasks() -> Dict[str, int]:
    """
    Check and execute due tasks (call from Streamlit on page load).
    This is a fallback for when background worker isn't running.
    """
    executor = get_executor()
    return executor.run_once()


if __name__ == "__main__":
    # Run as standalone worker
    import argparse

    parser = argparse.ArgumentParser(description="Task Executor Worker")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    args = parser.parse_args()

    executor = TaskExecutor()
    try:
        executor.run_forever(interval_seconds=args.interval)
    except KeyboardInterrupt:
        logger.info("Shutting down task executor")
        executor.stop()
