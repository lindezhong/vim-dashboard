" vim-dashboard autoload functions
" Author: vim-dashboard team

let s:plugin_root = expand('<sfile>:p:h:h')
let s:python_path = s:plugin_root . '/python3'
let s:venv_path = s:plugin_root . '/venv'

" Get virtual environment Python executable
function! s:get_venv_python()
  if has('win32') || has('win64')
    return s:venv_path . '/Scripts/python.exe'
  else
    return s:venv_path . '/bin/python'
  endif
endfunction

" Check if virtual environment exists
function! s:venv_exists()
  let l:python_exe = s:get_venv_python()
  return executable(l:python_exe)
endfunction

" Create virtual environment
function! s:create_venv()
  echom 'Creating virtual environment for vim-dashboard...'

  let l:python_cmd = 'python3'
  if !executable(l:python_cmd)
    let l:python_cmd = 'python'
  endif

  if !executable(l:python_cmd)
    echohl ErrorMsg
    echom 'Python3 not found. Please install Python3 first.'
    echohl None
    return 0
  endif

  " Create virtual environment
  let l:create_cmd = l:python_cmd . ' -m venv "' . s:venv_path . '"'
  let l:result = system(l:create_cmd)

  if v:shell_error != 0
    echohl ErrorMsg
    echom 'Failed to create virtual environment: ' . l:result
    echohl None
    return 0
  endif

  " Install dependencies
  echom 'Installing dependencies...'
  let l:pip_cmd = s:get_venv_python() . ' -m pip install -r "' . s:plugin_root . '/requirements.txt"'
  let l:pip_result = system(l:pip_cmd)

  if v:shell_error != 0
    echohl ErrorMsg
    echom 'Failed to install dependencies: ' . l:pip_result
    echohl None
    return 0
  endif

  echom 'Virtual environment created successfully!'
  return 1
endfunction

" Initialize virtual environment and Python path
function! s:init_python()
  if !exists('s:python_initialized')
    " Check if virtual environment exists
    if !s:venv_exists()
      if !s:create_venv()
        return 0
      endif
    endif

    " Use virtual environment Python
    let l:venv_python = s:get_venv_python()

    " Set Python executable for vim
    if has('python3_dynamic')
      execute 'py3 import sys'
      execute 'py3 sys.executable = "' . l:venv_python . '"'
    endif

    " Add plugin path to Python path
    execute 'python3 import sys'
    execute 'python3 sys.path.insert(0, "' . s:python_path . '")'

    let s:python_initialized = 1
  endif
  return 1
endfunction

" Get platform-specific paths
function! s:get_temp_dir()
  if has('win32') || has('win64')
    return $TEMP . '/vim-dashboard'
  else
    return '/tmp/vim-dashboard'
  endif
endfunction

function! s:get_config_dir()
  if exists('g:dashboard_config_dir') && !empty(g:dashboard_config_dir)
    return g:dashboard_config_dir
  endif
  return expand('~/dashboard')
endfunction

" Start dashboard with config file
function! dashboard#start(config_file)
  if !s:init_python()
    return
  endif
  
  let l:config_path = expand(a:config_file)
  if !filereadable(l:config_path)
    echohl ErrorMsg
    echom 'Dashboard config file not found: ' . l:config_path
    echohl None
    return
  endif
  
  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_start(vim.eval('l:config_path'))
EOF
  catch
    echohl ErrorMsg
    echom 'Error starting dashboard: ' . v:exception
    echohl None
  endtry
endfunction

" Restart current dashboard
function! dashboard#restart()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_restart()
EOF
  catch
    echohl ErrorMsg
    echom 'Error restarting dashboard: ' . v:exception
    echohl None
  endtry
endfunction

" Stop dashboard (current or specific config file)
function! dashboard#stop(...)
  if !s:init_python()
    return
  endif

  let l:config_file = a:0 > 0 ? a:1 : ""

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_stop(vim.eval('l:config_file'))
EOF
  catch
    echohl ErrorMsg
    echom 'Error stopping dashboard: ' . v:exception
    echohl None
  endtry
endfunction

