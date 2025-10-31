"""
vim-dashboard - Database Dashboard Plugin for Vim/Neovim
Author: vim-dashboard team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "vim-dashboard team"

# Import main modules for easy access
from .core import DashboardCore
from .config import ConfigManager
from .database import DatabaseManager
from .charts import ChartRenderer

__all__ = [
    'DashboardCore',
    'ConfigManager', 
    'DatabaseManager',
    'ChartRenderer'
]