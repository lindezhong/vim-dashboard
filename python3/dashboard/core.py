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
                # vim.command('echohl WarningMsg')
                # vim.command('echo "Dashboard already running for: " . shellescape(' + repr(config_file) + ')')
                # vim.command('echohl None')

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
            vim.command(r'''
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
            # Use current working directory instead of fixed config directory
            try:
                dashboard_dir = vim.eval('getcwd()')
            except:
                dashboard_dir = os.getcwd()

            # Ensure directory exists (but don't create sample files in current directory)
            if not os.path.exists(dashboard_dir):
                # If current directory doesn't exist, something is wrong
                vim.command('echohl ErrorMsg | echo "Current directory does not exist!" | echohl None')
                return False

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
            vim.command(r'''
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
                f"Directory: {dashboard_dir}",
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
            vim.command('nnoremap <buffer> <silent> q :python3 import dashboard.core; dashboard.core.dashboard_close()<CR>')
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
    
    def close_dashboard_browser(self) -> bool:
        """Close dashboard browser sidebar."""
        try:
            # Check if sidebar exists
            sidebar_exists = vim.eval('g:dashboard_sidebar_exists') == '1'

            if sidebar_exists:
                # Find and close the sidebar buffer
                vim.command('let l:current_win = winnr()')

                # Look for dashboard-sidebar buffer
                vim.command('for l:i in range(1, winnr("$"))')
                vim.command('  execute l:i . "wincmd w"')
                vim.command('  if &filetype == "dashboard-sidebar"')
                vim.command('    quit')
                vim.command('    break')
                vim.command('  endif')
                vim.command('endfor')

                # Return to original window if it still exists
                vim.command('if winnr("$") >= l:current_win')
                vim.command('  execute l:current_win . "wincmd w"')
                vim.command('endif')

                # Mark sidebar as closed
                vim.command('let g:dashboard_sidebar_exists = 0')

                return True
            else:
                vim.command('echo "Dashboard sidebar is not open"')
                return False

        except Exception as e:
            error_msg = format_error_message(e, "Dashboard Close")
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

def dashboard_close():
    """Vim interface for closing dashboard browser."""
    core = get_dashboard_core()
    core.close_dashboard_browser()


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

        # Add header with operation keys information at the top
        lines = [
            "Press 'Esc' to quit, 'y' to copy, 'Shift+Down/Up' to scroll",
            "",
            "Dashboard Rendered SQL",
            f"Config: {os.path.basename(current_task.config_file)}",
            f"Generated at: {current_task.get_last_execution_time() or 'N/A'}",
            "",
            "Variables used:",
        ]

        # Add variables info
        variables_info = current_task.get_variables_info()

        if variables_info:
            import json
            for var_name, var_info in variables_info.items():
                current_value = var_info.get('current_value', var_info.get('default_value', ''))
                # Safely serialize complex values to avoid escape issues
                try:
                    if isinstance(current_value, (dict, list)):
                        value_str = json.dumps(current_value, ensure_ascii=False)
                    else:
                        value_str = str(current_value)
                except:
                    value_str = str(current_value)
                lines.append(f"{var_name}: {value_str}")
        else:
            lines.append("No variables defined")

        lines.extend(["", "Rendered SQL:"])
        lines.extend(sql_lines)



        # Create a temporary buffer with the content
        vim.command('let l:temp_buf = bufnr("__dashboard_sql__", 1)')
        vim.command('call bufload(l:temp_buf)')

        # Clear buffer first
        vim.command('call deletebufline(l:temp_buf, 1, "$")')

        # Set buffer content using setbufline with list to avoid escaping issues
        vim.command('let l:content_lines = []')
        for i, line in enumerate(lines):
            # Use repr() to safely escape the line content
            safe_line = repr(line)
            vim.command(f'let l:line_{i} = {safe_line}')
            vim.command(f'call add(l:content_lines, l:line_{i})')

        vim.command('call setbufline(l:temp_buf, 1, l:content_lines)')

        # Set buffer options
        vim.command('call setbufvar(l:temp_buf, "&filetype", "sql")')
        vim.command('call setbufvar(l:temp_buf, "&buftype", "nofile")')
        vim.command('call setbufvar(l:temp_buf, "&bufhidden", "wipe")')
        vim.command('call setbufvar(l:temp_buf, "&swapfile", 0)')
        vim.command('call setbufvar(l:temp_buf, "&modifiable", 0)')

        # Calculate dimensions
        max_width = min(max(len(line) for line in lines) + 4, 120)
        width = max(max_width, 60)
        height = min(len(lines) + 2, 25)



        # Check editor type and create appropriate popup
        if vim.eval('has("nvim")') == '1':

            # Neovim floating window - use safer approach
            lua_script = f'''
local buf = vim.fn.bufnr("__dashboard_sql__")
local width = {width}
local height = {height}
local row = math.floor((vim.o.lines - height) / 2)
local col = math.floor((vim.o.columns - width) / 2)

local opts = {{
    relative = 'editor',
    width = width,
    height = height,
    row = row,
    col = col,
    style = 'minimal',
    border = 'rounded',
    title = ' SQL Query ',
    title_pos = 'center'
}}

local win = vim.api.nvim_open_win(buf, true, opts)

-- Set window options
vim.api.nvim_win_set_option(win, 'wrap', false)
vim.api.nvim_win_set_option(win, 'cursorline', true)

-- Set up key mappings
local function close_popup()
    if vim.api.nvim_win_is_valid(win) then
        vim.api.nvim_win_close(win, true)
    end
end

local function copy_content()
    local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
    -- Skip header lines (first 9 lines contain metadata)
    local sql_lines = {{}}
    for i = 10, #lines do
        table.insert(sql_lines, lines[i])
    end
    local content = table.concat(sql_lines, "\\n")
    vim.fn.setreg('+', content)
    vim.fn.setreg('*', content)
    print("SQL content copied to clipboard!")
end

-- Scrolling functions
local function scroll_down()
    local current_line = vim.api.nvim_win_get_cursor(win)[1]
    local total_lines = vim.api.nvim_buf_line_count(buf)
    local win_height = vim.api.nvim_win_get_height(win)
    local new_line = math.min(current_line + math.floor(win_height / 2), total_lines)
    vim.api.nvim_win_set_cursor(win, {{new_line, 0}})
end

local function scroll_up()
    local current_line = vim.api.nvim_win_get_cursor(win)[1]
    local win_height = vim.api.nvim_win_get_height(win)
    local new_line = math.max(current_line - math.floor(win_height / 2), 1)
    vim.api.nvim_win_set_cursor(win, {{new_line, 0}})
end

local function scroll_page_down()
    local current_line = vim.api.nvim_win_get_cursor(win)[1]
    local total_lines = vim.api.nvim_buf_line_count(buf)
    local win_height = vim.api.nvim_win_get_height(win)
    local new_line = math.min(current_line + win_height - 1, total_lines)
    vim.api.nvim_win_set_cursor(win, {{new_line, 0}})
end

local function scroll_page_up()
    local current_line = vim.api.nvim_win_get_cursor(win)[1]
    local win_height = vim.api.nvim_win_get_height(win)
    local new_line = math.max(current_line - win_height + 1, 1)
    vim.api.nvim_win_set_cursor(win, {{new_line, 0}})
end

local function scroll_line_down()
    local current_line = vim.api.nvim_win_get_cursor(win)[1]
    local total_lines = vim.api.nvim_buf_line_count(buf)
    local new_line = math.min(current_line + 1, total_lines)
    vim.api.nvim_win_set_cursor(win, {{new_line, 0}})
end

local function scroll_line_up()
    local current_line = vim.api.nvim_win_get_cursor(win)[1]
    local new_line = math.max(current_line - 1, 1)
    vim.api.nvim_win_set_cursor(win, {{new_line, 0}})
end

-- Key mappings
vim.api.nvim_buf_set_keymap(buf, 'n', '<Esc>', '', {{
    callback = close_popup,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', 'y', '', {{
    callback = copy_content,
    noremap = true,
    silent = true
}})

-- Scrolling key mappings
vim.api.nvim_buf_set_keymap(buf, 'n', 'j', '', {{
    callback = scroll_line_down,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', 'k', '', {{
    callback = scroll_line_up,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<Down>', '', {{
    callback = scroll_line_down,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<Up>', '', {{
    callback = scroll_line_up,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<S-j>', '', {{
    callback = scroll_page_down,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<S-k>', '', {{
    callback = scroll_page_up,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<S-Down>', '', {{
    callback = scroll_page_down,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<S-Up>', '', {{
    callback = scroll_page_up,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<PageDown>', '', {{
    callback = scroll_page_down,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<PageUp>', '', {{
    callback = scroll_page_up,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<C-f>', '', {{
    callback = scroll_page_down,
    noremap = true,
    silent = true
}})
vim.api.nvim_buf_set_keymap(buf, 'n', '<C-b>', '', {{
    callback = scroll_page_up,
    noremap = true,
    silent = true
}})

-- Store window ID for cleanup
vim.g.dashboard_sql_popup_win = win
'''
            vim.command('lua << EOF')
            vim.command(lua_script)
            vim.command('EOF')
        elif vim.eval('exists("*popup_create")') == '1':

            # Vim popup - use safer approach to avoid escaping issues

            # Create popup options step by step to avoid complex escaping
            vim.command('let l:popup_opts = {}')
            vim.command("let l:popup_opts['title'] = ' SQL Query '")
            vim.command("let l:popup_opts['wrap'] = 0")
            vim.command("let l:popup_opts['scrollbar'] = 1")
            vim.command("let l:popup_opts['resize'] = 0")
            vim.command("let l:popup_opts['close'] = 'button'")
            vim.command("let l:popup_opts['border'] = []")
            vim.command("let l:popup_opts['borderchars'] = ['─', '│', '─', '│', '┌', '┐', '┘', '└']")
            vim.command(f"let l:popup_opts['minwidth'] = {width}")
            vim.command(f"let l:popup_opts['maxwidth'] = {width}")
            vim.command(f"let l:popup_opts['minheight'] = {height}")
            vim.command(f"let l:popup_opts['maxheight'] = {height}")
            vim.command("let l:popup_opts['pos'] = 'center'")
            vim.command("let l:popup_opts['mapping'] = 0")
            vim.command("let l:popup_opts['filter'] = 'DashboardSQLPopupFilter'")

            vim.command('let g:dashboard_sql_popup_id = popup_create(l:temp_buf, l:popup_opts)')

            # Define the filter function separately to avoid escaping issues
            vim.command(r'''
function! DashboardSQLPopupFilter(winid, key)
    if a:key == "\<Esc>"
        call popup_close(a:winid)
        return 1
    elseif a:key == 'y'
        " Copy SQL content to clipboard (skip header lines)
        let l:bufnr = winbufnr(a:winid)
        let l:lines = getbufline(l:bufnr, 10, '$')
        let l:text = join(l:lines, "\n")
        let @+ = l:text
        let @* = l:text
        echo "SQL content copied to clipboard!"
        return 1
    elseif a:key == 'j' || a:key == "\<Down>"
        " Scroll down one line
        call win_execute(a:winid, 'normal! j')
        return 1
    elseif a:key == 'k' || a:key == "\<Up>"
        " Scroll up one line
        call win_execute(a:winid, 'normal! k')
        return 1
    elseif a:key == "\<PageDown>" || a:key == "\<C-f>" || a:key == "\<S-Down>" || a:key == "\<S-j>"
        " Scroll down full page
        call win_execute(a:winid, 'normal! ' . "\<C-f>")
        return 1
    elseif a:key == "\<PageUp>" || a:key == "\<C-b>" || a:key == "\<S-Up>"  || a:key == "\<S-k>"
        " Scroll up full page
        call win_execute(a:winid, 'normal! ' . "\<C-b>")
        return 1
    endif
    return 0
endfunction
            ''')
        else:

            # Fallback: split window - fix escaping
            vim.command(f'''
" Fallback to split window
let l:current_win = winnr()
execute 'split __dashboard_sql__'
execute 'buffer ' . l:temp_buf
resize {height}

" Set up key mappings for split window
nnoremap <buffer> q :close<CR>
nnoremap <buffer> <Esc> :close<CR>
nnoremap <buffer> y :call DashboardCopySQLContent()<CR>

" Scrolling key mappings for split window
nnoremap <buffer> j j
nnoremap <buffer> k k
nnoremap <buffer> <Down> j
nnoremap <buffer> <Up> k
nnoremap <buffer> <S-Down> <C-d>
nnoremap <buffer> <S-Up> <C-u>
nnoremap <buffer> <PageDown> <C-f>
nnoremap <buffer> <PageUp> <C-b>
nnoremap <buffer> <C-f> <C-f>
nnoremap <buffer> <C-b> <C-b>

function! DashboardCopySQLContent()
    let l:lines = getline(10, '$')  " Skip first 9 lines
    let l:text = join(l:lines, "\\n")
    let @+ = l:text
    let @* = l:text
    echo "SQL content copied to clipboard!"
endfunction
            ''')

        vim.command('echohl MoreMsg | echo "SQL popup created. Keys: Esc=close, y=copy, j/k/↑↓=scroll, Shift+↑↓=half-page, PageUp/Down=full-page" | echohl None')

    except Exception as e:
        error_msg = format_error_message(e, "Show SQL")
        vim.command(f'echohl ErrorMsg | echo "{error_msg}" | echohl None')
