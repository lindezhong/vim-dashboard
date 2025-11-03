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
        @staticmethod
        def eval(expr):
            return []
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
                    # Set autoread and disable file change warnings before opening
                    vim.command('set autoread')
                    vim.command(f'silent edit {temp_file}')
                    # Set filetype to dashboard for syntax highlighting
                    vim.command('setlocal filetype=dashboard')
                    # Set buffer options to handle external changes silently
                    vim.command('setlocal autoread')
                    vim.command('setlocal noswapfile')
                    vim.command('setlocal buftype=nowrite')
                    vim.command('setlocal readonly')
                    # Use the new dashboard buffer setup function
                    vim.command('call dashboard#setup_dashboard_buffer()')
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
                # Set autoread and disable file change warnings before opening
                vim.command('set autoread')
                vim.command(f'silent edit {temp_file}')
                # Set filetype to dashboard for syntax highlighting
                vim.command('setlocal filetype=dashboard')
                # Set buffer options to handle external changes silently
                vim.command('setlocal autoread')
                vim.command('setlocal noswapfile')
                vim.command('setlocal buftype=nowrite')
                vim.command('setlocal readonly')
                # Use the new dashboard buffer setup function
                vim.command('call dashboard#setup_dashboard_buffer()')


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
                vim.command('silent edit!')

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
                    # Get temp file path before stopping
                    temp_file = task.get_temp_file_path()

                    success = self.scheduler.remove_task(task.task_id)
                    if success:
                        # Close the temp file if it exists
                        if temp_file and os.path.exists(temp_file):
                            self._close_dashboard_file(temp_file)

                        # Use vim's shellescape() to safely handle paths with special characters
                        vim.command('echohl MoreMsg')
                        vim.command('echo "Dashboard stopped: " . shellescape(' + repr(config_file) + ')')
                        vim.command('echohl None')
                        # Refresh sidebar if it exists to update status
                        self._refresh_sidebar_if_exists()
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
                current_task_id = None

                for task_id, task_info in tasks.items():
                    if task_info['temp_file'] == current_file:
                        current_task_id = task_id
                        break

                if current_task_id:
                    # Get remaining tasks BEFORE stopping current one
                    all_tasks = self.scheduler.list_tasks()
                    remaining_tasks = {tid: task for tid, task in all_tasks.items() if tid != current_task_id}

                    success = self.scheduler.remove_task(current_task_id)
                    if success:
                        if remaining_tasks:
                            # Get current buffer info before closing
                            current_buffer_name = vim.current.buffer.name
                            current_buffer_number = vim.current.buffer.number


                            # Switch to the first remaining dashboard first
                            first_remaining_task = next(iter(remaining_tasks.values()))
                            remaining_temp_file = first_remaining_task['temp_file']


                            # Switch to the remaining dashboard file first (this preserves window layout)
                            vim.command('set autoread')
                            # Force reload the file content to ensure it's up to date
                            vim.command(f'silent edit! {remaining_temp_file}')
                            vim.command('setlocal filetype=dashboard')
                            vim.command('setlocal autoread')
                            vim.command('setlocal noswapfile')
                            vim.command('setlocal buftype=nowrite')
                            vim.command('setlocal readonly')
                            vim.command('call dashboard#setup_dashboard_buffer()')

                            # Force refresh the buffer content
                            vim.command('silent! checktime')
                            vim.command('redraw!')

                            # Immediately ensure focus is on the dashboard window after file switch
                            vim.command('wincmd l')  # Move to right window first

                            # Now close the old buffer (window layout is preserved since we have a new buffer)
                            vim.command(f'silent! bwipeout {current_buffer_number}')

                            # Final focus enforcement - find and switch to dashboard window
                            vim.command(r'''
for i in range(1, winnr("$") + 1)
  let ft = getwinvar(i, "&filetype")
  if ft == "dashboard"
    execute i . "wincmd w"
    break
  endif
endfor
''')

                            # Multiple forced window switches for reliable focus
                            vim.command('wincmd h')  # Go to left window
                            vim.command('wincmd l')  # Go back to right window
                            vim.command('wincmd h')  # Go to left window again
                            vim.command('wincmd l')  # Go back to right window again

                            # Force focus using window ID
                            vim.command(r'''
let dashboard_win_id = 0
for i in range(1, winnr("$") + 1)
  if getwinvar(i, "&filetype") == "dashboard"
    let dashboard_win_id = win_getid(i)
    break
  endif
endfor
if dashboard_win_id > 0
  call win_gotoid(dashboard_win_id)
endif
''')

                            # Ultimate focus enforcement function
                            vim.command(r'''
function! UltimateFocusEnforcement()
  for i in range(1, winnr("$") + 1)
    if getwinvar(i, "&filetype") == "dashboard"
      execute i . "wincmd w"
      redraw!
      redrawstatus!
      normal! gg
      normal! zz
      set cursorline
      startinsert
      stopinsert
      startinsert
      stopinsert
      redraw!
      break
    endif
  endfor
endfunction
call UltimateFocusEnforcement()
''')

                            # Use feedkeys to simulate user input
                            vim.command("call feedkeys(\"\\<C-w>l\", 'n')")

                            # Force focus using autocmd
                            vim.command(r'''
augroup DashboardFocus
  autocmd!
  autocmd CursorMoved * if &filetype == "dashboard" | set cursorline | endif
augroup END
''')

                            vim.command('echohl MoreMsg | echo "Dashboard stopped, switched to remaining dashboard" | echohl None')
                        else:
                            # No remaining dashboards, close the current buffer

                            # Close the current buffer
                            vim.command('bwipeout')

                            vim.command('echohl MoreMsg | echo "Dashboard stopped" | echohl None')

                        # Refresh sidebar if it exists to update status
                        self._refresh_sidebar_if_exists()
                        return True

                vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
                return False

        except Exception as e:
            import traceback
            # Safely format error message for vim echo
            error_msg = f"Error in stop_dashboard: {str(e)}"
            # Escape quotes and remove newlines for safe vim echo
            safe_error_msg = error_msg.replace('"', '\\"').replace('\n', ' ').replace('\r', '')
            vim.command(f'echohl ErrorMsg | echo "{safe_error_msg}" | echohl None')
            return False

    def _close_dashboard_file(self, temp_file: str):
        """Helper function to close dashboard file."""
        try:
            # Normalize paths for comparison
            temp_file_normalized = os.path.normpath(temp_file)

            # First, try to close the buffer directly
            vim.command(f'silent! bwipeout {temp_file_normalized}')

            # Check all windows to see if the file is still open
            vim.command(r'''
let g:dashboard_file_closed = 1
for i in range(1, winnr("$"))
  let bufname = bufname(winbufnr(i))
endfor
''')

        except Exception as e:
            import traceback
            vim.command(f'echohl ErrorMsg | echo "Error closing dashboard file: {str(e)}" | echohl None')

    def _refresh_sidebar_if_exists(self):
        """Refresh sidebar if it exists to update status."""
        try:
            # Check if sidebar exists
            vim.command('''
let g:dashboard_sidebar_exists = 0
for i in range(1, winnr("$"))
  if getwinvar(i, "&filetype") == "dashboard-sidebar"
    let g:dashboard_sidebar_exists = 1
    break
  endif
endfor
''')

            sidebar_exists = vim.eval('g:dashboard_sidebar_exists') == '1'

            if sidebar_exists:
                # Refresh the sidebar
                self.open_dashboard_browser()
        except Exception as e:
            # Silently ignore errors in sidebar refresh
            pass

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
                countdown_info = f" | Next refresh: {task_info['countdown_display']}" if task_info.get('countdown_display') else ""
                lines.append(f"  {config_file} - {status}{error_info}{countdown_info}")
            
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
        """Open dashboard configuration browser in sidebar."""
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

            # Check if sidebar already exists
            vim.command('''
let g:dashboard_sidebar_exists = 0
for i in range(1, winnr("$"))
  if getwinvar(i, "&filetype") == "dashboard-sidebar"
    let g:dashboard_sidebar_exists = 1
    execute i . "wincmd w"
    break
  endif
endfor
''')

            sidebar_exists = vim.eval('g:dashboard_sidebar_exists') == '1'

            if not sidebar_exists:
                # Create sidebar on the left
                vim.command('topleft 30vnew')
                vim.command('setlocal filetype=dashboard-sidebar')

            # Set buffer options for sidebar (NERDTree style)
            vim.command('setlocal buftype=nofile')
            vim.command('setlocal bufhidden=hide')  # 隐藏时不卸载
            vim.command('setlocal noswapfile')
            vim.command('setlocal nobuflisted')  # ⭐ 关键！不加入 buffer 列表
            vim.command('setlocal cursorline')
            vim.command('setlocal nonumber')
            vim.command('setlocal norelativenumber')
            vim.command('setlocal nowrap')
            vim.command('setlocal winfixwidth')

            # Get running tasks to determine status
            running_tasks = self.scheduler.list_tasks()
            running_config_files = set()
            for task_info in running_tasks.values():
                config_file = os.path.basename(task_info['config_file'])
                running_config_files.add(config_file)

            # Set buffer content with status indicators
            lines = [
                "Dashboard Sidebar",
                f"Directory: {os.path.basename(dashboard_dir)}",
                "",
                "▸ = Not running",
                "▾ = Running",
                ""
            ]

            for config_file in sorted(config_files):
                if config_file in running_config_files:
                    status_icon = "▾"
                else:
                    status_icon = "▸"
                lines.append(f"{status_icon} {config_file}")

            vim.current.buffer[:] = lines

            # Set up key mappings
            vim.command('nnoremap <buffer> <silent> <CR> :python3 import dashboard.core; dashboard.core.dashboard_sidebar_select()<CR>')
            vim.command('nnoremap <buffer> q :quit<CR>')
            vim.command('nnoremap <buffer> <silent> r :python3 import dashboard.core; dashboard.core.dashboard_sidebar_restart()<CR>')
            vim.command('nnoremap <buffer> <silent> t :python3 import dashboard.core; dashboard.core.dashboard_sidebar_stop()<CR>')

            # Store config files and directory for selection
            # Escape special characters in paths for vim
            escaped_dir = dashboard_dir.replace('\\', '\\\\').replace('"', '\\"')

            # Convert Python list to vim list format (use sorted list to match sidebar display)
            sorted_config_files = sorted(config_files)
            vim_list = '[' + ','.join(f'"{f}"' for f in sorted_config_files) + ']'

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

