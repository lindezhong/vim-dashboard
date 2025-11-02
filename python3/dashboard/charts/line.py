"""
Line chart implementation using Rich
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.text import Text
from rich.align import Align
from .base import BaseChart, ChartRenderer, ASCIIChartHelper
from ..utils import truncate_string


class LineChart(BaseChart):
    """Line chart implementation using ASCII characters."""
    
    def __init__(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        super().__init__(data, config)
        self.show_config = config.get('show', {})
        self.x_column = self.show_config.get('x_column', 'x')

        # Support both single y_column and multiple y_columns
        self.y_columns_config = self.show_config.get('y_columns', [])
        self.y_column_single = self.show_config.get('y_column', 'y')

        # Determine which columns to use
        if self.y_columns_config:
            # Multiple columns configuration
            self.y_columns = []
            for col_config in self.y_columns_config:
                if isinstance(col_config, dict):
                    self.y_columns.append({
                        'column': col_config.get('column', 'y'),
                        'label': col_config.get('label', col_config.get('column', 'y')),
                        'color': col_config.get('color', '#3498db'),
                        'line_style': col_config.get('line_style', 'solid'),
                        'marker': col_config.get('marker', 'circle')
                    })
                else:
                    # Simple string format
                    self.y_columns.append({
                        'column': str(col_config),
                        'label': str(col_config),
                        'color': '#3498db',
                        'line_style': 'solid',
                        'marker': 'circle'
                    })
        else:
            # Single column configuration (backward compatibility)
            self.y_columns = [{
                'column': self.y_column_single,
                'label': self.y_column_single,
                'color': '#3498db',
                'line_style': 'solid',
                'marker': 'circle'
            }]
        
    def _extract_chart_data(self) -> Tuple[List[str], Dict[str, List[float]]]:
        """Extract x and y data from the dataset for multiple series."""
        labels = []
        series_data = {}

        # Initialize series data
        for y_col in self.y_columns:
            series_data[y_col['column']] = []

        # Get unique x values (preserve order from data)
        seen_x = set()
        for row in self.data:
            x_val = str(row.get(self.x_column, ''))
            if x_val not in seen_x:
                labels.append(x_val)
                seen_x.add(x_val)

        # Extract values for each series
        for row in self.data:
            x_val = str(row.get(self.x_column, ''))
            if x_val in labels:  # Only process known x values
                for y_col in self.y_columns:
                    y_val = row.get(y_col['column'], 0)

                    # Convert value to float
                    try:
                        value = float(y_val) if y_val is not None else 0.0
                    except (ValueError, TypeError):
                        value = 0.0

                    # Find the index for this x value and set the corresponding y value
                    x_index = labels.index(x_val)
                    while len(series_data[y_col['column']]) <= x_index:
                        series_data[y_col['column']].append(0.0)
                    series_data[y_col['column']][x_index] = value

        # Ensure all series have the same length as labels
        for y_col in self.y_columns:
            while len(series_data[y_col['column']]) < len(labels):
                series_data[y_col['column']].append(0.0)

        return labels, series_data
    
    def _get_chart_dimensions(self) -> Tuple[int, int]:
        """Get chart dimensions."""
        width = self._get_width()
        height = self._get_height()
        
        # Reserve space for labels and axes
        chart_width = max(20, width - 15) if width else 60
        chart_height = max(5, height - 4)
        
        return chart_width, chart_height
    
    def _normalize_values_to_chart_height(self, values: List[float], chart_height: int) -> List[int]:
        """Normalize values to fit chart height."""
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            # All values are the same, put them in the middle
            middle = chart_height // 2
            return [middle] * len(values)
        
        # Normalize to chart height (0 = bottom, chart_height-1 = top)
        normalized = []
        for value in values:
            # Scale value to 0-1 range
            normalized_val = (value - min_val) / (max_val - min_val)
            # Scale to chart height
            chart_pos = int(normalized_val * (chart_height - 1))
            normalized.append(chart_pos)
        
        return normalized
    
    def _create_line_chart_grid(self, chart_width: int, chart_height: int) -> List[List[str]]:
        """Create empty chart grid."""
        grid = []
        for _ in range(chart_height):
            row = [' '] * chart_width
            grid.append(row)
        return grid
    
    def _plot_points_and_lines(self, grid: List[List[str]], labels: List[str], 
                              normalized_values: List[int], chart_width: int, chart_height: int):
        """Plot points and connecting lines on the grid (legacy method for backward compatibility)."""
        point_char = self.style.get('point_char', ASCIIChartHelper.CHART_CHARS['line']['point'])
        self._plot_series_points_and_lines(grid, labels, normalized_values, chart_width, chart_height, point_char)

    def _plot_series_points_and_lines(self, grid: List[List[str]], labels: List[str],
                                     normalized_values: List[int], chart_width: int, chart_height: int, point_char: str):
        """Plot points and connecting lines for a single series on the grid."""
        if not normalized_values:
            return

        # Calculate x positions for data points
        if len(normalized_values) == 1:
            x_positions = [chart_width // 2]
        else:
            x_positions = []
            for i in range(len(normalized_values)):
                x_pos = int((i / (len(normalized_values) - 1)) * (chart_width - 1))
                x_positions.append(x_pos)

        # Plot points
        for i, (x_pos, y_pos) in enumerate(zip(x_positions, normalized_values)):
            if 0 <= x_pos < chart_width and 0 <= y_pos < chart_height:
                # Y coordinate is inverted (0 = top of grid, but we want 0 = bottom of chart)
                grid_y = chart_height - 1 - y_pos
                # Only plot if position is empty or use the new character
                if grid[grid_y][x_pos] == ' ' or grid[grid_y][x_pos] == ASCIIChartHelper.CHART_CHARS['line']['line_h']:
                    grid[grid_y][x_pos] = point_char
        
        # Draw connecting lines
        line_char = self.style.get('line_char', ASCIIChartHelper.CHART_CHARS['line']['line_h'])
        
        for i in range(len(x_positions) - 1):
            x1, y1 = x_positions[i], normalized_values[i]
            x2, y2 = x_positions[i + 1], normalized_values[i + 1]
            
            self._draw_line_between_points(grid, x1, y1, x2, y2, chart_width, chart_height, line_char)
    
    def _draw_line_between_points(self, grid: List[List[str]], x1: int, y1: int, x2: int, y2: int,
                                 chart_width: int, chart_height: int, line_char: str):
        """Draw line between two points using Bresenham-like algorithm."""
        # Convert to grid coordinates (invert Y)
        grid_y1 = chart_height - 1 - y1
        grid_y2 = chart_height - 1 - y2
        
        # Simple line drawing
        steps = max(abs(x2 - x1), abs(grid_y2 - grid_y1))
        if steps == 0:
            return
        
        x_step = (x2 - x1) / steps
        y_step = (grid_y2 - grid_y1) / steps
        
        for step in range(steps + 1):
            x = int(x1 + step * x_step)
            y = int(grid_y1 + step * y_step)
            
            if 0 <= x < chart_width and 0 <= y < chart_height:
                # Don't overwrite points
                if grid[y][x] == ' ':
                    if abs(y_step) > abs(x_step):
                        # More vertical than horizontal
                        grid[y][x] = ASCIIChartHelper.CHART_CHARS['line']['line_v']
                    else:
                        # More horizontal than vertical
                        grid[y][x] = line_char
    
    def _add_axes_to_grid(self, grid: List[List[str]], chart_width: int, chart_height: int):
        """Add axes to the chart grid."""
        # Add bottom axis (x-axis)
        axis_char = ASCIIChartHelper.CHART_CHARS['line']['line_h']
        for x in range(chart_width):
            if grid[chart_height - 1][x] == ' ':
                grid[chart_height - 1][x] = axis_char
        
        # Add left axis (y-axis) - optional
        if self.style.get('show_y_axis', False):
            axis_char = ASCIIChartHelper.CHART_CHARS['line']['line_v']
            for y in range(chart_height):
                if grid[y][0] == ' ':
                    grid[y][0] = axis_char
    
    def _create_x_axis_labels(self, labels: List[str], chart_width: int) -> str:
        """Create x-axis labels line."""
        if not labels:
            return ""
        
        # Calculate positions for labels
        if len(labels) == 1:
            positions = [chart_width // 2]
        else:
            positions = []
            for i in range(len(labels)):
                pos = int((i / (len(labels) - 1)) * (chart_width - 1))
                positions.append(pos)
        
        # Create label line
        label_chars = [' '] * chart_width
        
        for i, (pos, label) in enumerate(zip(positions, labels)):
            # Truncate label to fit
            max_label_len = min(len(label), chart_width - pos)
            if max_label_len > 0:
                truncated_label = label[:max_label_len]
                for j, char in enumerate(truncated_label):
                    if pos + j < chart_width:
                        label_chars[pos + j] = char
        
        return ''.join(label_chars)
    
    def _create_y_axis_info(self, values: List[float]) -> List[str]:
        """Create y-axis value information."""
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        
        info_lines = []
        if self.style.get('show_y_range', True):
            info_lines.append(f"Range: {self._format_value(min_val)} - {self._format_value(max_val)}")
        
        return info_lines
    
    def _format_value(self, value: float) -> str:
        """Format value for display."""
        format_str = self.style.get('value_format', '{:.1f}')
        try:
            return format_str.format(value)
        except:
            return str(value)
    
    def render(self) -> str:
        """Render line chart with multiple series support."""
        labels, series_data = self._extract_chart_data()

        if not labels or not series_data:
            return self._handle_empty_data()

        chart_width, chart_height = self._get_chart_dimensions()

        # Create chart grid
        grid = self._create_line_chart_grid(chart_width, chart_height)

        # Get all values for range calculation
        all_values = []
        for series_values in series_data.values():
            all_values.extend(series_values)

        if not all_values:
            return self._handle_empty_data()

        # Characters for different series
        line_chars = ['●', '◆', '▲', '■', '♦', '○', '◇', '△', '□', '◊']

        # Plot each series
        for series_idx, y_col in enumerate(self.y_columns):
            column_name = y_col['column']
            if column_name not in series_data:
                continue

            values = series_data[column_name]
            if not values:
                continue

            # Normalize values to chart height
            normalized_values = self._normalize_values_to_chart_height(values, chart_height)

            # Use different character for each series
            char = line_chars[series_idx % len(line_chars)]

            # Plot this series
            self._plot_series_points_and_lines(grid, labels, normalized_values,
                                             chart_width, chart_height, char)

        # Add axes
        self._add_axes_to_grid(grid, chart_width, chart_height)

        # Build output
        chart_lines = []

        # Add title
        title = self.show_config.get('title', 'Line Chart')
        chart_lines.append(f"  {title}")
        chart_lines.append("")

        # Add legend for multiple series
        if len(self.y_columns) > 1:
            legend_line = "  Legend: "
            for i, y_col in enumerate(self.y_columns):
                char = line_chars[i % len(line_chars)]
                legend_line += f"{char} {y_col['label']}  "
            chart_lines.append(legend_line)
            chart_lines.append("")

        # Convert grid to strings
        for row in grid:
            chart_lines.append(''.join(row))

        # Add x-axis labels
        x_labels = self._create_x_axis_labels(labels, chart_width)
        if x_labels.strip():
            chart_lines.append(x_labels)

        # Add y-axis info
        y_info = self._create_y_axis_info(all_values)
        if y_info:
            chart_lines.append("")
            chart_lines.extend(y_info)

        # Add statistics if enabled
        if self.style.get('show_stats', False):
            stats = self._generate_stats(all_values)
            chart_lines.append("")
            chart_lines.append(stats)

        return '\n'.join(chart_lines)
    
    def _generate_stats(self, values: List[float]) -> str:
        """Generate statistics for the chart."""
        if not values:
            return ""
        
        total = sum(values)
        avg = total / len(values)
        max_val = max(values)
        min_val = min(values)
        
        stats_lines = [
            f"Points: {len(values)}",
            f"Average: {self._format_value(avg)}",
            f"Max: {self._format_value(max_val)}",
            f"Min: {self._format_value(min_val)}"
        ]
        
        return ' | '.join(stats_lines)


# Register the line chart
ChartRenderer.register_chart_class('line', LineChart)