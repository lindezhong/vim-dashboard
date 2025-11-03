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
command! -nargs=1 -complete=file DashboardStart call dashboard#start(<q-args>)
command! -nargs=0 DashboardRestart call dashboard#restart()
command! -nargs=? -complete=file DashboardStop call dashboard#stop(<q-args>)
command! -nargs=0 DashboardList call dashboard#list()
command! -nargs=0 DashboardStatus call dashboard#status()
command! -nargs=0 Dashboard call dashboard#browse()
command! -nargs=0 DashboardClose call dashboard#close()
" Variable management commands
command! -nargs=0 DashboardShowVariables call dashboard#show_variables()
command! -nargs=0 DashboardModifyVariable call dashboard#modify_variable()
command! -nargs=* DashboardUpdateVariable call dashboard#update_variable(<f-args>)
command! -nargs=0 DashboardResetVariables call dashboard#reset_variables()
" SQL viewing command
command! -nargs=0 DashboardShowSQL call dashboard#show_sql()

" Session management commands
command! -nargs=? -bang -complete=file DashboardMksession call dashboard#enhanced_mksession(<bang>0, <q-args>)

" Override standard mksession command to handle dashboard buffers automatically
command! -nargs=? -bang -complete=file -range Mksession call dashboard#enhanced_mksession(<bang>0, <q-args>)

" Create command abbreviation to intercept mksession calls
cnoreabbrev <expr> mksession (getcmdtype() == ':' && getcmdline() == 'mksession') ? 'DashboardMksession' : 'mksession'

" Auto commands
augroup DashboardPlugin
  autocmd!
  autocmd VimEnter * call dashboard#init()
  autocmd VimLeave * call dashboard#cleanup()
  " Auto-reload dashboard temp files when they change
  autocmd BufRead,BufEnter */dashboard/*.dashboard call dashboard#setup_dashboard_buffer()
  autocmd BufRead,BufEnter */vim-dashboard/*.dashboard call dashboard#setup_dashboard_buffer()
  autocmd FileChangedShell */dashboard/*.dashboard call dashboard#handle_file_changed()
  autocmd FileChangedShell */vim-dashboard/*.dashboard call dashboard#handle_file_changed()

  " Handle session restore - check for .dashboard files after session load
  autocmd SessionLoadPost * call dashboard#handle_session_dashboard_files()
augroup END

" Key mappings (optional)
if get(g:, 'dashboard_enable_mappings', 1)
  nnoremap <leader>ds :DashboardStart<space>
  nnoremap <leader>dr :DashboardRestart<cr>
  nnoremap <leader>dt :DashboardStop<cr>
  nnoremap <leader>dl :DashboardList<cr>
  nnoremap <leader>dd :Dashboard<cr>
endif