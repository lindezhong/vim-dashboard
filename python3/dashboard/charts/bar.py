"""
Bar chart implementation using Rich
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.text import Text
from rich.align import Align
from .base import BaseChart, ChartRenderer, ASCIIChartHelper
from ..utils import truncate_string
import re

class BarChart(BaseChart):
    """Bar chart implementation using ASCII characters."""

    def __init__(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        super().__init__(data, config)
        self.show_config = config.get('show', {})
        self.x_column = self.show_config.get('x_column', 'x')
        self.y_column = self.show_config.get('y_column', 'y')

    def _get_style_config(self) -> Dict[str, Any]:
        """Get style configuration from show config."""
        return self.show_config.get('style', {})

    def _get_axes_config(self) -> Dict[str, Any]:
        """Get axes configuration from show config."""
        return self.show_config.get('axes', {})

    def _get_colors_config(self) -> Dict[str, Any]:
        """Get colors configuration from show config."""
        return self.show_config.get('colors', {})

    def _get_data_labels_config(self) -> Dict[str, Any]:
        """Get data labels configuration from show config."""
        return self.show_config.get('data_labels', {})

    def _get_threshold_lines_config(self) -> List[Dict[str, Any]]:
        """Get threshold lines configuration from show config."""
        return self.show_config.get('threshold_lines', [])

    def _sort_data_if_configured(self) -> tuple[List[str], List[float]]:
        """Sort data based on sort configuration and extract chart data."""
        labels = []
        values = []

        # Extract data first
        for row in self.data:
            x_val = row.get(self.x_column, '')
            y_val = row.get(self.y_column, 0)

            # Convert label to string
            label = str(x_val)

            # Convert value to float
            try:
                value = float(y_val) if y_val is not None else 0.0
            except (ValueError, TypeError):
                value = 0.0

            labels.append(label)
            values.append(value)

        # Apply sorting if configured
        sort_config = self.show_config.get('sort', {})
        # If sort config exists and has a 'by' field, enable sorting
        # Support both explicit enabled field and implicit (if 'by' is specified)
        sort_enabled = sort_config.get('enabled', True) if sort_config.get('by') else False
        if sort_enabled:
            sort_by = sort_config.get('by', 'value')
            sort_order = sort_config.get('order', 'desc')

            # Create pairs for sorting
            pairs = list(zip(labels, values))

            if sort_by == 'value':
                pairs.sort(key=lambda x: x[1], reverse=(sort_order == 'desc'))
            else:  # sort by label
                pairs.sort(key=lambda x: x[0], reverse=(sort_order == 'desc'))

            # Unzip sorted pairs
            labels, values = zip(*pairs) if pairs else ([], [])
            labels, values = list(labels), list(values)

        return labels, values

    def _extract_chart_data(self) -> tuple[List[str], List[float]]:
        """Extract x and y data from the dataset."""
        labels, values = self._sort_data_if_configured()

        # Apply label truncation
        max_label_length = self.style.get('max_label_length', 15)
        if max_label_length:
            labels = [truncate_string(label, max_label_length) for label in labels]

        return labels, values

    def _get_chart_dimensions(self) -> tuple[int, int]:
        """Get chart dimensions."""
        width = self._get_width()
        height = self._get_height()

        # Reserve space for labels and axes
        chart_width = max(20, width - 20) if width else 60
        chart_height = max(5, height - 5)

        return chart_width, chart_height

    def _format_value_with_config(self, value: float) -> str:
        """Format value based on style configuration."""
        style_config = self._get_style_config()
        value_format = style_config.get('value_format', '{:.1f}')

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

    def _get_bar_character(self, style_config: Dict[str, Any]) -> str:
        """Get bar character based on style configuration."""
        # For now, use default bar character
        # In a more advanced implementation, this could support different bar styles
        return ASCIIChartHelper.CHART_CHARS['bar']['full']

    def _create_horizontal_bar_chart(self, labels: List[str], values: List[float]) -> List[str]:
        """Create horizontal bar chart with advanced styling."""
        if not values:
            return ["No data to display"]

        chart_width, chart_height = self._get_chart_dimensions()
        max_value = max(values) if values else 1
        max_label_width = max(len(label) for label in labels) if labels else 0
        max_label_width = min(max_label_width, 15)  # Limit label width

        # Get style configuration
        style_config = self._get_style_config()
        show_values = style_config.get('show_values', True)
        bar_width_ratio = style_config.get('bar_width', 0.8)

        # Calculate bar width (reserve space for labels and padding)
        available_width = max(10, chart_width - max_label_width - 10)
        bar_width = max(5, int(available_width * bar_width_ratio))

        lines = []

        # Limit number of bars to fit in height
        max_bars = min(len(labels), chart_height)

        for i in range(max_bars):
            label = labels[i]
            value = values[i]

            # Create bar
            bar_chars = ASCIIChartHelper.get_bar_char(value, max_value, bar_width)

            # Format value display
            value_str = self._format_value_with_config(value) if show_values else ""

            # Create line with label, bar, and value
            label_part = f"{label:<{max_label_width}}"
            if show_values:
                line = f"{label_part} │{bar_chars}│ {value_str}"
            else:
                line = f"{label_part} │{bar_chars}│"
            lines.append(line)

        # Add threshold lines if configured
        threshold_lines = self._get_threshold_lines_config()
        if threshold_lines:
            lines.extend(self._add_threshold_indicators(threshold_lines, max_value, bar_width, max_label_width))

        # Add truncation indicator if needed
        if len(labels) > max_bars:
            lines.append(f"{'...':<{max_label_width}} │{'':>{bar_width}}│ ({len(labels) - max_bars} more)")

        return lines

    def _add_threshold_indicators(self, threshold_lines: List[Dict[str, Any]], max_value: float, bar_width: int, label_width: int) -> List[str]:
        """Add threshold line indicators to the chart."""
        indicators = []

        for threshold in threshold_lines:
            threshold_value = threshold.get('value', 0)
            threshold_label = threshold.get('label', f'Threshold: {threshold_value}')
            threshold_color = threshold.get('color', 'red')
            threshold_style = threshold.get('style', 'dashed')

            # Calculate position
            if max_value > 0:
                position = int((threshold_value / max_value) * bar_width)
                position = max(0, min(position, bar_width - 1))

                # Create threshold line
                line_char = '┊' if threshold_style == 'dashed' else '│'
                threshold_bar = ' ' * position + line_char + ' ' * (bar_width - position - 1)

                # Add threshold indicator
                label_part = f"{'':>{label_width}}"
                indicators.append(f"{label_part} │{threshold_bar}│ {threshold_label}")

        return indicators

    def _create_vertical_bar_chart(self, labels: List[str], values: List[float]) -> List[str]:
        """Create vertical bar chart with advanced styling."""
        if not values:
            return ["No data to display"]

        chart_width, chart_height = self._get_chart_dimensions()
        max_value = max(values) if values else 1

        # Get style configuration
        style_config = self._get_style_config()
        show_values = style_config.get('show_values', True)

        # Limit number of bars to fit in width
        max_bars = min(len(labels), chart_width // 3)  # Each bar needs at least 3 chars

        if max_bars == 0:
            return ["Chart too narrow"]

        # Calculate bar positions
        bar_width = max(1, chart_width // max_bars)

        lines = []

        # Create chart from top to bottom
        for row in range(chart_height - 2, -1, -1):  # Reserve bottom row for labels
            line_chars = []

            for i in range(max_bars):
                value = values[i]
                # Calculate bar height for this value
                bar_height = int((value / max_value) * (chart_height - 2))

                if row < bar_height:
                    # This row should have bar content
                    bar_char = self._get_bar_character(style_config)
                else:
                    bar_char = ' '

                # Add bar character(s) with spacing
                line_chars.extend([bar_char] * (bar_width - 1))
                line_chars.append(' ')  # Spacing between bars

            lines.append(''.join(line_chars[:chart_width]))

        # Add x-axis line
        axes_config = self._get_axes_config()
        x_axis_config = axes_config.get('x_axis', {})
        if x_axis_config.get('show_grid', True):
            axis_line = '─' * chart_width
            lines.append(axis_line)

        # Add labels with rotation support
        label_rotation = x_axis_config.get('rotation', 0)
        if label_rotation == 0:
            # Horizontal labels
            label_line_chars = []
            for i in range(max_bars):
                label = labels[i]
                # Truncate label to fit bar width
                truncated_label = truncate_string(label, bar_width - 1)
                label_line_chars.extend(list(f"{truncated_label:<{bar_width - 1}}"))
                label_line_chars.append(' ')

            lines.append(''.join(label_line_chars[:chart_width]))
        else:
            # For rotated labels, just show first character for now
            # In a real implementation, this would need more sophisticated handling
            label_line_chars = []
            for i in range(max_bars):
                label = labels[i]
                first_char = label[0] if label else ' '
                label_line_chars.extend([first_char] + [' '] * (bar_width - 2))
                label_line_chars.append(' ')

            lines.append(''.join(label_line_chars[:chart_width]))

        # Add values if configured
        if show_values:
            value_line_chars = []
            for i in range(max_bars):
                value = values[i]
                value_str = self._format_value_with_config(value)
                # Truncate value to fit bar width
                truncated_value = truncate_string(value_str, bar_width - 1)
                value_line_chars.extend(list(f"{truncated_value:<{bar_width - 1}}"))
                value_line_chars.append(' ')

            lines.append(''.join(value_line_chars[:chart_width]))

        # Add truncation indicator if needed
        if len(labels) > max_bars:
            lines.append(f"... ({len(labels) - max_bars} more bars)")

        return lines

    def _format_value(self, value: float) -> str:
        """Format value for display (legacy method)."""
        return self._format_value_with_config(value)

    def _add_axes_titles(self, chart_lines: List[str]) -> List[str]:
        """Add axes titles if configured."""
        axes_config = self._get_axes_config()
        x_axis_config = axes_config.get('x_axis', {})
        y_axis_config = axes_config.get('y_axis', {})

        result_lines = chart_lines.copy()

        # Add Y-axis title (for horizontal charts)
        y_title = y_axis_config.get('title')
        if y_title:
            result_lines.insert(0, f"Y-axis: {y_title}")

        # Add X-axis title
        x_title = x_axis_config.get('title')
        if x_title:
            result_lines.append(f"X-axis: {x_title}")

        return result_lines

    def render(self) -> str:
        """Render bar chart with advanced configuration support."""
        labels, values = self._extract_chart_data()

        if not labels or not values:
            return self._handle_empty_data()

        # Choose chart orientation
        orientation = self.show_config.get('orientation', 'horizontal')

        if orientation == 'vertical':
            chart_lines = self._create_vertical_bar_chart(labels, values)
        else:
            chart_lines = self._create_horizontal_bar_chart(labels, values)

        # Add axes titles if configured
        chart_lines = self._add_axes_titles(chart_lines)

        # Join lines
        chart_content = '\n'.join(chart_lines)

        # Add statistics if enabled
        if self.style.get('show_stats', False):
            stats = self._generate_stats(values)
            chart_content += '\n\n' + stats

        return chart_content

    def _generate_stats(self, values: List[float]) -> str:
        """Generate statistics for the chart."""
        if not values:
            return ""

        total = sum(values)
        avg = total / len(values)
        max_val = max(values)
        min_val = min(values)

        stats_lines = [
            f"Total: {self._format_value_with_config(total)}",
            f"Average: {self._format_value_with_config(avg)}",
            f"Max: {self._format_value_with_config(max_val)}",
            f"Min: {self._format_value_with_config(min_val)}"
        ]

        return ' | '.join(stats_lines)

# Register the bar chart
ChartRenderer.register_chart_class('bar', BarChart)