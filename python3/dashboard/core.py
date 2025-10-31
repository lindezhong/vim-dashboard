"""
Core dashboard functionality
"""

import os
import sys
from typing import Optional, Dict, Any, List

# Try to import vim module, but don't fail if it's not available
# (e.g., during installation verification)
try:
    import vim
    VIM_AVAILABLE = True
except ImportError:
    VIM_AVAILABLE = False
    # Create a mock vim module for testing purposes
    class MockVim:
        class current:
            class buffer:
                name = ""
            class window:
                cursor = (1, 0)
        class vars:
            @staticmethod
            def get(key, default=None):
                return default
        @staticmethod
        def command(cmd):
            pass
    vim = MockVim()
from .config import ConfigManager
from .scheduler import get_scheduler, cleanup_scheduler
from .utils import get_platform_config_dir, format_error_message


class DashboardCore:
    """Core dashboard functionality."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.scheduler = get_scheduler()

    def start_dashboard(self, config_file: str) -> bool:
        """Start dashboard with specified config file."""
        try:
            # Normalize and validate config file path
            config_file = os.path.abspath(config_file)

            if not os.path.exists(config_file):
                # Use vim's shellescape() to safely handle paths with special characters
                vim.command('echohl ErrorMsg')
                vim.command('echo "Config file not found: " . shellescape(' + repr(config_file) + ')')
                vim.command('echohl None')
                return False

            # Load and validate configuration
            config = self.config_manager.load_config(config_file)
            if not config:
                vim.command('echohl ErrorMsg')
                vim.command('echo "Failed to load configuration"')
                vim.command('echohl None')
                return False

            # Check if task already exists for this config file
            existing_task = self.scheduler.get_task_by_config_file(config_file)
            if existing_task:
                # Use vim's shellescape() to safely handle paths with special characters
                vim.command('echohl WarningMsg')
                vim.command('echo "Dashboard already running for: " . shellescape(' + repr(config_file) + ')')
                vim.command('echohl None')

                # Open existing temp file
                temp_file = existing_task.get_temp_file_path()
                if os.path.exists(temp_file):
                    vim.command(f'edit {temp_file}')
                return True

            # Add task to scheduler
            task_id = self.scheduler.add_task(config_file, config)
            if not task_id:
                vim.command('echohl ErrorMsg')
                vim.command('echo "Failed to start dashboard task"')
                vim.command('echohl None')
                return False

            # Get task and open temp file
            task = self.scheduler.get_task(task_id)
            if task:
                temp_file = task.get_temp_file_path()
                vim.command(f'edit {temp_file}')

                # Use vim's shellescape() to safely handle paths with special characters
                vim.command('echohl MoreMsg')
                vim.command('echo "Dashboard started: " . shellescape(' + repr(config_file) + ')')
                vim.command('echohl None')
                return True

            return False

        except Exception as e:
            error_msg = format_error_message(e, "Dashboard Start")
            vim.command('echohl ErrorMsg')
            vim.command('echo "' + error_msg.replace('"', '\\"') + '"')
            vim.command('echohl None')
            return False

    def restart_dashboard(self) -> bool:
        """Restart current dashboard (refresh data)."""
        try:
            # Get current buffer file path
            current_file = vim.current.buffer.name
            if not current_file:
                vim.command('echohl ErrorMsg | echo "No active dashboard buffer" | echohl None')
                return False

            # Find task by temp file
            tasks = self.scheduler.list_tasks()
            target_task_id = None

            for task_id, task_info in tasks.items():
                if task_info['temp_file'] == current_file:
                    target_task_id = task_id
                    break

            if not target_task_id:
                vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
                return False

            # Restart the task
            success = self.scheduler.restart_task(target_task_id)
            if success:
                # Reload the buffer
                vim.command('edit!')
                vim.command('echohl MoreMsg | echo "Dashboard refreshed" | echohl None')
                return True
            else:
                vim.command('echohl ErrorMsg | echo "Failed to refresh dashboard" | echohl None')
                return False

        except Exception as e:
            error_msg = format_error_message(e, "Dashboard Restart")
            vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')
            return False

    def stop_dashboard(self, config_file: Optional[str] = None) -> bool:
        """Stop dashboard task."""
        try:
            if config_file:
                # Stop specific config file
                config_file = os.path.abspath(config_file)
                task = self.scheduler.get_task_by_config_file(config_file)
                if task:
                    success = self.scheduler.remove_task(task.task_id)
                    if success:
                        # Use vim's shellescape() to safely handle paths with special characters
                        vim.command('echohl MoreMsg')
                        vim.command('echo "Dashboard stopped: " . shellescape(' + repr(config_file) + ')')
                        vim.command('echohl None')
                        return True
                    else:
                        # Use vim's shellescape() to safely handle paths with special characters
                        vim.command('echohl ErrorMsg')
                        vim.command('echo "Failed to stop dashboard: " . shellescape(' + repr(config_file) + ')')
                        vim.command('echohl None')
                        return False
                else:
                    # Use vim's shellescape() to safely handle paths with special characters
                    vim.command('echohl WarningMsg')
                    vim.command('echo "No running dashboard for: " . shellescape(' + repr(config_file) + ')')
                    vim.command('echohl None')
                    return False
            else:
                # Stop current buffer's dashboard
                current_file = vim.current.buffer.name
                if not current_file:
                    vim.command('echohl ErrorMsg | echo "No active dashboard buffer" | echohl None')
                    return False
                
                # Find and stop task
                tasks = self.scheduler.list_tasks()
                for task_id, task_info in tasks.items():
                    if task_info['temp_file'] == current_file:
                        success = self.scheduler.remove_task(task_id)
                        if success:
                            vim.command('echohl MoreMsg | echo "Dashboard stopped" | echohl None')
                            return True
                        break
                
                vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
                return False
                
        except Exception as e:
            error_msg = format_error_message(e, "Dashboard Stop")
            vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')
            return False
    
    def list_dashboards(self) -> bool:
        """List all running dashboards."""
        try:
            tasks = self.scheduler.list_tasks()
            if not tasks:
                vim.command('echohl MoreMsg | echo "No running dashboards" | echohl None')
                return True
            
            # Create status display
            lines = ["Running Dashboards:", ""]
            for task_id, task_info in tasks.items():
                config_file = task_info['config_file']
                status = "Running" if task_info['is_running'] else "Idle"
                error_info = f" (Errors: {task_info['error_count']})" if task_info['error_count'] > 0 else ""
                lines.append(f"  {config_file} - {status}{error_info}")
            
            # Display in new buffer
            vim.command('new')
            vim.current.buffer[:] = lines
            vim.command('setlocal buftype=nofile')
            vim.command('setlocal noswapfile')
            vim.command('setlocal readonly')
            
            return True
            
        except Exception as e:
            error_msg = format_error_message(e, "Dashboard List")
            vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')
            return False
    
    def open_dashboard_browser(self) -> bool:
        """Open dashboard configuration browser."""
        try:
            dashboard_dir = get_platform_config_dir()

            # Create dashboard directory if it doesn't exist
            if not os.path.exists(dashboard_dir):
                os.makedirs(dashboard_dir, exist_ok=True)
                # Create a sample config file
                sample_config = """# Sample Dashboard Configuration