def dashboard_status():
    """Vim interface for showing dashboard status with countdown."""
    core = get_dashboard_core()
    core.list_dashboards()  # Reuse the same functionality as list


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

def dashboard_sidebar_select():
    """Handle selection from sidebar."""
    try:
        # Get current line number
        line_num = vim.current.window.cursor[0]

        # Get config files from vim variable
        try:
            config_files = vim.eval('g:dashboard_config_files')
            if not isinstance(config_files, list):
                config_files = []
        except Exception as e:
            config_files = []
        try:
            config_dir = vim.eval('g:dashboard_config_dir')
            if not isinstance(config_dir, str):
                config_dir = ''
        except Exception as e:
            config_dir = ''

        # Calculate selected index (skip header lines)
        # Sidebar format: title + directory + empty + help1 + help2 + empty = 6 lines, then files start
        selected_index = line_num - 7  # Files start from line 7 (6 header lines + 1 for 0-based)

        if 0 <= selected_index < len(config_files):
            selected_file = config_files[selected_index]
            full_path = os.path.join(config_dir, selected_file)

            # Check if dashboard is already running for this config
            core = get_dashboard_core()
            existing_task = core.scheduler.get_task_by_config_file(full_path)

            if existing_task:
                # Dashboard is running, open the temp file
                temp_file = existing_task.get_temp_file_path()
                if os.path.exists(temp_file):
                    # Switch to right window and open temp file
                    vim.command('wincmd l')
                    # Set autoread and disable file change warnings before opening
                    vim.command('set autoread')
                    vim.command(f'silent edit {temp_file}')
                    # Set filetype to dashboard for syntax highlighting
                    vim.command('setlocal filetype=dashboard')
                    # Set buffer options to handle external changes silently
                    vim.command('setlocal autoread')
                    vim.command('setlocal noswapfile')
                    vim.command('setlocal buftype=nowrite')
                    vim.command('setlocal readonly')
                    # Use the dashboard buffer setup function
                    vim.command('call dashboard#setup_dashboard_buffer()')
                    vim.command('echo "Dashboard file opened"')
                else:
                    vim.command('echohl ErrorMsg | echo "Dashboard temp file not found" | echohl None')
            else:
                # Dashboard not running, start it
                # Switch to right window first so dashboard_start opens file there
                vim.command('wincmd l')
                success = dashboard_start(full_path)

                if success:

                    # Update sidebar status (switch back to sidebar first)
                    vim.command('wincmd h')
                    dashboard_browser()
                    # Switch back to dashboard file (dashboard_start already opened it)
                    vim.command('wincmd l')
                else:
                    vim.command('echohl ErrorMsg | echo "Failed to start dashboard" | echohl None')
        else:
            vim.command(f'echohl ErrorMsg | echo "Invalid selection: {selected_index} not in range 0-{len(config_files)-1}" | echohl None')

    except Exception as e:
        import traceback
        error_msg = f"Error in dashboard_sidebar_select: {str(e)}\\n{traceback.format_exc()}"
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')


