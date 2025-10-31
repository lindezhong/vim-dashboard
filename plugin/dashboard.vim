" vim-dashboard - Database Dashboard Plugin for Vim/Neovim
" Author: vim-dashboard team
" Version: 1.0.0

if exists('g:loaded_dashboard') || &cp
  finish
endif
let g:loaded_dashboard = 1

" Check for Python3 support
if !has('python3')
  echohl ErrorMsg
  echom 'vim-dashboard requires Python3 support'
  echohl None
  finish
endif

" Default configuration
let g:dashboard_config_dir = get(g:, 'dashboard_config_dir', expand('~/dashboard'))
let g:dashboard_temp_dir = get(g:, 'dashboard_temp_dir', '')

" Commands
command! -nargs=1 -complete=file <silent> DashboardStart call dashboard#start(<q-args>)
command! -nargs=0 <silent> DashboardRestart call dashboard#restart()
command! -nargs=? -complete=file <silent> DashboardStop call dashboard#stop(<q-args>)
command! -nargs=0 <silent> DashboardList call dashboard#list()
command! -nargs=0 <silent> DashboardStatus call dashboard#status()
command! -nargs=0 <silent> Dashboard call dashboard#browse()

" Auto commands
augroup DashboardPlugin
  autocmd!
  autocmd VimEnter * call dashboard#init()
  autocmd VimLeave * call dashboard#cleanup()
  " Auto-reload dashboard temp files when they change
  autocmd BufRead,BufEnter */dashboard/*.tmp call dashboard#setup_dashboard_buffer()
  autocmd BufRead,BufEnter */vim-dashboard/*.tmp call dashboard#setup_dashboard_buffer()
  autocmd FileChangedShell */dashboard/*.tmp call dashboard#handle_file_changed()
  autocmd FileChangedShell */vim-dashboard/*.tmp call dashboard#handle_file_changed()
augroup END

" Key mappings (optional)
if get(g:, 'dashboard_enable_mappings', 1)
  nnoremap <leader>ds :DashboardStart<space>
  nnoremap <leader>dr :DashboardRestart<cr>
  nnoremap <leader>dt :DashboardStop<cr>
  nnoremap <leader>dl :DashboardList<cr>
  nnoremap <leader>dd :Dashboard<cr>
endif