database:
  type: sqlite
  url: sqlite:///sample.db
query: "SELECT 'Hello' as message, 'World' as target"
interval: 30s
show:
  type: table
  column_list:
    - column: message
      alias: Message
    - column: target
      alias: Target
"""
                sample_file = os.path.join(dashboard_dir, "sample.yaml")
                with open(sample_file, 'w', encoding='utf-8') as f:
                    f.write(sample_config)
            
            # Get all YAML files in dashboard directory
            config_files = []
            for file in os.listdir(dashboard_dir):
                if file.endswith(('.yaml', '.yml')):
                    config_files.append(file)
            
            if not config_files:
                # Use vim's shellescape() to safely handle paths with special characters
                vim.command('echohl WarningMsg')
                vim.command('echo "No config files found in " . shellescape(' + repr(dashboard_dir) + ')')
                vim.command('echohl None')
                vim.command(f'edit {dashboard_dir}')
                return True
            
            # Create browser buffer
            vim.command('new')
            vim.command('setlocal buftype=nofile')
            vim.command('setlocal noswapfile')
            vim.command('setlocal cursorline')
            
            # Set buffer content
            lines = [
                "Dashboard Configuration Browser",
                f"Directory: {dashboard_dir}",
                "",
                "Press <Enter> to open selected config",
                "Press 'q' to quit",
                ""
            ]
            
            for i, config_file in enumerate(config_files, 1):
                full_path = os.path.join(dashboard_dir, config_file)
                lines.append(f"{i:2d}. {config_file}")
            
            vim.current.buffer[:] = lines
            
            # Set up key mappings
            vim.command('nnoremap <buffer> <CR> :python3 import dashboard.core; dashboard.core.dashboard_open_selected()<CR>')
            vim.command('nnoremap <buffer> q :quit<CR>')
            
            # Store config files for selection
            # Escape special characters in paths for vim
            escaped_dir = dashboard_dir.replace('\\', '\\\\').replace('"', '\\"')

            # Convert Python list to vim list format
            vim_list = '[' + ','.join(f'"{f}"' for f in config_files) + ']'

            vim.command(f'let g:dashboard_config_files = {vim_list}')
            vim.command(f'let g:dashboard_config_dir = "{escaped_dir}"')
            
            return True
            
        except Exception as e:
            error_msg = format_error_message(e, "Dashboard Browser")
            vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')
            return False
    
    def cleanup(self):
        """Cleanup dashboard resources."""
        try:
            cleanup_scheduler()
        except Exception as e:
            print(f"Cleanup error: {e}")


# Global dashboard instance
_dashboard_core = None


def get_dashboard_core() -> DashboardCore:
    """Get the global dashboard core instance."""
    global _dashboard_core
    if _dashboard_core is None:
        _dashboard_core = DashboardCore()
    return _dashboard_core


# Vim interface functions
def dashboard_start(config_file: str):
    """Vim interface for starting dashboard."""
    core = get_dashboard_core()
    return core.start_dashboard(config_file)


def dashboard_restart():
    """Vim interface for restarting dashboard."""
    core = get_dashboard_core()
    core.restart_dashboard()


def dashboard_stop(config_file: str = ""):
    """Vim interface for stopping dashboard."""
    core = get_dashboard_core()
    core.stop_dashboard(config_file if config_file else None)


def dashboard_list():
    """Vim interface for listing dashboards."""
    core = get_dashboard_core()
    core.list_dashboards()


def dashboard_browser():
    """Vim interface for opening dashboard browser."""
    core = get_dashboard_core()
    core.open_dashboard_browser()


def dashboard_open_selected():
    """Open selected config file from browser."""
    try:
        # Get current line number
        line_num = vim.current.window.cursor[0]
        
        # Get config files from vim variable
        try:
            config_files = vim.eval('g:dashboard_config_files')
            # vim.eval returns vim list as Python list, so it should work directly
            if not isinstance(config_files, list):
                config_files = []
        except:
            config_files = []
        try:
            config_dir = vim.eval('g:dashboard_config_dir')
            if not isinstance(config_dir, str):
                config_dir = ''
        except:
            config_dir = ''
        
        # Calculate selected index (skip header lines)
        selected_index = line_num - 7  # Adjust for header lines
        
        if 0 <= selected_index < len(config_files):
            selected_file = config_files[selected_index]
            full_path = os.path.join(config_dir, selected_file)
            
            # Close browser and start dashboard
            vim.command('quit')
            dashboard_start(full_path)
        else:
            vim.command('echohl ErrorMsg | echo "Invalid selection" | echohl None')
            
    except Exception as e:
        error_msg = format_error_message(e, "Dashboard Selection")
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')


def dashboard_cleanup():
    """Cleanup dashboard on vim exit."""
    global _dashboard_core
    if _dashboard_core:
        _dashboard_core.cleanup()
        _dashboard_core = None