def dashboard_sidebar_restart():
    """Restart selected dashboard from sidebar."""
    try:
        # Get current line number
        line_num = vim.current.window.cursor[0]

        # Get config files from vim variable
        try:
            config_files = vim.eval('g:dashboard_config_files')
            if not isinstance(config_files, list):
                config_files = []
        except Exception as e:
            config_files = []
        try:
            config_dir = vim.eval('g:dashboard_config_dir')
            if not isinstance(config_dir, str):
                config_dir = ''
        except Exception as e:
            config_dir = ''

        # Calculate selected index (skip header lines)
        selected_index = line_num - 7  # Files start from line 7

        if 0 <= selected_index < len(config_files):
            selected_file = config_files[selected_index]
            full_path = os.path.join(config_dir, selected_file)

            # Check if dashboard is running for this config
            core = get_dashboard_core()
            existing_task = core.scheduler.get_task_by_config_file(full_path)

            if existing_task:
                # Restart the dashboard
                core.scheduler.restart_task_by_config_file(full_path)
                vim.command('echo "Dashboard restarted"')

                # Refresh sidebar to update status
                dashboard_browser()
            else:
                vim.command('echohl WarningMsg | echo "Dashboard not running for this config" | echohl None')
        else:
            vim.command(f'echohl ErrorMsg | echo "Invalid selection: {selected_index} not in range 0-{len(config_files)-1}" | echohl None')

    except Exception as e:
        import traceback
        error_msg = f"Error in dashboard_sidebar_restart: {str(e)}\n{traceback.format_exc()}"
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')

