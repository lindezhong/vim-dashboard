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
        # Get interval from show.interval (new format) or fallback to interval (old format)
        show_config = config.get('show', {})
        interval_str = show_config.get('interval') or config.get('interval', '30s')
        self.interval = parse_interval(interval_str)
        self.last_run = 0
        self.next_run = 0
        self.is_running = False
        self.error_count = 0
        self.last_error = None
        self.temp_file = None
        self.last_countdown_update = 0  # Track last countdown update time
        self._creation_time = time.time()  # Track task creation time for countdown

        # Variables management for template engine
        self.runtime_variables = {}  # Runtime variable overrides
        self.variables_info = {}  # Variables metadata for display

        # Initialize components
        self.db_manager = DatabaseManager()
        self.config_manager = ConfigManager()

        # Load initial variables info
        self._load_variables_info()

    def _load_variables_info(self):
        """Load variables information from config for display."""
        query_config = self.config.get('query', {})
        args = query_config.get('args', [])

        self.variables_info = {}
        for arg in args:
            var_name = arg.get('name') or arg.get('key')
            if var_name:
                self.variables_info[var_name] = {
                    'type': arg.get('type', 'string'),
                    'default_value': arg.get('default'),
                    'current_value': self.runtime_variables.get(var_name, arg.get('default')),
                    'description': arg.get('description', '')
                }

    def update_variable(self, var_name: str, new_value: Any) -> bool:
        """Update a runtime variable value."""
        if var_name not in self.variables_info:
            return False

        # Type conversion based on variable type
        var_type = self.variables_info[var_name]['type']
        try:
            if var_type == 'number':
                new_value = float(new_value) if '.' in str(new_value) else int(new_value)
            elif var_type == 'boolean':
                new_value = str(new_value).lower() in ('true', '1', 'yes', 'on')
            elif var_type == 'list':
                if isinstance(new_value, str):
                    # Parse comma-separated values
                    new_value = [item.strip() for item in new_value.split(',')]
            elif var_type == 'map':
                if isinstance(new_value, str):
                    # Simple key=value parsing (basic implementation)
                    new_value = dict(item.split('=', 1) for item in new_value.split(',') if '=' in item)
            # string type needs no conversion

            self.runtime_variables[var_name] = new_value
            self.variables_info[var_name]['current_value'] = new_value
            return True

        except (ValueError, TypeError) as e:
            self.last_error = f"Invalid value for variable '{var_name}': {e}"
            return False

    def get_variables_info(self) -> Dict[str, Any]:
        """Get current variables information for display."""
        return self.variables_info.copy()

    def reset_variables(self):
        """Reset all variables to their default values."""
        self.runtime_variables.clear()
        for var_name, var_info in self.variables_info.items():
            var_info['current_value'] = var_info['default_value']

    def should_run(self) -> bool:
        """Check if task should run based on interval."""
        current_time = time.time()

        # If never run before, check against creation time
        if self.last_run == 0:
            return (current_time - self._creation_time) >= self.interval

        return (current_time - self.last_run) >= self.interval
    
    def get_remaining_time(self) -> int:
        """Get remaining time until next refresh in seconds."""
        current_time = time.time()

        # If task is currently running, show "Refreshing..."
        if self.is_running:
            return 0

        # If never run before, calculate from task creation time
        if self.last_run == 0:
            # Initialize last_run to current time for countdown calculation
            if not hasattr(self, '_creation_time'):
                self._creation_time = current_time
            elapsed = current_time - self._creation_time
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

            # Load and process configuration with template engine
            self.config_manager.load_config(self.config_file)

            # Apply runtime variable overrides to template processor
            if self.runtime_variables:
                self.config_manager.template_processor.set_runtime_overrides(self.runtime_variables)

            # Get rendered SQL query (with template processing if needed)
            query = self.config_manager.get_query()
            if not query:
                raise ValueError("SQL query not found in configuration")

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

            # Add variables information to config for display
            if self.variables_info:
                config_with_countdown['_variables_info'] = self.get_variables_info()

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
    
    def update_variable(self, task_id: str, var_name: str, new_value: Any) -> bool:
        """Update a variable for a specific task and trigger refresh."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.update_variable(var_name, new_value):
                    # Trigger immediate refresh after variable update
                    return task.execute()
        return False

    def update_variable_by_config_file(self, config_file: str, var_name: str, new_value: Any) -> bool:
        """Update a variable by config file path and trigger refresh."""
        task = self.get_task_by_config_file(config_file)
        if task:
            if task.update_variable(var_name, new_value):
                # Trigger immediate refresh after variable update
                return task.execute()
        return False

    def get_variables_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get variables information for a specific task."""
        with self.lock:
            if task_id in self.tasks:
                return self.tasks[task_id].get_variables_info()
        return None

    def get_variables_info_by_config_file(self, config_file: str) -> Optional[Dict[str, Any]]:
        """Get variables information by config file path."""
        task = self.get_task_by_config_file(config_file)
        if task:
            return task.get_variables_info()
        return None

    def reset_variables(self, task_id: str) -> bool:
        """Reset all variables to default values for a specific task."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.reset_variables()
                # Trigger immediate refresh after reset
                return task.execute()
        return False

    def reset_variables_by_config_file(self, config_file: str) -> bool:
        """Reset all variables to default values by config file path."""
        task = self.get_task_by_config_file(config_file)
        if task:
            task.reset_variables()
            # Trigger immediate refresh after reset
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
                        # Check if countdown should be updated (independent of task execution)
                        if task.should_update_countdown():
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