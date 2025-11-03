"""
Table chart implementation using Rich
"""

from typing import Dict, Any, List, Optional, Union
from rich.table import Table
from rich.text import Text
from rich.console import Console
from .base import BaseChart, ChartRenderer
from ..utils import truncate_string
import re

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
        style_config = self.show_config.get('style', {})
        return {
            'show_header': style_config.get('show_header', True),
            'show_lines': style_config.get('show_lines', True),
            'show_edge': style_config.get('show_edge', True),
            'border': style_config.get('border', True),
            'header_style': style_config.get('header_style', 'bold blue'),
            'row_styles': style_config.get('row_styles', ['', 'dim']),
            'border_style': style_config.get('border_style', 'blue'),
            'caption_style': style_config.get('caption_style', 'italic'),
            'min_width': style_config.get('min_width'),
            'max_width': style_config.get('max_width'),
            'expand': style_config.get('expand', False),
            'collapse_padding': style_config.get('collapse_padding', False)
        }

    def _format_cell_value(self, value: Any, column_config: Dict[str, Any]) -> str:
        """Format cell value based on column configuration."""
        if value is None:
            return self.style.get('null_value', 'NULL')

        # Apply format string if specified
        format_str = column_config.get('format')
        if format_str:
            try:
                if isinstance(value, (int, float)):
                    # Handle numeric formatting like "¥{:,}" or "{:>3d}"
                    if '{:' in format_str:
                        # Extract format specification
                        format_match = re.search(r'\{:([^}]+)\}', format_str)
                        if format_match:
                            format_spec = format_match.group(1)
                            formatted_number = format(value, format_spec)
                            # Replace the format placeholder with formatted number
                            str_value = format_str.replace('{:' + format_spec + '}', formatted_number)
                        else:
                            str_value = format_str.format(value)
                    else:
                        # Simple format string like "¥{}"
                        str_value = format_str.format(value)
                else:
                    str_value = format_str.format(value)
            except (ValueError, TypeError):
                # Fallback to string conversion if formatting fails
                str_value = str(value)
        else:
            # Convert to string
            str_value = str(value)

        # Apply truncation if specified
        max_length = column_config.get('max_length') or self.style.get('max_cell_length')
        if max_length:
            str_value = truncate_string(str_value, int(max_length))

        return str_value

    def _sort_data_if_configured(self) -> List[Dict[str, Any]]:
        """Sort data based on sort configuration."""
        sort_config = self.show_config.get('sort', {})

        # If sort config exists and has a column, enable sorting
        # Support both explicit enabled field and implicit (if column is specified)
        sort_enabled = sort_config.get('enabled', True) if sort_config.get('column') else False
        if not sort_enabled:
            return self.data

        sort_column = sort_config.get('column')
        sort_order = sort_config.get('order', 'asc')

        if not sort_column:
            return self.data

        try:
            # Sort data
            reverse_order = sort_order.lower() == 'desc'
            sorted_data = sorted(
                self.data,
                key=lambda x: x.get(sort_column, 0),
                reverse=reverse_order
            )
            return sorted_data
        except (TypeError, KeyError):
            # Return original data if sorting fails
            return self.data

    def _apply_pagination(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply pagination if configured."""
        pagination_config = self.show_config.get('pagination', {})
        if not pagination_config.get('enabled', False):
            return data

        page_size = pagination_config.get('page_size', 10)
        # For now, just show first page
        return data[:page_size]

    def _create_rich_table(self) -> Table:
        """Create Rich Table object with proper styling."""
        table_style = self._get_table_style()

        # Create table with styling
        table = Table(
            show_header=table_style['show_header'],
            show_lines=table_style['show_lines'],
            show_edge=table_style['show_edge'] and table_style['border'],
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

            # Column styling - support both old and new config formats
            # Prioritize 'align' over 'justify' for consistency with example configs
            justify = col_config.get('align') or col_config.get('justify', 'left')
            style = col_config.get('style')
            header_style = col_config.get('header_style')
            footer_style = col_config.get('footer_style')
            width = col_config.get('width')
            min_width = col_config.get('min_width')
            max_width = col_config.get('max_width')
            ratio = col_config.get('ratio')
            no_wrap = col_config.get('no_wrap', False)

            # Handle color mapping for cells
            color_map = col_config.get('color_map', {})
            if color_map:
                # Store color map for later use in row rendering
                col_config['_color_map'] = color_map

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

    def _add_rows_to_table(self, table: Table, columns_info: List[Dict[str, str]], data: List[Dict[str, Any]]) -> None:
        """Add data rows to the Rich table."""
        max_rows = self.style.get('max_rows')
        row_count = 0

        for row_data in data:
            if max_rows and row_count >= max_rows:
                # Add truncation indicator
                truncation_msg = f"... ({len(data) - max_rows} more rows)"
                row_values = [truncation_msg] + [''] * (len(columns_info) - 1)
                table.add_row(*row_values, style='dim italic')
                break

            # Extract values for each column
            row_values = []
            for col_config in columns_info:
                column_name = col_config.get('column', '')
                value = row_data.get(column_name)
                formatted_value = self._format_cell_value(value, col_config)

                # Apply color mapping if configured
                color_map = col_config.get('color_map', {})
                if color_map and str(value) in color_map:
                    color = color_map[str(value)]
                    formatted_value = f"[{color}]{formatted_value}[/{color}]"

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

        # Sort data if configured
        sorted_data = self._sort_data_if_configured()

        # Apply pagination if configured
        paginated_data = self._apply_pagination(sorted_data)

        # Create Rich table
        table = self._create_rich_table()

        # Add columns
        self._add_columns_to_table(table, columns_info)

        # Add rows - even if no data, still show table with headers
        if paginated_data:
            self._add_rows_to_table(table, columns_info, paginated_data)
        else:
            # Add a single row with "No data available" message
            no_data_msg = "No data available"
            empty_row = [no_data_msg] + [''] * (len(columns_info) - 1)
            table.add_row(*empty_row, style='dim italic')

        # Add caption if configured
        self._add_caption_if_configured(table)

        # Render to string
        with self.console.capture() as capture:
            self.console.print(table)

        return capture.get()

# Register the table chart
ChartRenderer.register_chart_class('table', TableChart)