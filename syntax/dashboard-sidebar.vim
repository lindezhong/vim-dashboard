" Vim syntax file for dashboard sidebar
" Language: Dashboard Sidebar
" Maintainer: Dashboard Plugin
" Latest Revision: 2024

if exists("b:current_syntax")
  finish
endif

" Header
syn match dashboardSidebarHeader '^Dashboard Sidebar$'
syn match dashboardSidebarDirectory '^Directory:.*$'

" Status indicators
syn match dashboardSidebarRunning '^▾.*$'
syn match dashboardSidebarStopped '^▸.*$'

" Legend
syn match dashboardSidebarLegend '^▸ = Not running$'
syn match dashboardSidebarLegend '^▾ = Running$'

" Status icons
syn match dashboardSidebarIcon '[▸▾]'

" Define the default highlighting
hi def link dashboardSidebarHeader     Title
hi def link dashboardSidebarDirectory  Comment
hi def link dashboardSidebarRunning    String
hi def link dashboardSidebarStopped    Comment
hi def link dashboardSidebarLegend     PreProc
hi def link dashboardSidebarIcon       Special

let b:current_syntax = "dashboard-sidebar"