" List all running dashboards
function! dashboard#list()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_list()
EOF
  catch
    echohl ErrorMsg
    echom 'Error listing dashboards: ' . v:exception
    echohl None
  endtry
endfunction

" Show dashboard status with countdown
function! dashboard#status()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_status()
EOF
  catch
    echohl ErrorMsg
    echom 'Error showing dashboard status: ' . v:exception
    echohl None
  endtry
endfunction

" Browse dashboard configs
function! dashboard#browse()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_browser()
EOF
  catch
    echohl ErrorMsg
    echom 'Error opening dashboard browser: ' . v:exception
    echohl None
  endtry
endfunction

" Initialize dashboard system
function! dashboard#init()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard
# Import all chart types to register them
import dashboard.charts.table
import dashboard.charts.bar
import dashboard.charts.line
EOF
  catch
    echohl ErrorMsg
    echom 'Error initializing dashboard: ' . v:exception
    echohl None
  endtry
endfunction

" Cleanup dashboard on vim exit
function! dashboard#cleanup()
  if exists('s:python_initialized')
    try
      execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_cleanup()
EOF
    catch
      " Ignore cleanup errors
    endtry
  endif
endfunction

" Handle file changed event for dashboard buffers
function! dashboard#handle_file_changed()
  " Only handle dashboard buffers
  if !exists('b:is_dashboard_buffer') || !b:is_dashboard_buffer
    return
  endif

  " Automatically reload without prompting
  let v:fcs_choice = 'reload'

  " Update stored modification time
  if exists('b:dashboard_file_path')
    let b:dashboard_last_mtime = getftime(b:dashboard_file_path)
  endif

  " Force reload the file
  silent! edit!

  " Show a brief message
  redraw
  echo "Dashboard updated via FileChangedShell"
endfunction

" Variables management functions

" Show variables for current dashboard
function! dashboard#show_variables()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_show_variables()
EOF
  catch
    echohl ErrorMsg
    echom 'Error showing variables: ' . v:exception
    echohl None
  endtry
endfunction

" Update a variable value
function! dashboard#update_variable(var_name, new_value)
  if !s:init_python()
    return
  endif

  let l:var_name = a:var_name
  let l:new_value = a:new_value

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_update_variable(vim.eval('l:var_name'), vim.eval('l:new_value'))
EOF
  catch
    echohl ErrorMsg
    echom 'Error updating variable: ' . v:exception
    echohl None
  endtry
endfunction

" Interactive variable modification
function! dashboard#modify_variable()
  if !s:init_python()
    return
  endif

  try
    " First get available variables
    execute 'python3 << EOF'
import dashboard.core
import json

