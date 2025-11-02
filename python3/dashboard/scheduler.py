"""
Task scheduler for dashboard data refresh
"""

import threading
import time
import uuid
import os
from typing import Dict, Any, Optional, Callable
from .utils import parse_interval, get_platform_temp_dir, format_error_message
from .config import ConfigManager
from .database.base import DatabaseManager
from .charts.base import ChartRenderer


class DashboardTask:
    """Represents a single dashboard task."""
    
    def __init__(self, task_id: str, config_file: str, config: Dict[str, Any]):
        self.task_id = task_id
        self.config_file = config_file
        self.config = config
        self.interval = parse_interval(config.get('interval', '30s'))
        self.last_run = 0
        self.next_run = 0
        self.is_running = False
        self.error_count = 0
        self.last_error = None
        self.temp_file = None
        self.last_countdown_update = 0  # Track last countdown update time

        # Initialize components
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()
        
    def should_run(self) -> bool:
        """Check if task should run based on interval."""
        current_time = time.time()
        return (current_time - self.last_run) >= self.interval
    
    def get_remaining_time(self) -> int:
        """Get remaining time until next refresh in seconds."""
        current_time = time.time()

        # If task is currently running, show "Refreshing..."
        if self.is_running:
            return 0

        # If never run before, calculate from creation time
        if self.last_run == 0:
            # Use current time as reference for countdown
            elapsed = 0
        else:
            elapsed = current_time - self.last_run

        remaining = max(0, self.interval - elapsed)
        return int(remaining)

    def get_countdown_display(self) -> str:
        """Get formatted countdown display string."""
        remaining = self.get_remaining_time()

        if remaining == 0:
            return "Refreshing..."

        # Format as MM:SS or HH:MM:SS
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def should_update_countdown(self) -> bool:
        """Check if countdown should be updated (every 10 seconds)."""
        current_time = time.time()
        return (current_time - self.last_countdown_update) >= 10

    def update_countdown_display(self) -> bool:
        """Update countdown display in temp file without re-executing query."""
        if not self.should_update_countdown():
            return False

        try:
            temp_file = self.get_temp_file_path()
            if not os.path.exists(temp_file):
                return False

            # Read current file content
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get current countdown info
            config_with_countdown = self.config.copy()
            config_with_countdown['_countdown_info'] = {
                'remaining_time': self.get_remaining_time(),
                'countdown_display': self.get_countdown_display(),
                'interval': self.interval,
                'last_run': self.last_run
            }

            # Re-render with updated countdown (reuse last data if available)
            show_config = self.config.get('show', {})
            chart_type = show_config.get('type', 'table')

            # Try to extract data from existing content or use empty data
            # This is a simplified approach - in a real implementation,
            # we might want to cache the last query result
            try:
                # For now, we'll just update the countdown in the existing content
                # by replacing the countdown pattern
                import re

                # Pattern to match countdown display
                countdown_pattern = r'Next refresh: \d{1,2}:\d{2}(:\d{2})?|Next refresh: Refreshing\.\.\.'
                new_countdown = f"Next refresh: {self.get_countdown_display()}"

                if re.search(countdown_pattern, content):
                    updated_content = re.sub(countdown_pattern, new_countdown, content)

                    # Write updated content back to file
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

                    self.last_countdown_update = time.time()
                    return True

            except Exception:
                # If pattern matching fails, fall back to not updating
                pass

            return False

        except Exception as e:
            # Ignore countdown update errors
            return False

    def get_temp_file_path(self) -> str:
        """Get or create temp file path for this task."""
        if not self.temp_file:
            temp_dir = get_platform_temp_dir()
            os.makedirs(temp_dir, exist_ok=True)
            # Extract filename from config file path and use it for temp file
            config_filename = os.path.splitext(os.path.basename(self.config_file))[0]
            self.temp_file = os.path.join(temp_dir, f"{config_filename}.dashboard")
        return self.temp_file
    
    def execute(self) -> bool:
        """Execute the dashboard task."""
        if self.is_running:
            return False
        
        self.is_running = True
        success = False
        connection = None
        db_url = None

        try:
            # Get database connection
            db_config = self.config.get('database', {})
            db_url = db_config.get('url')
            if not db_url:
                raise ValueError("Database URL not configured")

            connection = self.db_manager.get_connection(db_url)

            # Execute query
            query = self.config.get('query')
            if not query:
                raise ValueError("Query not configured")

            data = connection.execute_query(query)

            # Render chart
            show_config = self.config.get('show', {})
            chart_type = show_config.get('type', 'table')

            # Add countdown information to config
            config_with_countdown = self.config.copy()
            config_with_countdown['_countdown_info'] = {
                'remaining_time': self.get_remaining_time(),
                'countdown_display': self.get_countdown_display(),
                'interval': self.interval,
                'last_run': self.last_run
            }

            chart_content = ChartRenderer.render_chart(chart_type, data, config_with_countdown)

            # Write to temp file
            temp_file = self.get_temp_file_path()
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(chart_content)

            # Update status
            self.last_run = time.time()
            self.error_count = 0
            self.last_error = None
            success = True

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)

            # Write error to temp file
            error_content = format_error_message(e, "Dashboard Task")
            temp_file = self.get_temp_file_path()
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(error_content)

        finally:
            # Always return connection to pool and mark task as not running
            if connection and db_url:
                try:
                    self.db_manager.connection_pool.return_connection(db_url, connection)
                except Exception:
                    pass  # Ignore connection return errors
            self.is_running = False
        
        return success
    
    def cleanup(self):
        """Clean up task resources."""
        # Clean up database connections
        try:
            db_config = self.config.get('database', {})
            db_url = db_config.get('url')
            if db_url:
                self.db_manager.connection_pool.cleanup_idle_connections(db_url)
        except Exception:
            pass  # Ignore cleanup errors

        # Clean up temp file
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass  # Ignore cleanup errors


