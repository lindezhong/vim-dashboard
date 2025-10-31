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

" Setup dashboard buffer with proper auto-reload settings
function! dashboard#setup_dashboard_buffer()
  let l:current_file = expand('%:p')
  let l:temp_dir = s:get_temp_dir()

  " Check if current file is in dashboard temp directory
  if (stridx(l:current_file, l:temp_dir) == 0 ||
      \ stridx(l:current_file, 'dashboard') != -1 ||
      \ stridx(l:current_file, 'vim-dashboard') != -1) &&
      \ l:current_file =~# '\.tmp$'

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

    " Initial message
    echo "Dashboard buffer configured with auto-refresh"
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