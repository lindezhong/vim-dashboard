"""
Pie chart implementation for vim-dashboard
"""

from typing import List, Dict, Any
from .base import BaseChart, ChartRenderer
import re

class PieChart(BaseChart):
    """Pie chart renderer using ASCII characters with advanced configuration support"""

    def __init__(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        super().__init__(data, config)
        self.show_config = config.get('show', {})

    def _get_style_config(self) -> Dict[str, Any]:
        """Get style configuration from show config."""
        return self.show_config.get('style', {})

    def _get_colors_config(self) -> List[str]:
        """Get colors configuration from show config."""
        return self.show_config.get('colors', [])

    def _get_legend_config(self) -> Dict[str, Any]:
        """Get legend configuration from show config."""
        return self.show_config.get('legend', {})

    def _format_value_with_config(self, value: float) -> str:
        """Format value based on style configuration."""
        style_config = self._get_style_config()
        value_format = style_config.get('value_format', '{:.0f}')

        try:
            if isinstance(value, (int, float)):
                # Handle numeric formatting like "¥{:,.0f}" or "{:.1f}"
                if '{:' in value_format:
                    # Extract format specification
                    format_match = re.search(r'\{:([^}]+)\}', value_format)
                    if format_match:
                        format_spec = format_match.group(1)
                        formatted_number = format(value, format_spec)
                        # Replace the format placeholder with formatted number
                        return value_format.replace('{:' + format_spec + '}', formatted_number)
                    else:
                        return value_format.format(value)
                else:
                    # Simple format string like "¥{}"
                    return value_format.format(value)
            else:
                return value_format.format(value)
        except (ValueError, TypeError):
            # Fallback to string conversion if formatting fails
            return str(value)

    def _format_percentage_with_config(self, percentage: float) -> str:
        """Format percentage based on style configuration."""
        style_config = self._get_style_config()
        percentage_format = style_config.get('percentage_format', '{:.1f}%')

        try:
            return percentage_format.format(percentage)
        except (ValueError, TypeError):
            return f"{percentage:.1f}%"

    def render(self) -> str:
        """
        Render pie chart data as ASCII art with advanced configuration support

        Returns:
            Rendered chart as string
        """
        try:
            if not self.data:
                return self._handle_empty_data()

            # Extract configuration from show section
            value_column = self.show_config.get('value_column', 'value')
            label_column = self.show_config.get('label_column', 'label')

            # Get style configuration
            style_config = self._get_style_config()
            show_percentages = style_config.get('show_percentages', True)
            show_values = style_config.get('show_values', True)
            show_labels = style_config.get('show_labels', True)

            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()

            # Validate required columns
            for row in self.data:
                if value_column not in row or label_column not in row:
                    return f"Error: Required columns '{value_column}' or '{label_column}' not found"
                if row[value_column] is None or row[label_column] is None:
                    return f"Error: Required columns '{value_column}' or '{label_column}' contain null values"

            # Extract and convert data
            pie_data = []
            total = 0
            for row in self.data:
                try:
                    value = float(row.get(value_column, 0))
                    label = str(row.get(label_column, ''))
                    if value > 0:  # Only include positive values
                        pie_data.append({'label': label, 'value': value})
                        total += value
                except (ValueError, TypeError):
                    continue

            if not pie_data or total == 0:
                return "Error: No valid positive numeric data found"

            # Sort by value (largest first)
            pie_data.sort(key=lambda x: x['value'], reverse=True)

            # Get colors configuration
            colors = self._get_colors_config()

            # Build output
            chart_lines = []

            # Add title
            title = self.show_config.get('title', 'Pie Chart')
            chart_lines.append(f"  {title}")
            chart_lines.append("")

            # Pie chart symbols for different percentages
            pie_chars = ['█', '▉', '▊', '▋', '▌', '▍', '▎', '▏']

            # Calculate and display each slice
            for i, item in enumerate(pie_data):
                value = item['value']
                label = item['label']
                percentage = (value / total) * 100

                # Create visual bar representation
                bar_length = int(percentage * width / 100)  # Scale to available width

                # Create bar with blocks
                full_blocks = bar_length // 8
                partial_block = bar_length % 8

                bar = '█' * full_blocks
                if partial_block > 0 and full_blocks < width // 8:
                    bar += pie_chars[8 - partial_block]

                # Truncate label if too long
                display_label = label[:15] if len(label) > 15 else label

                # Build display components
                components = []
                if show_labels:
                    components.append(f"{display_label:<15}")

                components.append(f"│{bar:<20}│")

                if show_percentages:
                    components.append(self._format_percentage_with_config(percentage))

                if show_values:
                    formatted_value = self._format_value_with_config(value)
                    components.append(f"({formatted_value})")

                # Format line
                line = " ".join(components)
                chart_lines.append(line)

            # Add legend if configured
            legend_config = self._get_legend_config()
            if legend_config.get('show', True):
                chart_lines.append("")
                chart_lines.append("Legend:")
                for i, item in enumerate(pie_data):
                    color_info = ""
                    if colors and i < len(colors):
                        color_info = f" ({colors[i]})"
                    chart_lines.append(f"  █ {item['label']}{color_info}")

            # Add summary
            chart_lines.append("")
            chart_lines.append("─" * 50)
            chart_lines.append(f"Total: {self._format_value_with_config(total)}")
            chart_lines.append(f"Slices: {len(pie_data)}")

            # Add explode information if configured
            explode_config = self.show_config.get('explode', {})
            if explode_config.get('auto_explode_max', False):
                max_item = max(pie_data, key=lambda x: x['value'])
                explode_distance = explode_config.get('explode_distance', 0.1)
                chart_lines.append("")
                chart_lines.append(f"Highlighted: {max_item['label']} (largest slice)")

            return "\n".join(chart_lines)

        except Exception as e:
            return self._handle_error(e)

# Register the pie chart
ChartRenderer.register_chart_class('pie', PieChart)