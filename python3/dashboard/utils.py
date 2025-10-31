"""
Utility functions for vim-dashboard
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional


def get_platform_temp_dir() -> str:
    """Get platform-specific temporary directory for dashboard files."""
    if sys.platform.startswith('win'):
        temp_base = os.environ.get('TEMP', tempfile.gettempdir())
    else:
        temp_base = '/tmp'
    
    dashboard_temp = os.path.join(temp_base, 'vim-dashboard')
    os.makedirs(dashboard_temp, exist_ok=True)
    return dashboard_temp


def get_platform_config_dir() -> str:
    """Get platform-specific config directory."""
    try:
        # Try to get home directory using multiple methods
        home_dir = None

        # Method 1: Try environment variables first
        if sys.platform.startswith('win'):
            home_dir = os.environ.get('USERPROFILE') or os.environ.get('HOMEPATH')
        else:
            home_dir = os.environ.get('HOME')

        # Method 2: Try os.path.expanduser if env vars failed
        if not home_dir:
            try:
                home_dir = os.path.expanduser('~')
                # Validate that expanduser actually worked
                if home_dir == '~':
                    home_dir = None
            except:
                home_dir = None

        # Method 3: Try pathlib.Path.home() as fallback
        if not home_dir:
            try:
                home_dir = str(Path.home())
            except:
                home_dir = None

        # Method 4: Use current working directory as last resort
        if not home_dir:
            home_dir = os.getcwd()

        config_dir = os.path.join(home_dir, 'dashboard')
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    except Exception as e:
        # Ultimate fallback: use temp directory
        temp_dir = get_platform_temp_dir()
        config_dir = os.path.join(temp_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)
        return config_dir


def generate_temp_filename(extension: str = 'tmp') -> str:
    """Generate a unique temporary filename."""
    temp_dir = get_platform_temp_dir()
    filename = f"{uuid.uuid4().hex}.{extension}"
    return os.path.join(temp_dir, filename)


def parse_interval(interval_str: str) -> int:
    """Parse interval string (e.g., '30s', '5m', '1h') to seconds."""
    if not interval_str:
        return 30  # default 30 seconds
    
    interval_str = interval_str.strip().lower()
    
    # Extract number and unit
    if interval_str[-1] in 'smh':
        try:
            number = int(interval_str[:-1])
            unit = interval_str[-1]
        except ValueError:
            return 30
    else:
        try:
            number = int(interval_str)
            unit = 's'  # default to seconds
        except ValueError:
            return 30
    
    # Convert to seconds
    multipliers = {'s': 1, 'm': 60, 'h': 3600}
    return number * multipliers.get(unit, 1)


def safe_get_nested(data: dict, keys: list, default=None):
    """Safely get nested dictionary value."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def validate_config_structure(config: dict) -> tuple[bool, Optional[str]]:
    """Validate basic config structure."""
    required_keys = ['database', 'query', 'show']
    
    for key in required_keys:
        if key not in config:
            return False, f"Missing required key: {key}"
    
    # Validate database section
    db_config = config.get('database', {})
    if 'url' not in db_config:
        return False, "Missing database.url"
    
    # Validate show section
    show_config = config.get('show', {})
    if 'type' not in show_config:
        return False, "Missing show.type"
    
    return True, None


def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message for display."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"[{context}] {error_type}: {error_msg}"
    else:
        return f"{error_type}: {error_msg}"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def ensure_directory_exists(path: str) -> bool:
    """Ensure directory exists, create if necessary."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False