def dashboard_sidebar_stop():
    """Stop selected dashboard from sidebar."""
    try:
        # Get current line number
        line_num = vim.current.window.cursor[0]

        # Get config files from vim variable
        try:
            config_files = vim.eval('g:dashboard_config_files')
            if not isinstance(config_files, list):
                config_files = []
        except Exception as e:
            config_files = []
        try:
            config_dir = vim.eval('g:dashboard_config_dir')
            if not isinstance(config_dir, str):
                config_dir = ''
        except Exception as e:
            config_dir = ''

        # Calculate selected index (skip header lines)
        selected_index = line_num - 7  # Files start from line 7

        if 0 <= selected_index < len(config_files):
            selected_file = config_files[selected_index]
            full_path = os.path.join(config_dir, selected_file)

            # Check if dashboard is running for this config
            core = get_dashboard_core()
            existing_task = core.scheduler.get_task_by_config_file(full_path)

            if existing_task:
                # Get temp file path before stopping
                temp_file = existing_task.get_temp_file_path()


                # Check if the temp file is currently open in any buffer


                # Switch to the temp file buffer first, then use unified stop logic

                vim.command('wincmd l')  # Switch to right window
                vim.command(f'silent edit {temp_file}')  # Open the temp file

                # Verify we're in the correct buffer
                current_buffer_after_switch = vim.current.buffer.name
                # Now use the unified stop logic (no config_file parameter)
                core.stop_dashboard()  # This will use the current buffer logic

                # Check again if the temp file buffer still exists after stopping




                # Refresh sidebar to update status
                dashboard_browser()
            else:
                vim.command('echohl WarningMsg | echo "Dashboard not running for this config" | echohl None')
        else:
            vim.command(f'echohl ErrorMsg | echo "Invalid selection: {selected_index} not in range 0-{len(config_files)-1}" | echohl None')

    except Exception as e:
        import traceback
        error_msg = f"Error in dashboard_sidebar_stop: {str(e)}\n{traceback.format_exc()}"
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')

