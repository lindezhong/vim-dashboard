" Vim syntax file for dashboard files
" Language: Dashboard
" Maintainer: Dashboard Plugin
" Latest Revision: 2024

if exists("b:current_syntax")
  finish
endif

" Keywords
syn keyword dashboardKeyword Database Query Interval Show Type
syn keyword dashboardType table bar line pie scatter area histogram boxplot heatmap bubble
syn keyword dashboardDatabase mysql postgres sqlite oracle mssql redis mongodb cassandra

" Numbers
syn match dashboardNumber '\d\+'
syn match dashboardFloat '\d\+\.\d\+'

" Strings
syn region dashboardString start='"' end='"' contained
syn region dashboardString start="'" end="'" contained

" Comments (for chart headers and info)
syn match dashboardComment '^#.*$'
syn match dashboardComment '│.*│'
syn match dashboardComment '┌.*┐'
syn match dashboardComment '└.*┘'
syn match dashboardComment '├.*┤'

" Chart elements
syn match dashboardChart '[│┌┐└┘├┤┬┴┼─]'
syn match dashboardChart '[▸▾●◆▲■♦]'

" Status indicators
syn match dashboardStatus 'Running\|Idle\|Error\|Refreshing'
syn match dashboardTime '\d\{1,2\}:\d\{2\}\(:\d\{2\}\)\?'

" Countdown info
syn match dashboardCountdown 'Next refresh:.*$'

" Define the default highlighting
hi def link dashboardKeyword     Keyword
hi def link dashboardType        Type
hi def link dashboardDatabase    Constant
hi def link dashboardNumber      Number
hi def link dashboardFloat       Float
hi def link dashboardString      String
hi def link dashboardComment     Comment
hi def link dashboardChart       Special
hi def link dashboardStatus      Statement
hi def link dashboardTime        Number
hi def link dashboardCountdown   PreProc

let b:current_syntax = "dashboard"