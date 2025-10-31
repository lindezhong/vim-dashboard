"""
Table chart implementation using Rich
"""

from typing import Dict, Any, List, Optional, Union
from rich.table import Table
from rich.text import Text
from rich.console import Console
from .base import BaseChart, ChartRenderer
from ..utils import truncate_string


class TableChart(BaseChart):
    """Table chart implementation using Rich Table."""
    
    def __init__(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        super().__init__(data, config)
        self.show_config = config.get('show', {})
        self.column_list = self.show_config.get('column_list', [])
        
    def _get_columns_info(self) -> List[Dict[str, str]]:
        """Get column information from config or auto-detect from data."""
        if self.column_list:
            return self.column_list
        
        # Auto-detect columns from first row of data
        if self.data:
            first_row = self.data[0]
            columns = []
            for key in first_row.keys():
                columns.append({
                    'column': key,
                    'alias': key
                })
            return columns
        
        return []
    
    def _get_table_style(self) -> Dict[str, Any]:
        """Get table styling options."""
        return {
            'show_header': self.style.get('show_header', True),
            'show_lines': self.style.get('show_lines', True),
            'show_edge': self.style.get('show_edge', True),
            'header_style': self.style.get('header_style', 'bold magenta'),
            'row_styles': self.style.get('row_styles', ['none', 'dim']),
            'border_style': self.style.get('border_style', 'blue'),
            'caption_style': self.style.get('caption_style', 'italic'),
            'min_width': self.style.get('min_width'),
            'max_width': self.style.get('max_width'),
            'expand': self.style.get('expand', False),
            'collapse_padding': self.style.get('collapse_padding', False)
        }
    
    def _format_cell_value(self, value: Any, column_config: Dict[str, Any]) -> str:
        """Format cell value based on column configuration."""
        if value is None:
            return self.style.get('null_value', 'NULL')
        
        # Convert to string
        str_value = str(value)
        
        # Apply truncation if specified
        max_length = column_config.get('max_length') or self.style.get('max_cell_length')
        if max_length:
            str_value = truncate_string(str_value, int(max_length))
        
        return str_value
    
    def _create_rich_table(self) -> Table:
        """Create Rich Table object with proper styling."""
        table_style = self._get_table_style()
        
        # Create table with styling
        table = Table(
            show_header=table_style['show_header'],
            show_lines=table_style['show_lines'],
            show_edge=table_style['show_edge'],
            header_style=table_style['header_style'],
            row_styles=table_style['row_styles'],
            border_style=table_style['border_style'],
            min_width=table_style['min_width'],
            expand=table_style['expand'],
            collapse_padding=table_style['collapse_padding']
        )
        
        # Set max width if specified
        if table_style['max_width']:
            table.width = table_style['max_width']
        
        return table
    
    def _add_columns_to_table(self, table: Table, columns_info: List[Dict[str, str]]) -> None:
        """Add columns to the Rich table."""
        for col_config in columns_info:
            column_name = col_config.get('column', '')
            alias = col_config.get('alias', column_name)
            
            # Column styling
            justify = col_config.get('justify', 'left')
            style = col_config.get('style')
            header_style = col_config.get('header_style')
            footer_style = col_config.get('footer_style')
            width = col_config.get('width')
            min_width = col_config.get('min_width')
            max_width = col_config.get('max_width')
            ratio = col_config.get('ratio')
            no_wrap = col_config.get('no_wrap', False)
            
            table.add_column(
                alias,
                justify=justify,
                style=style,
                header_style=header_style,
                footer_style=footer_style,
                width=width,
                min_width=min_width,
                max_width=max_width,
                ratio=ratio,
                no_wrap=no_wrap
            )
    
    def _add_rows_to_table(self, table: Table, columns_info: List[Dict[str, str]]) -> None:
        """Add data rows to the Rich table."""
        max_rows = self.style.get('max_rows')
        row_count = 0
        
        for row_data in self.data:
            if max_rows and row_count >= max_rows:
                # Add truncation indicator
                truncation_msg = f"... ({len(self.data) - max_rows} more rows)"
                row_values = [truncation_msg] + [''] * (len(columns_info) - 1)
                table.add_row(*row_values, style='dim italic')
                break
            
            # Extract values for each column
            row_values = []
            for col_config in columns_info:
                column_name = col_config.get('column', '')
                value = row_data.get(column_name)
                formatted_value = self._format_cell_value(value, col_config)
                row_values.append(formatted_value)
            
            table.add_row(*row_values)
            row_count += 1
    
    def _add_caption_if_configured(self, table: Table) -> None:
        """Add caption to table if configured."""
        caption = self.style.get('caption')
        if caption:
            table.caption = caption
            table.caption_style = self.style.get('caption_style', 'italic')
    
    def render(self) -> str:
        """Render table chart."""
        columns_info = self._get_columns_info()
        
        if not columns_info:
            return self._handle_empty_data()
        
        # Create Rich table
        table = self._create_rich_table()
        
        # Add columns
        self._add_columns_to_table(table, columns_info)
        
        # Add rows
        self._add_rows_to_table(table, columns_info)
        
        # Add caption if configured
        self._add_caption_if_configured(table)
        
        # Render to string
        with self.console.capture() as capture:
            self.console.print(table)
        
        return capture.get()


# Register the table chart
ChartRenderer.register_chart_class('table', TableChart)