def dashboard_cleanup():
    """Cleanup dashboard on vim exit."""
    global _dashboard_core
    if _dashboard_core:
        _dashboard_core.cleanup()
        _dashboard_core = None

# Variables management functions

def dashboard_show_variables():
    """Show variables for current dashboard."""
    try:
        # Get current buffer file path
        current_file = vim.current.buffer.name
        if not current_file:
            vim.command('echohl ErrorMsg | echo "No active dashboard buffer" | echohl None')
            return

        # Find the task associated with this temp file
        core = get_dashboard_core()
        tasks = core.scheduler.list_tasks()

        current_task = None
        for task_id, task_info in tasks.items():
            if task_info.get('temp_file') == current_file:
                current_task = core.scheduler.get_task(task_id)
                break

        if not current_task:
            vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
            return

        # Get variables info
        variables_info = current_task.get_variables_info()

        if not variables_info:
            vim.command('echohl MoreMsg | echo "No variables found for current dashboard" | echohl None')
            return

        # Display variables in a new buffer
        vim.command('new')
        lines = ["Dashboard Variables", ""]

        for var_name, var_info in variables_info.items():
            var_type = var_info.get('type', 'string')
            current_value = str(var_info.get('current_value', ''))
            default_value = str(var_info.get('default_value', ''))
            description = var_info.get('description', '')

            lines.append(f"Variable: {var_name}")
            lines.append(f"  Type: {var_type}")
            lines.append(f"  Current Value: {current_value}")
            lines.append(f"  Default Value: {default_value}")
            if description:
                lines.append(f"  Description: {description}")
            lines.append("")

        vim.current.buffer[:] = lines
        vim.command('setlocal buftype=nofile')
        vim.command('setlocal noswapfile')
        vim.command('setlocal readonly')
        vim.command('setlocal filetype=text')

    except Exception as e:
        error_msg = format_error_message(e, "Show Variables")
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')

def dashboard_get_variables_info():
    """Get variables info for current dashboard (used by Vim interface)."""
    try:
        # Get current buffer file path
        current_file = vim.current.buffer.name
        if not current_file:
            return None

        # Find the task associated with this temp file
        core = get_dashboard_core()
        tasks = core.scheduler.list_tasks()

        current_task = None
        for task_id, task_info in tasks.items():
            if task_info.get('temp_file') == current_file:
                current_task = core.scheduler.get_task(task_id)
                break

        if not current_task:
            return None

        # Get variables info
        return current_task.get_variables_info()

    except Exception as e:
        return None