class DashboardScheduler:
    """Scheduler for managing dashboard tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, DashboardTask] = {}
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.Lock()
        
    def add_task(self, config_file: str, config: Dict[str, Any]) -> str:
        """Add a new dashboard task."""
        task_id = str(uuid.uuid4())
        
        with self.lock:
            task = DashboardTask(task_id, config_file, config)
            self.tasks[task_id] = task
            
            # Execute immediately for the first time
            task.execute()
        
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a dashboard task."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.cleanup()
                del self.tasks[task_id]
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[DashboardTask]:
        """Get a task by ID."""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_task_by_config_file(self, config_file: str) -> Optional[DashboardTask]:
        """Get a task by config file path."""
        with self.lock:
            for task in self.tasks.values():
                if task.config_file == config_file:
                    return task
        return None
    
    def restart_task(self, task_id: str) -> bool:
        """Restart a specific task (execute immediately)."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                return task.execute()
        return False
    
    def restart_task_by_config_file(self, config_file: str) -> bool:
        """Restart task by config file path."""
        task = self.get_task_by_config_file(config_file)
        if task:
            return task.execute()
        return False
    
    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """List all tasks with their status."""
        with self.lock:
            result = {}
            for task_id, task in self.tasks.items():
                result[task_id] = {
                    'config_file': task.config_file,
                    'interval': task.interval,
                    'last_run': task.last_run,
                    'is_running': task.is_running,
                    'error_count': task.error_count,
                    'last_error': task.last_error,
                    'temp_file': task.temp_file,
                    'remaining_time': task.get_remaining_time(),
                    'countdown_display': task.get_countdown_display()
                }
            return result
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # Cleanup all tasks
        with self.lock:
            for task in self.tasks.values():
                task.cleanup()
            self.tasks.clear()
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                # Check all tasks for execution and countdown updates
                tasks_to_run = []
                tasks_to_update_countdown = []

                with self.lock:
                    for task in self.tasks.values():
                        # Check if task should run
                        if task.should_run() and not task.is_running:
                            tasks_to_run.append(task)
                        # Check if countdown should be updated
                        elif task.should_update_countdown():
                            tasks_to_update_countdown.append(task)

                # Execute tasks (outside of lock to avoid blocking)
                for task in tasks_to_run:
                    try:
                        task.execute()
                    except Exception as e:
                        # Log error but continue with other tasks
                        print(f"Error executing task {task.task_id}: {e}")

                # Update countdown displays (outside of lock to avoid blocking)
                for task in tasks_to_update_countdown:
                    try:
                        task.update_countdown_display()
                    except Exception as e:
                        # Log error but continue with other tasks
                        print(f"Error updating countdown for task {task.task_id}: {e}")
                
                # Sleep for a short interval
                time.sleep(1)
                
            except Exception as e:
                # Log scheduler error but continue
                print(f"Scheduler error: {e}")
                time.sleep(5)  # Wait longer on error


# Global scheduler instance
_scheduler = None


def get_scheduler() -> DashboardScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DashboardScheduler()
        _scheduler.start()
    return _scheduler


def cleanup_scheduler():
    """Cleanup the global scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None