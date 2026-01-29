"""
Scheduler Manager - Handles creation, storage, and execution of scheduled tasks.

This module provides:
- Task CRUD operations (create, read, update, delete)
- Cron expression parsing and next run calculation
- Natural language time parsing
- Mock mode for demo/testing

In production, tasks would be stored in Supabase and executed by a background worker.
For demo purposes, we use session state storage with mock execution.
"""

import json
import uuid
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from croniter import croniter

# Check if we're in demo/mock mode (no Supabase connection)
DEMO_MODE = False  # Using Supabase for persistent task storage


class SchedulerManager:
    """Manages scheduled tasks - creation, storage, retrieval, and execution"""

    # Common cron patterns for user convenience
    CRON_PATTERNS = {
        "daily": "0 9 * * *",           # 9am daily
        "weekly": "0 9 * * 1",          # 9am Monday
        "biweekly": "0 9 * * 1/2",      # Every other Monday
        "monthly": "0 9 1 * *",         # 9am on the 1st
        "weekdays": "0 9 * * 1-5",      # 9am Mon-Fri
    }

    @staticmethod
    def _get_storage_key(user_id: str) -> str:
        """Get session state key for user's tasks"""
        return f"_scheduled_tasks_{user_id}"

    @staticmethod
    def _get_runs_key(user_id: str) -> str:
        """Get session state key for task runs history"""
        return f"_task_runs_{user_id}"

    @staticmethod
    def _parse_natural_time(time_str: str) -> Optional[datetime]:
        """
        Parse natural language time expressions.

        Supports:
        - "tomorrow 9am"
        - "next Monday"
        - "in 2 hours"
        - "Friday at 5pm"
        - ISO format "2024-01-15T09:00:00"
        """
        if not time_str:
            return None

        time_str = time_str.lower().strip()
        now = datetime.now()

        # Try ISO format first
        try:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Tomorrow
        if "tomorrow" in time_str:
            base = now + timedelta(days=1)
            # Extract time if specified
            if "am" in time_str or "pm" in time_str:
                hour = SchedulerManager._extract_hour(time_str)
                return base.replace(hour=hour, minute=0, second=0, microsecond=0)
            return base.replace(hour=9, minute=0, second=0, microsecond=0)

        # Next [weekday]
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(weekdays):
            if day in time_str:
                days_ahead = i - now.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                base = now + timedelta(days=days_ahead)
                hour = SchedulerManager._extract_hour(time_str) if ("am" in time_str or "pm" in time_str) else 9
                return base.replace(hour=hour, minute=0, second=0, microsecond=0)

        # In X hours/days
        if "in " in time_str:
            parts = time_str.split()
            try:
                amount = int(parts[1])
                if "hour" in time_str:
                    return now + timedelta(hours=amount)
                if "day" in time_str:
                    return now + timedelta(days=amount)
                if "week" in time_str:
                    return now + timedelta(weeks=amount)
            except (ValueError, IndexError):
                pass

        # Default: try to parse as date
        return None

    @staticmethod
    def _extract_hour(time_str: str) -> int:
        """Extract hour from time string like '9am' or '5pm'"""
        import re
        match = re.search(r'(\d{1,2})\s*(am|pm)', time_str.lower())
        if match:
            hour = int(match.group(1))
            if match.group(2) == "pm" and hour != 12:
                hour += 12
            elif match.group(2) == "am" and hour == 12:
                hour = 0
            return hour
        return 9  # Default to 9am

    @staticmethod
    def _parse_cron_or_natural(schedule_type: str, cron_expression: Optional[str], schedule_time: Optional[str]) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Parse schedule configuration into cron expression and next run time.

        Returns:
            Tuple of (cron_expression, next_run_at)
        """
        if schedule_type == "once":
            next_run = SchedulerManager._parse_natural_time(schedule_time)
            if not next_run:
                # Default to 1 hour from now
                next_run = datetime.now() + timedelta(hours=1)
            return None, next_run

        elif schedule_type == "recurring":
            # Check for natural language patterns
            if cron_expression:
                cron = cron_expression
                # Check if it's a named pattern
                if cron.lower() in SchedulerManager.CRON_PATTERNS:
                    cron = SchedulerManager.CRON_PATTERNS[cron.lower()]
            elif schedule_time:
                # Try to infer cron from natural language
                time_lower = schedule_time.lower()
                if "daily" in time_lower:
                    cron = SchedulerManager.CRON_PATTERNS["daily"]
                elif "weekly" in time_lower or "every week" in time_lower:
                    cron = SchedulerManager.CRON_PATTERNS["weekly"]
                elif "monthly" in time_lower or "every month" in time_lower:
                    cron = SchedulerManager.CRON_PATTERNS["monthly"]
                elif "weekday" in time_lower:
                    cron = SchedulerManager.CRON_PATTERNS["weekdays"]
                else:
                    cron = SchedulerManager.CRON_PATTERNS["weekly"]  # Default
            else:
                cron = SchedulerManager.CRON_PATTERNS["weekly"]

            # Calculate next run
            try:
                cron_iter = croniter(cron, datetime.now())
                next_run = cron_iter.get_next(datetime)
            except Exception:
                next_run = datetime.now() + timedelta(days=7)

            return cron, next_run

        elif schedule_type == "conditional":
            # Conditional tasks don't have a fixed schedule
            return None, None

        return None, None

    @staticmethod
    def create_task(
        user_id: str,
        task_type: str,
        task_params: Dict[str, Any],
        schedule_type: str = "once",
        schedule_time: Optional[str] = None,
        cron_expression: Optional[str] = None,
        description: Optional[str] = None,
        max_runs: Optional[int] = None,
        condition_type: Optional[str] = None,
        condition_value: Optional[float] = None,
        condition_asset: Optional[str] = None
    ) -> str:
        """
        Create a new scheduled task.

        In demo mode, stores in session state.
        In production, would store in Supabase.
        """
        # Parse schedule
        cron, next_run = SchedulerManager._parse_cron_or_natural(
            schedule_type, cron_expression, schedule_time
        )

        # Generate task
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "user_id": user_id,
            "task_type": task_type,
            "task_params": task_params,
            "description": description or f"{task_type} task",
            "schedule_type": schedule_type,
            "cron_expression": cron,
            "next_run_at": next_run.isoformat() if next_run else None,
            "condition_type": condition_type,
            "condition_value": condition_value,
            "condition_asset": condition_asset,
            "status": "active",
            "run_count": 0,
            "max_runs": max_runs,
            "created_at": datetime.now().isoformat(),
            "last_run_at": None,
            "consecutive_failures": 0
        }

        if DEMO_MODE:
            # Store in session state (fallback)
            storage_key = SchedulerManager._get_storage_key(user_id)
            if storage_key not in st.session_state:
                st.session_state[storage_key] = []
            st.session_state[storage_key].append(task)
        else:
            # Store in Supabase
            from supabase_client import get_supabase_client
            try:
                supabase = get_supabase_client(use_service_key=True)
                if supabase:
                    # Convert task_params to JSON string for storage
                    db_task = task.copy()
                    db_task["task_params"] = json.dumps(task_params)
                    supabase.table("scheduled_tasks").insert(db_task).execute()
            except Exception as e:
                # Fallback to session state
                storage_key = SchedulerManager._get_storage_key(user_id)
                if storage_key not in st.session_state:
                    st.session_state[storage_key] = []
                st.session_state[storage_key].append(task)

        # Build response
        response = f"**Scheduled task created**\n\n"
        response += f"- **ID:** `{task_id[:8]}`\n"
        response += f"- **Type:** {task_type}\n"
        response += f"- **Description:** {description}\n"

        if schedule_type == "once" and next_run:
            response += f"- **Scheduled for:** {next_run.strftime('%B %d, %Y at %I:%M %p')}\n"
        elif schedule_type == "recurring" and cron:
            response += f"- **Schedule:** `{cron}`\n"
            if next_run:
                response += f"- **Next run:** {next_run.strftime('%B %d, %Y at %I:%M %p')}\n"
            if max_runs:
                response += f"- **Max runs:** {max_runs}\n"
        elif schedule_type == "conditional":
            response += f"- **Trigger:** {condition_asset} {condition_type.replace('_', ' ')} ${condition_value}\n"

        return response

    @staticmethod
    def get_user_tasks(user_id: str, status: str = "active") -> List[Dict[str, Any]]:
        """Get all tasks for a user, optionally filtered by status"""
        if DEMO_MODE:
            storage_key = SchedulerManager._get_storage_key(user_id)
            tasks = st.session_state.get(storage_key, [])

            if status == "all":
                return tasks
            return [t for t in tasks if t.get("status") == status]
        else:
            # Fetch from Supabase
            from supabase_client import get_supabase_client
            try:
                supabase = get_supabase_client(use_service_key=True)
                if not supabase:
                    return []

                query = supabase.table("scheduled_tasks").select("*").eq("user_id", user_id)
                if status != "all":
                    query = query.eq("status", status)

                result = query.order("created_at", desc=True).execute()
                tasks = result.data if result.data else []

                # Parse task_params from JSON
                for task in tasks:
                    if isinstance(task.get("task_params"), str):
                        try:
                            task["task_params"] = json.loads(task["task_params"])
                        except json.JSONDecodeError:
                            pass
                return tasks
            except Exception:
                return []

    @staticmethod
    def update_task_status(user_id: str, task_id: str, new_status: str) -> str:
        """Update task status (active, paused, completed, cancelled)"""
        if DEMO_MODE:
            storage_key = SchedulerManager._get_storage_key(user_id)
            tasks = st.session_state.get(storage_key, [])

            for task in tasks:
                if task["id"].startswith(task_id):
                    old_status = task["status"]
                    task["status"] = new_status
                    task["updated_at"] = datetime.now().isoformat()

                    if new_status == "active" and task.get("cron_expression"):
                        try:
                            cron_iter = croniter(task["cron_expression"], datetime.now())
                            task["next_run_at"] = cron_iter.get_next(datetime).isoformat()
                        except Exception:
                            pass

                    return f"Task `{task_id[:8]}` status changed from {old_status} to {new_status}"

            return f"Task `{task_id}` not found"
        else:
            # Update in Supabase
            from supabase_client import get_supabase_client
            try:
                supabase = get_supabase_client(use_service_key=True)
                if not supabase:
                    return "Database connection failed"

                # Find task by partial ID
                result = supabase.table("scheduled_tasks").select("id, status, cron_expression").eq(
                    "user_id", user_id
                ).ilike("id", f"{task_id}%").execute()

                if not result.data:
                    return f"Task `{task_id}` not found"

                task = result.data[0]
                old_status = task["status"]

                updates = {
                    "status": new_status,
                    "updated_at": datetime.now().isoformat()
                }

                # Recalculate next run if resuming
                if new_status == "active" and task.get("cron_expression"):
                    try:
                        cron_iter = croniter(task["cron_expression"], datetime.now())
                        updates["next_run_at"] = cron_iter.get_next(datetime).isoformat()
                    except Exception:
                        pass

                supabase.table("scheduled_tasks").update(updates).eq("id", task["id"]).execute()
                return f"Task `{task_id[:8]}` status changed from {old_status} to {new_status}"

            except Exception as e:
                return f"Failed to update task: {str(e)}"

    @staticmethod
    def delete_task(user_id: str, task_id: str) -> str:
        """Delete a scheduled task"""
        if DEMO_MODE:
            storage_key = SchedulerManager._get_storage_key(user_id)
            tasks = st.session_state.get(storage_key, [])

            for i, task in enumerate(tasks):
                if task["id"].startswith(task_id):
                    deleted_task = tasks.pop(i)
                    st.session_state[storage_key] = tasks
                    return f"Cancelled task `{task_id[:8]}`: {deleted_task.get('description', 'No description')}"

            return f"Task `{task_id}` not found"
        else:
            # Delete from Supabase
            from supabase_client import get_supabase_client
            try:
                supabase = get_supabase_client(use_service_key=True)
                if not supabase:
                    return "Database connection failed"

                # Find task by partial ID
                result = supabase.table("scheduled_tasks").select("id, description").eq(
                    "user_id", user_id
                ).ilike("id", f"{task_id}%").execute()

                if not result.data:
                    return f"Task `{task_id}` not found"

                task = result.data[0]
                supabase.table("scheduled_tasks").delete().eq("id", task["id"]).execute()
                return f"Cancelled task `{task_id[:8]}`: {task.get('description', 'No description')}"

            except Exception as e:
                return f"Failed to delete task: {str(e)}"

    @staticmethod
    def get_task_runs(user_id: str, task_id: str, limit: int = 5) -> str:
        """Get execution history for a task"""
        if DEMO_MODE:
            runs_key = SchedulerManager._get_runs_key(user_id)
            all_runs = st.session_state.get(runs_key, [])

            task_runs = [r for r in all_runs if r.get("task_id", "").startswith(task_id)]
            task_runs = sorted(task_runs, key=lambda x: x.get("started_at", ""), reverse=True)[:limit]

            if not task_runs:
                return f"No execution history for task `{task_id[:8]}`. Task hasn't run yet."

            result = f"**Execution history for task `{task_id[:8]}`:**\n\n"
            for run in task_runs:
                status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(run.get("status"), "⚪")
                started = run.get("started_at", "Unknown")
                result += f"{status_emoji} {started}\n"
                if run.get("error_message"):
                    result += f"   Error: {run['error_message']}\n"
                if run.get("tx_hash"):
                    result += f"   TX: `{run['tx_hash'][:16]}...`\n"
                result += "\n"

            return result
        else:
            # Fetch from Supabase
            from supabase_client import get_supabase_client
            try:
                supabase = get_supabase_client(use_service_key=True)
                if not supabase:
                    return "Database connection failed"

                # Find task runs by partial task ID
                result = supabase.table("task_runs").select("*").eq(
                    "user_id", user_id
                ).ilike("task_id", f"{task_id}%").order(
                    "started_at", desc=True
                ).limit(limit).execute()

                task_runs = result.data if result.data else []

                if not task_runs:
                    return f"No execution history for task `{task_id[:8]}`. Task hasn't run yet."

                output = f"**Execution history for task `{task_id[:8]}`:**\n\n"
                for run in task_runs:
                    status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(run.get("status"), "⚪")
                    started = run.get("started_at", "Unknown")
                    output += f"{status_emoji} {started}\n"
                    if run.get("error_message"):
                        output += f"   Error: {run['error_message']}\n"
                    if run.get("tx_hash"):
                        output += f"   TX: `{run['tx_hash'][:16]}...`\n"
                    output += "\n"

                return output

            except Exception as e:
                return f"Failed to fetch task history: {str(e)}"

    @staticmethod
    def simulate_task_execution(user_id: str, task_id: str) -> str:
        """
        Simulate executing a task (for demo purposes).

        In production, this would be called by the background worker.
        """
        if DEMO_MODE:
            storage_key = SchedulerManager._get_storage_key(user_id)
            runs_key = SchedulerManager._get_runs_key(user_id)
            tasks = st.session_state.get(storage_key, [])

            for task in tasks:
                if task["id"].startswith(task_id):
                    # Create a mock run record
                    run = {
                        "id": str(uuid.uuid4()),
                        "task_id": task["id"],
                        "started_at": datetime.now().isoformat(),
                        "completed_at": datetime.now().isoformat(),
                        "status": "success",  # In demo, always succeeds
                        "result": {"simulated": True},
                        "triggered_by": "manual_demo",
                        "execution_time_ms": 150
                    }

                    # Add mock tx hash for transfers
                    if task["task_type"] == "transfer":
                        run["tx_hash"] = f"0x{''.join(['abcdef0123456789'[i % 16] for i in range(64)])}"

                    # Store run
                    if runs_key not in st.session_state:
                        st.session_state[runs_key] = []
                    st.session_state[runs_key].append(run)

                    # Update task
                    task["run_count"] = task.get("run_count", 0) + 1
                    task["last_run_at"] = datetime.now().isoformat()

                    # Calculate next run for recurring
                    if task.get("cron_expression"):
                        try:
                            cron_iter = croniter(task["cron_expression"], datetime.now())
                            task["next_run_at"] = cron_iter.get_next(datetime).isoformat()
                        except Exception:
                            pass

                    # Check if completed (max runs reached)
                    if task.get("max_runs") and task["run_count"] >= task["max_runs"]:
                        task["status"] = "completed"

                    return f"✅ Simulated execution of task `{task_id[:8]}`: {task.get('description', '')}"

            return f"Task `{task_id}` not found"
        else:
            return "Not available in production mode"