def python_to_vim_value(obj):
    """Convert Python objects to VimScript-compatible format"""
    if obj is None:
        return ""  # Convert None to empty string for VimScript
    elif isinstance(obj, bool):
        return 1 if obj else 0
    elif isinstance(obj, (list, tuple)):
        return [python_to_vim_value(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: python_to_vim_value(v) for k, v in obj.items()}
    else:
        return obj

variables_info = dashboard.core.dashboard_get_variables_info()
if variables_info:
    var_names = list(variables_info.keys())
    # Convert to VimScript-compatible format
    vim_var_names = json.dumps(var_names)
    vim_variables_info = json.dumps(python_to_vim_value(variables_info))

    # Replace any remaining null values in JSON strings
    vim_var_names = vim_var_names.replace('null', '""')
    vim_variables_info = vim_variables_info.replace('null', '""')

    vim.command('let l:var_names = ' + vim_var_names)
    vim.command('let l:variables_info = ' + vim_variables_info)
else:
    vim.command('let l:var_names = []')
    vim.command('let l:variables_info = {}')
EOF

    if empty(l:var_names)
      echom 'No variables found for current dashboard'
      return
    endif

    " Show variable selection menu
    let l:choice_list = []
    let l:index = 0
    for l:var_name in l:var_names
      let l:index += 1
      let l:var_info = get(l:variables_info, l:var_name, {})
      let l:current_value = get(l:var_info, 'current_value', '')
      let l:var_type = get(l:var_info, 'type', 'string')
      let l:description = get(l:var_info, 'description', '')

      let l:current_value_str = l:current_value
      " Convert complex types to string representation for display
      if l:var_type == 'list' || l:var_type == 'map'
        let l:current_value_str = string(l:current_value)
      endif

      let l:display_line = printf('%d. %s (%s) = %s', l:index, l:var_name, l:var_type, l:current_value_str)
      if !empty(l:description)
        let l:display_line .= ' - ' . l:description
      endif
      call add(l:choice_list, l:display_line)
    endfor

    " Show selection menu
    echo "Select variable to modify:"
    for l:line in l:choice_list
      echo l:line
    endfor

    let l:choice = input('Enter variable number (1-' . len(l:var_names) . '): ')
    let l:choice_num = str2nr(l:choice)

    if l:choice_num < 1 || l:choice_num > len(l:var_names)
      echom 'Invalid choice'
      return
    endif

    let l:selected_var = l:var_names[l:choice_num - 1]
    let l:var_info = get(l:variables_info, l:selected_var, {})
    let l:current_value = get(l:var_info, 'current_value', '')
    let l:var_type = get(l:var_info, 'type', 'string')

    " Prompt for new value
    " Convert current value to string for display
    let l:current_value_display = l:current_value
    if l:var_type == 'list' || l:var_type == 'map'
      let l:current_value_display = string(l:current_value)
    endif

    echo "\nCurrent value: " . l:current_value_display
    echo "Variable type: " . l:var_type

    if l:var_type == 'boolean'
      echo "Enter new value (true/false): "
    elseif l:var_type == 'list'
      echo "Enter new value (comma-separated): "
    elseif l:var_type == 'map'
      echo "Enter new value (key1=value1,key2=value2): "
    else
      echo "Enter new value: "
    endif

    let l:new_value = input('')

    if empty(l:new_value)
      echom 'No value entered, operation cancelled'
      return
    endif

    " Update the variable
    call dashboard#update_variable(l:selected_var, l:new_value)

  catch
    echohl ErrorMsg
    echom 'Error in variable modification: ' . v:exception
    echohl None
  endtry
endfunction

" Reset variables to default values
function! dashboard#reset_variables()
  if !s:init_python()
    return
  endif

  let l:confirm = input('Reset all variables to default values? (y/N): ')
  if l:confirm !=? 'y'
    echom 'Operation cancelled'
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_reset_variables()
EOF
  catch
    echohl ErrorMsg
    echom 'Error resetting variables: ' . v:exception
    echohl None
  endtry
endfunction

" Setup dashboard buffer with variable interaction mappings
function! dashboard#setup_dashboard_buffer()
  let l:current_file = expand('%:p')
  let l:temp_dir = s:get_temp_dir()

  " Check if current file is in dashboard temp directory
  if (stridx(l:current_file, l:temp_dir) == 0 ||
      \ stridx(l:current_file, 'dashboard') != -1 ||
      \ stridx(l:current_file, 'vim-dashboard') != -1) &&
      \ l:current_file =~# '\.dashboard$'

    " Set buffer options for dashboard temp files
    setlocal autoread
    setlocal noswapfile
    setlocal buftype=nowrite
    setlocal readonly
    setlocal nomodeline
    setlocal updatetime=1000

    " Store file modification time for comparison
    let b:dashboard_last_mtime = getftime(l:current_file)
    let b:is_dashboard_buffer = 1
    let b:dashboard_file_path = l:current_file

    " Set up buffer-local key mappings for variable interaction
    nnoremap <buffer> <silent> v :call dashboard#modify_variable()<CR>
    nnoremap <buffer> <silent> V :call dashboard#show_variables()<CR>
    nnoremap <buffer> <silent> r :call dashboard#restart()<CR>
    nnoremap <buffer> <silent> R :call dashboard#reset_variables()<CR>
    nnoremap <buffer> <silent> s :call dashboard#show_sql()<CR>

    " Set up buffer-local auto commands for file change detection
    augroup DashboardBuffer
      autocmd! * <buffer>
      " Multiple triggers for checking file changes
      autocmd CursorHold,CursorHoldI <buffer> call dashboard#check_file_changes()
      autocmd FocusGained <buffer> call dashboard#check_file_changes()
      autocmd BufEnter <buffer> call dashboard#check_file_changes()
      " Handle external file changes without prompting
      autocmd FileChangedShell <buffer> call dashboard#handle_file_changed()
    augroup END

    " Start periodic refresh timer
    call dashboard#start_refresh_timer()

    " Help message removed for silent execution

  endif
endfunction

" Start periodic refresh timer for active dashboard buffer
function! dashboard#start_refresh_timer()
  " Stop any existing timer
  call dashboard#stop_refresh_timer()

  " Start new timer that checks every 2 seconds
  let b:dashboard_timer = timer_start(2000, 'dashboard#timer_callback', {'repeat': -1})
endfunction

" Stop refresh timer
function! dashboard#stop_refresh_timer()
  if exists('b:dashboard_timer')
    call timer_stop(b:dashboard_timer)
    unlet b:dashboard_timer
  endif
endfunction

" Timer callback function
function! dashboard#timer_callback(timer_id)
  " Only process if current buffer is a dashboard buffer
  if exists('b:is_dashboard_buffer') && b:is_dashboard_buffer
    call dashboard#check_file_changes()
  else
    " Stop timer if buffer is no longer a dashboard buffer
    call timer_stop(a:timer_id)
  endif
endfunction

" Check for file changes and reload if necessary
function! dashboard#check_file_changes()
  if !exists('b:is_dashboard_buffer') || !b:is_dashboard_buffer
    return
  endif

  if !exists('b:dashboard_file_path') || !exists('b:dashboard_last_mtime')
    return
  endif

  let l:current_file = b:dashboard_file_path

  " Check if file still exists
  if !filereadable(l:current_file)
    return
  endif

  " Get current modification time
  let l:current_mtime = getftime(l:current_file)

  " Compare with stored modification time
  if l:current_mtime > b:dashboard_last_mtime
    " File has been modified, reload it
    let b:dashboard_last_mtime = l:current_mtime

    " Save current cursor position
    let l:save_cursor = getpos('.')

    " Reload file silently
    silent! edit!

    " Restore cursor position
    call setpos('.', l:save_cursor)


  endif
endfunction" Show rendered SQL for current dashboard
function! dashboard#show_sql()
  if !s:init_python()
    return
  endif

  try
    execute 'python3 << EOF'
import dashboard.core
dashboard.core.dashboard_show_sql()
EOF
  catch
    echohl ErrorMsg
    echom 'Error showing SQL: ' . v:exception
    echohl None
  endtry
endfunction

" Popup filter function for SQL popup
function! dashboard#sql_popup_filter(winid, key)
  " Handle key presses in the SQL popup
  if a:key ==# 'q' || a:key ==# "\<Esc>"
    call popup_close(a:winid)
    return 1
  elseif a:key ==# 'r'
    " Refresh SQL
    call popup_close(a:winid)
    call dashboard#show_sql()
    return 1
  elseif a:key ==# 'j' || a:key ==# "\<Down>"
    call win_execute(a:winid, "normal! j")
    return 1
  elseif a:key ==# 'k' || a:key ==# "\<Up>"
    call win_execute(a:winid, "normal! k")
    return 1
  elseif a:key ==# 'g'
    call win_execute(a:winid, "normal! gg")
    return 1
  elseif a:key ==# 'G'
    call win_execute(a:winid, "normal! G")
    return 1
  elseif a:key ==# "\<C-d>"
    call win_execute(a:winid, "normal! \<C-d>")
    return 1
  elseif a:key ==# "\<C-u>"
    call win_execute(a:winid, "normal! \<C-u>")
    return 1
  endif

  " Let other keys pass through
  return 0
endfunction

" Popup callback function for SQL popup
function! dashboard#sql_popup_callback(winid, result)
  " Called when popup is closed
  " Clean up any global variables if needed
  if exists('g:dashboard_sql_popup_id')
    unlet g:dashboard_sql_popup_id
  endif
endfunction