def dashboard_update_variable(var_name: str, new_value: str):
    """Update a variable for current dashboard."""
    try:
        # Get current buffer file path
        current_file = vim.current.buffer.name
        if not current_file:
            vim.command('echohl ErrorMsg | echo "No active dashboard buffer" | echohl None')
            return

        # Find the task associated with this temp file
        core = get_dashboard_core()
        tasks = core.scheduler.list_tasks()

        current_task_id = None
        current_task = None
        for task_id, task_info in tasks.items():
            if task_info.get('temp_file') == current_file:
                current_task_id = task_id
                current_task = core.scheduler.get_task(task_id)
                break

        if not current_task_id or not current_task:
            vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
            return

        # Check if variable exists
        variables_info = current_task.get_variables_info()
        if var_name not in variables_info:
            vim.command(f'echohl ErrorMsg | echo "Variable {var_name} not found" | echohl None')
            return

        # Update the variable (this will trigger refresh automatically)
        success = core.scheduler.update_variable(current_task_id, var_name, new_value)

        if success:
            vim.command(f'echohl MoreMsg | echo "Variable {var_name} updated to \\"{new_value}\\" and dashboard refreshed" | echohl None')
        else:
            # Get detailed error from task
            error_msg = getattr(current_task, 'last_error', 'Unknown error')
            vim.command(f'echohl ErrorMsg | echo "Failed to update variable {var_name}: {error_msg}" | echohl None')

    except Exception as e:
        import traceback
        error_msg = f"Error updating variable: {str(e)}\\n{traceback.format_exc()}"
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')

def dashboard_reset_variables():
    """Reset all variables to default values for current dashboard."""
    try:
        # Get current buffer file path
        current_file = vim.current.buffer.name
        if not current_file:
            vim.command('echohl ErrorMsg | echo "No active dashboard buffer" | echohl None')
            return

        # Find the task associated with this temp file
        core = get_dashboard_core()
        tasks = core.scheduler.list_tasks()

        current_task_id = None
        for task_id, task_info in tasks.items():
            if task_info.get('temp_file') == current_file:
                current_task_id = task_id
                break

        if not current_task_id:
            vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
            return

        # Reset variables (this will trigger refresh automatically)
        success = core.scheduler.reset_variables(current_task_id)

        if success:
            vim.command('echohl MoreMsg | echo "All variables reset to default values and dashboard refreshed" | echohl None')
        else:
            vim.command('echohl ErrorMsg | echo "Failed to reset variables" | echohl None')

    except Exception as e:
        error_msg = format_error_message(e, "Reset Variables")
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')

