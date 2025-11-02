"""
SQL Template Engine using Jinja2
Supports dynamic SQL generation with variables, conditions, and loops
"""

import re
from typing import Dict, Any, List, Optional, Union
from jinja2 import Environment, BaseLoader, StrictUndefined, TemplateSyntaxError
from jinja2.exceptions import UndefinedError
import logging

logger = logging.getLogger(__name__)


class SQLTemplateEngine:
    """SQL Template Engine using Jinja2 with SQL-specific features."""
    
    def __init__(self):
        """Initialize the template engine with SQL-safe configuration."""
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # SQL doesn't need HTML escaping
            undefined=StrictUndefined,  # Strict mode - undefined variables raise errors
            trim_blocks=True,  # Remove newlines after block tags
            lstrip_blocks=True,  # Strip leading whitespace before block tags
        )
        
        # Register SQL-specific filters
        self._register_sql_filters()
        
        # Register SQL-specific functions
        self._register_sql_functions()
    
    def _register_sql_filters(self):
        """Register custom filters for SQL operations."""
        
        def sql_escape(value):
            """Escape SQL string literals."""
            if value is None:
                return 'NULL'
            if isinstance(value, str):
                # Escape single quotes by doubling them
                return value.replace("'", "''")
            return str(value)
        
        def sql_quote(value):
            """Quote SQL string literals."""
            if value is None:
                return 'NULL'
            if isinstance(value, str):
                return f"'{sql_escape(value)}'"
            return str(value)
        
        def sql_in_clause(values):
            """Generate SQL IN clause from list of values."""
            if not values:
                return 'NULL'
            
            quoted_values = []
            for val in values:
                if val is None:
                    quoted_values.append('NULL')
                elif isinstance(val, str):
                    quoted_values.append(f"'{sql_escape(val)}'")
                else:
                    quoted_values.append(str(val))
            
            return f"({', '.join(quoted_values)})"
        
        def sql_identifier(value):
            """Quote SQL identifiers (table names, column names)."""
            if not isinstance(value, str):
                raise ValueError("SQL identifier must be a string")
            
            # Simple validation - only allow alphanumeric and underscore
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
                raise ValueError(f"Invalid SQL identifier: {value}")
            
            return f'`{value}`'
        
        def sql_limit(value):
            """Format LIMIT clause value."""
            if value is None:
                return ''
            
            try:
                limit_val = int(value)
                if limit_val <= 0:
                    raise ValueError("LIMIT value must be positive")
                return str(limit_val)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid LIMIT value: {value}")
        
        # Register filters
        self.env.filters.update({
            'sql_escape': sql_escape,
            'sql_quote': sql_quote,
            'sql_in': sql_in_clause,
            'sql_id': sql_identifier,
            'sql_limit': sql_limit,
        })
    
    def _register_sql_functions(self):
        """Register custom functions for SQL operations."""
        
        def sql_case(conditions, default=None):
            """Generate SQL CASE statement."""
            if not conditions:
                return str(default) if default is not None else 'NULL'
            
            case_parts = ['CASE']
            for condition, value in conditions.items():
                case_parts.append(f"WHEN {condition} THEN {value}")
            
            if default is not None:
                case_parts.append(f"ELSE {default}")
            
            case_parts.append('END')
            return ' '.join(case_parts)
        
        def sql_concat(*args):
            """Generate SQL CONCAT function."""
            if not args:
                return "''"
            
            quoted_args = []
            for arg in args:
                if isinstance(arg, str):
                    quoted_args.append(f"'{self.env.filters['sql_escape'](arg)}'")
                else:
                    quoted_args.append(str(arg))
            
            return f"CONCAT({', '.join(quoted_args)})"
        
        # Register functions in global namespace
        self.env.globals.update({
            'sql_case': sql_case,
            'sql_concat': sql_concat,
        })
    
    def render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        Render SQL template with given context.
        
        Args:
            template_str: Jinja2 template string
            context: Variables to use in template
            
        Returns:
            Rendered SQL string
            
        Raises:
            TemplateSyntaxError: If template syntax is invalid
            UndefinedError: If required variable is missing
            ValueError: If SQL-specific validation fails
        """
        try:
            # Compile template
            template = self.env.from_string(template_str)
            
            # Render with context
            rendered_sql = template.render(**context)
            
            # Post-process: clean up whitespace
            rendered_sql = self._clean_sql(rendered_sql)
            
            # Validate rendered SQL
            self._validate_sql_safety(rendered_sql)
            
            return rendered_sql
            
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise
        except UndefinedError as e:
            logger.error(f"Undefined variable in template: {e}")
            raise
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up rendered SQL string."""
        # Remove excessive whitespace
        sql = re.sub(r'\s+', ' ', sql.strip())
        
        # Remove empty lines
        lines = [line.strip() for line in sql.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def _validate_sql_safety(self, sql: str) -> None:
        """
        Validate SQL for basic safety.
        
        Args:
            sql: SQL string to validate
            
        Raises:
            ValueError: If SQL contains dangerous patterns
        """
        sql_upper = sql.upper()
        
        # Check for dangerous keywords (basic protection)
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
            'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_keywords:
            if f' {keyword} ' in f' {sql_upper} ':
                raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
        
        # Check for SQL injection patterns
        injection_patterns = [
            r';\s*\w',  # Multiple statements (potential injection)
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE | re.DOTALL):
                raise ValueError(f"Potentially dangerous SQL pattern detected: {pattern}")

        # Allow SQL comments (-- and /* */) as they are legitimate SQL syntax
    
    def validate_template(self, template_str: str) -> tuple[bool, Optional[str]]:
        """
        Validate template syntax without rendering.
        
        Args:
            template_str: Template string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.env.from_string(template_str)
            return True, None
        except TemplateSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"


class ParameterManager:
    """Manages template parameters with type validation and default values."""
    
    def __init__(self):
        self.parameters = {}
    
    def define_parameter(self, name: str, param_type: str, default_value: Any = None, 
                        description: str = "", required: bool = False) -> None:
        """
        Define a template parameter.
        
        Args:
            name: Parameter name
            param_type: Parameter type ('string', 'number', 'boolean', 'list', 'map')
            default_value: Default value
            description: Parameter description
            required: Whether parameter is required
        """
        self.parameters[name] = {
            'type': param_type,
            'default': default_value,
            'description': description,
            'required': required
        }
    
    def validate_and_prepare_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate arguments and prepare template context.
        
        Args:
            args: Runtime arguments
            
        Returns:
            Validated context dictionary
            
        Raises:
            ValueError: If validation fails
        """
        context = {}
        
        # Check all defined parameters
        for param_name, param_def in self.parameters.items():
            value = args.get(param_name)
            
            # Handle missing values
            if value is None:
                if param_def['required']:
                    raise ValueError(f"Required parameter '{param_name}' is missing")
                value = param_def['default']
            
            # Always add parameter to context, even if None (for optional parameters)
            # This allows Jinja2 templates to use default filters like {{ param | default("") }}
            if value is not None:
                validated_value = self._validate_parameter_type(
                    param_name, value, param_def['type']
                )
                context[param_name] = validated_value
            else:
                # Add None for optional parameters without defaults
                context[param_name] = None
        
        # Add any extra arguments (with warning)
        for arg_name, arg_value in args.items():
            if arg_name not in self.parameters:
                logger.warning(f"Unknown parameter '{arg_name}' provided")
                context[arg_name] = arg_value
        
        return context
    
    def _validate_parameter_type(self, name: str, value: Any, expected_type: str) -> Any:
        """
        Validate parameter type and convert if necessary.
        
        Args:
            name: Parameter name
            value: Parameter value
            expected_type: Expected type
            
        Returns:
            Validated/converted value
            
        Raises:
            ValueError: If type validation fails
        """
        if expected_type == 'string':
            if not isinstance(value, str):
                return str(value)
            return value
        
        elif expected_type == 'number':
            if isinstance(value, (int, float)):
                return value
            try:
                # Try to convert string to number
                if isinstance(value, str):
                    if '.' in value:
                        return float(value)
                    else:
                        return int(value)
                return float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Parameter '{name}' must be a number, got {type(value).__name__}")
        
        elif expected_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'yes', 'on'):
                    return True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    return False
            raise ValueError(f"Parameter '{name}' must be a boolean, got {type(value).__name__}")
        
        elif expected_type == 'list':
            if isinstance(value, list):
                return value
            raise ValueError(f"Parameter '{name}' must be a list, got {type(value).__name__}")
        
        elif expected_type == 'map':
            if isinstance(value, dict):
                return value
            raise ValueError(f"Parameter '{name}' must be a map/dict, got {type(value).__name__}")
        
        else:
            raise ValueError(f"Unknown parameter type: {expected_type}")
    
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all defined parameters."""
        return self.parameters.copy()


class SQLTemplateProcessor:
    """High-level processor that combines template engine and parameter management."""
    
    def __init__(self):
        self.template_engine = SQLTemplateEngine()
        self.parameter_manager = ParameterManager()
    
    def process_config_parameters(self, config: Dict[str, Any]) -> None:
        """
        Process parameter definitions from config.
        
        Args:
            config: Configuration dictionary containing 'args' section
        """
        args_config = config.get('args', [])
        
        for arg_def in args_config:
            if not isinstance(arg_def, dict):
                continue

            # Support both 'name' and 'key' fields for parameter name
            param_name = arg_def.get('name') or arg_def.get('key')
            if not param_name:
                continue
            param_type = arg_def.get('type', 'string')
            default_value = arg_def.get('default')
            description = arg_def.get('description', '')
            required = arg_def.get('required', False)
            
            self.parameter_manager.define_parameter(
                param_name, param_type, default_value, description, required
            )
    
    def render_sql(self, template_str: str, runtime_args: Dict[str, Any] = None) -> str:
        """
        Render SQL template with runtime arguments.
        
        Args:
            template_str: SQL template string
            runtime_args: Runtime arguments to override defaults
            
        Returns:
            Rendered SQL string
        """
        if runtime_args is None:
            runtime_args = {}
        
        # Validate and prepare context
        context = self.parameter_manager.validate_and_prepare_context(runtime_args)
        
        # Render template
        return self.template_engine.render_template(template_str, context)
    
    def validate_template(self, template_str: str) -> tuple[bool, Optional[str]]:
        """Validate template syntax."""
        return self.template_engine.validate_template(template_str)
    
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """Get parameter information."""
        return self.parameter_manager.get_parameter_info()