"""
Configuration management for vim-dashboard
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from .utils import validate_config_structure, parse_interval, safe_get_nested
from .template import SQLTemplateProcessor


class ConfigManager:
    """Manages dashboard configuration loading and validation."""
    
    def __init__(self):
        self.config: Optional[Dict[str, Any]] = None
        self.config_path: Optional[str] = None
        self.template_processor: Optional[SQLTemplateProcessor] = None

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file: {e}")
        
        # Validate config structure
        is_valid, error_msg = validate_config_structure(config)
        if not is_valid:
            raise ValueError(f"Invalid config: {error_msg}")
        
        # Apply defaults and normalize
        config = self._apply_defaults(config)
        config = self._normalize_config(config)
        
        # Initialize template processor if args are defined
        query_config = config.get('query', {})
        if isinstance(query_config, dict) and 'args' in query_config:
            self.template_processor = SQLTemplateProcessor()
            # Pass the args from query.args to the template processor
            config_with_args = {'args': query_config['args']}
            self.template_processor.process_config_parameters(config_with_args)
            # Apply default values to template processor
            self.template_processor.apply_defaults()

        self.config = config
        self.config_path = config_path
        return config
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to configuration."""
        # Default interval
        if 'interval' not in config:
            config['interval'] = '30s'
        
        # Default show configuration
        show_config = config.get('show', {})
        if 'style' not in show_config:
            show_config['style'] = {}
        
        # Apply chart-specific defaults
        chart_type = show_config.get('type', 'table')
        show_config['style'] = self._apply_chart_defaults(chart_type, show_config['style'])
        
        config['show'] = show_config
        return config
    
    def _apply_chart_defaults(self, chart_type: str, style: Dict[str, Any]) -> Dict[str, Any]:
        """Apply chart-specific default styles."""
        defaults = {
            'table': {
                'title_style': 'bold magenta',
                'header_style': 'bold cyan',
                'border_style': 'blue',
                'show_header': True,
                'show_lines': True,
                'width': None,  # Auto-fit
            },
            'bar': {
                'title_style': 'bold magenta',
                'bar_style': 'blue',
                'value_style': 'bold white',
                'label_style': 'green',
                'width': 60,
                'height': 20,
            },
            'line': {
                'title_style': 'bold magenta',
                'line_style': 'green',
                'point_style': 'bold green',
                'axis_style': 'white',
                'width': 80,
                'height': 20,
                'grid': True,
            },
            'pie': {
                'title_style': 'bold magenta',
                'show_percentage': True,
                'colors': ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan'],
                'radius': 10,
            },
            'scatter': {
                'title_style': 'bold magenta',
                'point_style': 'blue',
                'axis_style': 'white',
                'width': 60,
                'height': 20,
                'point_char': '●',
            }
        }
        
        chart_defaults = defaults.get(chart_type, {})
        
        # Merge defaults with user style, user style takes precedence
        merged_style = chart_defaults.copy()
        merged_style.update(style)
        
        return merged_style
    
    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize configuration values."""
        # Parse interval to seconds
        interval_str = config.get('interval', '30s')
        config['interval_seconds'] = parse_interval(interval_str)
        
        # Normalize database URL
        db_config = config.get('database', {})
        if 'type' not in db_config and 'url' in db_config:
            # Extract type from URL
            url = db_config['url']
            if '://' in url:
                db_type = url.split('://')[0]
                db_config['type'] = db_type
        
        # Normalize column configurations
        show_config = config.get('show', {})
        if show_config.get('type') == 'table':
            columns = show_config.get('columns', show_config.get('column_list', []))
            if columns:
                show_config['columns'] = self._normalize_columns(columns)
        
        return config
    
    def _normalize_columns(self, columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize column configurations."""
        normalized = []
        for col in columns:
            if isinstance(col, dict):
                normalized_col = {
                    'column': col.get('column', ''),
                    'alias': col.get('alias', col.get('column', '')),
                    'width': col.get('width', None),
                    'style': col.get('style', None),
                }
                normalized.append(normalized_col)
        return normalized
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        if not self.config:
            raise ValueError("No configuration loaded")
        return self.config.get('database', {})
    
    def get_query(self) -> str:
        """Get SQL query with template rendering if needed."""
        if not self.config:
            raise ValueError("No configuration loaded")

        query_config = self.config.get('query', '')

        # Support both old format (query as string) and new format (query as dict with sql)
        if isinstance(query_config, dict):
            query_template = query_config.get('sql', '')
        else:
            query_template = query_config

        # If template processor is available, render the template
        if self.template_processor and query_template:
            try:
                return self.template_processor.render_sql(query_template)
            except Exception as e:
                raise ValueError(f"Template rendering error: {e}")

        return query_template
    
    def get_interval_seconds(self) -> int:
        """Get refresh interval in seconds."""
        if not self.config:
            raise ValueError("No configuration loaded")
        return self.config.get('interval_seconds', 30)
    
    def get_show_config(self) -> Dict[str, Any]:
        """Get display configuration."""
        if not self.config:
            raise ValueError("No configuration loaded")
        return self.config.get('show', {})
    
    def get_chart_type(self) -> str:
        """Get chart type."""
        show_config = self.get_show_config()
        return show_config.get('type', 'table')
    
    def get_chart_style(self) -> Dict[str, Any]:
        """Get chart style configuration."""
        show_config = self.get_show_config()
        return show_config.get('style', {})
    
    def get_title(self) -> Optional[str]:
        """Get dashboard title."""
        if not self.config:
            return None
        return self.config.get('title', safe_get_nested(self.config, ['show', 'title']))
    
    def validate_chart_config(self) -> tuple[bool, Optional[str]]:
        """Validate chart-specific configuration."""
        if not self.config:
            return False, "No configuration loaded"
        
        show_config = self.get_show_config()
        chart_type = show_config.get('type', 'table')
        
        # Chart-specific validation
        if chart_type == 'table':
            return self._validate_table_config(show_config)
        elif chart_type in ['bar', 'line', 'scatter']:
            return self._validate_xy_chart_config(show_config)
        elif chart_type == 'pie':
            return self._validate_pie_config(show_config)
        else:
            return True, None  # Other chart types are valid by default
    
    def _validate_table_config(self, show_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate table configuration."""
        columns = show_config.get('columns', [])
        if not columns:
            return True, None  # No columns config is valid, will show all columns
        
        for i, col in enumerate(columns):
            if not isinstance(col, dict):
                return False, f"Column {i} must be a dictionary"
            if 'column' not in col:
                return False, f"Column {i} missing 'column' field"
        
        return True, None
    
    def _validate_xy_chart_config(self, show_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate X-Y chart configuration."""
        if 'x_column' not in show_config:
            return False, "Missing x_column for chart"
        if 'y_column' not in show_config:
            return False, "Missing y_column for chart"
        return True, None
    
    def _validate_pie_config(self, show_config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate pie chart configuration."""
        if 'label_column' not in show_config:
            return False, "Missing label_column for pie chart"
        if 'value_column' not in show_config:
            return False, "Missing value_column for pie chart"
        return True, None
    
    def reload_config(self) -> Dict[str, Any]:
        """Reload configuration from the same file."""
        if not self.config_path:
            raise ValueError("No config file path available for reload")
        return self.load_config(self.config_path)

    def render_query(self, runtime_args: Dict[str, Any] = None) -> str:
        """
        Render SQL query with template variables.

        Args:
            runtime_args: Runtime arguments to override defaults

        Returns:
            Rendered SQL query string
        """
        if not self.config:
            raise ValueError("No configuration loaded")

        query_template = self.config.get('query', '')

        # If no template processor, return query as-is
        if not self.template_processor:
            return query_template

        # Render template with runtime arguments
        return self.template_processor.render_sql(query_template, runtime_args or {})

    def get_template_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about template parameters.

        Returns:
            Dictionary of parameter information
        """
        if not self.template_processor:
            return {}

        return self.template_processor.get_parameter_info()

    def validate_template_syntax(self) -> tuple[bool, Optional[str]]:
        """
        Validate SQL template syntax.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.config:
            return False, "No configuration loaded"

        query_template = self.config.get('query', '')

        if not self.template_processor:
            return True, None  # No template processing needed

        return self.template_processor.validate_template(query_template)

    def get_args_config(self) -> List[Dict[str, Any]]:
        """Get template arguments configuration."""
        if not self.config:
            return []

        # Support both old format (args at root) and new format (args under query)
        query_config = self.config.get('query', {})
        if isinstance(query_config, dict) and 'args' in query_config:
            return query_config.get('args', [])
        else:
            # Fallback to old format
            return self.config.get('args', [])