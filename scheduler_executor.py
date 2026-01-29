"""
Background Task Executor for Scheduled Payments

This module provides task execution for scheduled transfers, gift cards, and conditional triggers.
Can run as:
1. Standalone worker (for production: python scheduler_executor.py)
2. On-demand check (for MVP: called on page load)
3. HTTP endpoint (for cron services like cron-job.org)

Production deployment options:
- Railway: Deploy as separate service
- Fly.io: Deploy as separate app
- Render: Background worker
- External cron: Call /api/execute-tasks endpoint

Environment variables required:
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- TASK_EXECUTOR_SECRET (for HTTP endpoint auth)
"""

import os
import sys
import time
import json
import signal
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from croniter import croniter

# Add parent directory to path for imports when running standalone
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        """
        Execute a USDC transfer task.

        For scheduled transfers to work, the user must have:
        1. Enabled "auto-execute" for scheduled payments in settings
        2. A valid encrypted wallet stored in the database
        3. Sufficient balance (checked via BalanceService)

        Security: The wallet decryption key is stored encrypted with a
        user-specific key. For fully autonomous execution, consider
        using Circle Programmable Wallets instead.
        """
        from direct_tx import DirectTransactionExecutor
        from balance_service import BalanceService, generate_idempotency_key
        from supabase_client import get_supabase_client
        from config import calculate_fee

        task_params = task.get("task_params", {})
        if isinstance(task_params, str):
            task_params = json.loads(task_params)

        to_address = task_params.get("to_address")
        amount = Decimal(str(task_params.get("amount", 0)))
        chain = task_params.get("chain", "base-mainnet")
        user_id = task.get("user_id")

        if not to_address or amount <= 0:
            return {"success": False, "error": "Invalid transfer parameters"}

        # Check if user has auto-execute enabled
        supabase = get_supabase_client(use_service_key=True)
        if not supabase:
            return {"success": False, "error": "No database connection"}

        try:
            settings = supabase.table("user_settings").select(
                "auto_execute_scheduled, scheduled_tx_private_key_encrypted"
            ).eq("user_id", user_id).single().execute()

            if not settings.data or not settings.data.get("auto_execute_scheduled"):
                return {
                    "success": False,
                    "error": "Auto-execute not enabled. User must approve manually.",
                    "requires_manual_approval": True
                }

            # Check balance via BalanceService
            fee = Decimal(str(calculate_fee(float(amount))))
            total_needed = amount + fee

            available = BalanceService.get_available_balance(user_id, chain, "USDC")
            if available < total_needed:
                return {
                    "success": False,
                    "error": f"Insufficient balance. Need ${total_needed:.2f}, have ${available:.2f}"
                }

            # Reserve balance (prevents double-spend)
            idempotency_key = generate_idempotency_key()
            reserved, ledger_id = BalanceService.reserve_for_send(
                user_id, chain, "USDC", amount, fee, idempotency_key
            )

            if not reserved:
                return {"success": False, "error": f"Failed to reserve balance: {ledger_id}"}

            # Get encrypted private key for auto-execution
            encrypted_key = settings.data.get("scheduled_tx_private_key_encrypted")
            if not encrypted_key:
                # Release the reserved balance
                BalanceService.release_reserved(user_id, chain, "USDC", amount, fee, ledger_id)
                return {
                    "success": False,
                    "error": "No auto-execution key configured",
                    "requires_manual_approval": True
                }

            # Decrypt private key (requires scheduler service secret)
            try:
                from utils.encryption import PasswordEncryption
                scheduler_secret = os.getenv("SCHEDULER_ENCRYPTION_SECRET")
                if not scheduler_secret:
                    BalanceService.release_reserved(user_id, chain, "USDC", amount, fee, ledger_id)
                    return {"success": False, "error": "Scheduler secret not configured"}

                private_key = PasswordEncryption.decrypt_with_key(
                    encrypted_key, scheduler_secret
                )
            except Exception as e:
                BalanceService.release_reserved(user_id, chain, "USDC", amount, fee, ledger_id)
                return {"success": False, "error": f"Failed to decrypt key: {e}"}

            # Execute the transfer
            executor = DirectTransactionExecutor(chain)
            result = executor.execute_transfer(
                private_key=private_key,
                to_address=to_address,
                amount_usdc=float(amount),
                user_id=user_id
            )

            if result.get("success"):
                # Confirm the send (removes from pending_out)
                BalanceService.confirm_send(
                    user_id, chain, "USDC", amount, fee,
                    tx_hash=result.get("tx_hash"),
                    ledger_entry_id=ledger_id,
                    counterparty_address=to_address
                )
                return {
                    "success": True,
                    "tx_hash": result.get("tx_hash"),
                    "amount": float(amount),
                    "to_address": to_address,
                    "chain": chain,
                    "fee": float(fee)
                }
            else:
                # Release reserved balance on failure
                BalanceService.release_reserved(
                    user_id, chain, "USDC", amount, fee, ledger_id,
                    reason=result.get("error", "Transaction failed")
                )
                return {
                    "success": False,
                    "error": result.get("error", "Transaction failed")
                }

        except Exception as e:
            logger.error(f"execute_transfer error: {e}")
            return {"success": False, "error": str(e)}

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


def run_http_server(port: int = 8080):
    """
    Run a simple HTTP server for cron-triggered execution.

    Endpoints:
    - GET /health - Health check
    - POST /execute - Execute due tasks (requires auth)

    Use with cron services like cron-job.org, EasyCron, or GitHub Actions.
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse

    executor_secret = os.getenv("TASK_EXECUTOR_SECRET", "")

    class TaskHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "healthy"}')
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/execute":
                # Check auth
                auth_header = self.headers.get("Authorization", "")
                if executor_secret and auth_header != f"Bearer {executor_secret}":
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error": "Unauthorized"}')
                    return

                # Execute tasks
                executor = get_executor()
                result = executor.run_once()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = json.dumps({
                    "success": True,
                    "scheduled_processed": result["scheduled"],
                    "conditional_processed": result["conditional"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.wfile.write(response.encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            logger.info(f"HTTP: {args[0]}")

    server = HTTPServer(("0.0.0.0", port), TaskHandler)
    logger.info(f"Starting HTTP server on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Task Executor Worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as continuous worker (checks every 60 seconds)
  python scheduler_executor.py --mode worker --interval 60

  # Run once and exit (for external cron)
  python scheduler_executor.py --mode once

  # Run HTTP server (for webhook-based triggering)
  python scheduler_executor.py --mode http --port 8080
        """
    )
    parser.add_argument(
        "--mode",
        choices=["worker", "once", "http"],
        default="worker",
        help="Execution mode: worker (continuous), once (single run), http (server)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (worker mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP server port (http mode only)"
    )
    args = parser.parse_args()

    # Setup graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        executor = get_executor()
        executor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.mode == "once":
        # Run once and exit
        executor = TaskExecutor()
        result = executor.run_once()
        total = result["scheduled"] + result["conditional"]
        logger.info(f"Processed {total} tasks (scheduled: {result['scheduled']}, conditional: {result['conditional']})")
        sys.exit(0)

    elif args.mode == "http":
        # Run HTTP server
        run_http_server(port=args.port)

    else:
        # Run as continuous worker
        executor = TaskExecutor()
        try:
            executor.run_forever(interval_seconds=args.interval)
        except KeyboardInterrupt:
            logger.info("Shutting down task executor")
            executor.stop()