def dashboard_show_sql():
    """Show the rendered SQL for current dashboard."""
    try:
        # Get current buffer file path
        current_file = vim.current.buffer.name
        if not current_file:
            vim.command('echohl ErrorMsg | echo "No active dashboard buffer" | echohl None')
            return

        # Find the task associated with this temp file
        core = get_dashboard_core()
        tasks = core.scheduler.list_tasks()

        current_task = None
        for task_id, task_info in tasks.items():
            if task_info.get('temp_file') == current_file:
                current_task = core.scheduler.get_task(task_id)
                break

        if not current_task:
            vim.command('echohl ErrorMsg | echo "Current buffer is not a dashboard" | echohl None')
            return

        # Get the rendered SQL
        rendered_sql = current_task.get_rendered_sql()

        if not rendered_sql:
            vim.command('echohl WarningMsg | echo "No SQL found for current dashboard" | echohl None')
            return

        # Prepare SQL content for popup display
        sql_lines = rendered_sql.split('\n')

        # Add header
        lines = [
            "Dashboard Rendered SQL",
            f"Config: {os.path.basename(current_task.config_file)}",
            f"Generated at: {current_task.get_last_execution_time() or 'N/A'}",
            "",
            "Variables used:",
        ]

        # Add variables info
        variables_info = current_task.get_variables_info()
        if variables_info:
            for var_name, var_info in variables_info.items():
                current_value = var_info.get('current_value', var_info.get('default_value', ''))
                lines.append(f"{var_name}: {current_value}")
        else:
            lines.append("No variables defined")

        lines.extend(["", "Rendered SQL:"])
        lines.extend(sql_lines)

        # Calculate popup dimensions
        max_width = max(len(line) for line in lines) + 4
        max_height = min(len(lines) + 2, 30)  # Limit height to 30 lines

        # Ensure minimum dimensions
        popup_width = max(max_width, 60)
        popup_height = max(max_height, 10)

        # Create popup using Vim's popup functionality
        # Use the safest method: create a temporary buffer and read from it
        # This completely avoids any string escaping issues

        # Create a temporary buffer with the content
        vim.command('new')
        vim.command('setlocal buftype=nofile noswapfile')

        # Set the content in the buffer (no escaping needed)
        vim.current.buffer[:] = lines

        # Get buffer number for reference
        temp_buf_num = vim.current.buffer.number

        # Close the temporary buffer window but keep the buffer
        vim.command('quit')

        # Create popup using separate commands to avoid complex string interpolation
        vim.command(f'let g:temp_buf_num = {temp_buf_num}')

        # Execute VimScript commands step by step
        vim.command('let l:popup_content = getbufline(g:temp_buf_num, 1, "$")')

        # Check for popup support and create accordingly
        vim.command(r'''
        if exists('*popup_create')
            " Vim 8.2+ popup
            let l:popup_opts = {
                \ 'title': ' SQL Query ',
                \ 'wrap': 1,
                \ 'scrollbar': 1,
                \ 'resize': 1,
                \ 'close': 'button',
                \ 'border': [],
                \ 'borderchars': ['─', '│', '─', '│', '┌', '┐', '┘', '└'],
                \ 'minwidth': 60,
                \ 'maxwidth': 120,
                \ 'minheight': 10,
                \ 'maxheight': 30,
                \ 'pos': 'center',
                \ 'mapping': 0,
                \ 'filter': 'dashboard#sql_popup_filter',
                \ 'callback': 'dashboard#sql_popup_callback'
            \ }
            let g:dashboard_sql_popup_id = popup_create(l:popup_content, l:popup_opts)
            call popup_setoptions(g:dashboard_sql_popup_id, {'filetype': 'sql'})
        elseif exists('*nvim_open_win')
            " Neovim floating window
            let l:buf = nvim_create_buf(v:false, v:true)
            call nvim_buf_set_lines(l:buf, 0, -1, v:true, l:popup_content)
            call nvim_buf_set_option(l:buf, 'filetype', 'sql')
            call nvim_buf_set_option(l:buf, 'modifiable', v:false)

            let l:width = min([max([max(map(copy(l:popup_content), 'len(v:val)')) + 4, 60]), 120])
            let l:height = min([len(l:popup_content) + 2, 30])

            let l:opts = {
                \ 'relative': 'editor',
                \ 'width': l:width,
                \ 'height': l:height,
                \ 'col': (&columns - l:width) / 2,
                \ 'row': (&lines - l:height) / 2,
                \ 'anchor': 'NW',
                \ 'style': 'minimal',
                \ 'border': 'rounded'
            \ }

            let g:dashboard_sql_popup_id = nvim_open_win(l:buf, v:true, l:opts)
            nnoremap <buffer> q :lua vim.api.nvim_win_close(0, true)<CR>
            nnoremap <buffer> <Esc> :lua vim.api.nvim_win_close(0, true)<CR>
        else
            " Fallback to split window for older versions
            new
            setlocal buftype=nofile noswapfile readonly filetype=sql
            call setline(1, l:popup_content)
            nnoremap <buffer> q :quit<CR>
            resize 20
        endif
        ''')

        # Clean up the temporary buffer
        vim.command('execute "bdelete! " . g:temp_buf_num')
        vim.command('unlet g:temp_buf_num')

    except Exception as e:
        error_msg = format_error_message(e, "Show SQL")
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')