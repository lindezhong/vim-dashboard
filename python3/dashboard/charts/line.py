"""
Line chart implementation with proper line visualization and Y-axis labels
"""

from typing import Dict, Any, List, Optional, Tuple
from .base import BaseChart, ChartRenderer
from ..utils import truncate_string
import re

class LineChart(BaseChart):
    """Line chart implementation using ASCII characters with proper line connections."""

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

        # Axes configuration
        self.axes_config = self.show_config.get('axes', {})
        self.x_axis_config = self.axes_config.get('x_axis', {})
        self.y_axis_config = self.axes_config.get('y_axis', {})

        # Line style configuration
        self.line_style_config = self.show_config.get('line_style', {})

        # Legend configuration
        self.legend_config = self.show_config.get('legend', {})

    def _get_line_character(self, line_style: str, direction: str) -> str:
        """Get appropriate line character based on style and direction."""
        if line_style == 'dashed':
            if direction == 'horizontal':
                return '┄'
            elif direction == 'vertical':
                return '┆'
            elif direction == 'diagonal_down':
                return '\\'  # For dashed, use same as solid
            else:  # diagonal_up
                return '/'
        elif line_style == 'dotted':
            if direction == 'horizontal':
                return '┈'
            elif direction == 'vertical':
                return '┊'
            elif direction == 'diagonal_down':
                return '\\'
            else:  # diagonal_up
                return '/'
        else:  # solid
            if direction == 'horizontal':
                return '─'
            elif direction == 'vertical':
                return '│'
            elif direction == 'diagonal_down':
                return '\\'
            else:  # diagonal_up
                return '/'

    def _get_marker_character(self, marker_type: str) -> str:
        """Get marker character based on type."""
        marker_map = {
            'circle': '●',
            'square': '■',
            'triangle': '▲',
            'diamond': '◆',
            'cross': '✕',
            'plus': '✚'
        }
        return marker_map.get(marker_type, '●')

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

    def _create_ascii_line_chart(self, labels: List[str], series_data: Dict[str, List[float]],
                                chart_width: int, chart_height: int, min_val: float, max_val: float) -> List[str]:
        """Create ASCII line chart with proper line visualization and advanced styling."""

        # Initialize empty grid
        grid = []
        for _ in range(chart_height):
            grid.append([' '] * chart_width)

        # Get line style configuration
        show_points = self.line_style_config.get('show_points', True)

        # Plot each series
        for series_idx, y_col in enumerate(self.y_columns):
            column_name = y_col['column']
            if column_name not in series_data:
                continue

            values = series_data[column_name]
            if not values:
                continue

            # Get styling for this series
            line_style = y_col.get('line_style', 'solid')
            marker_type = y_col.get('marker', 'circle')
            marker_char = self._get_marker_character(marker_type)

            # Convert values to grid coordinates
            points = []
            for i, value in enumerate(values):
                # X coordinate
                if len(values) == 1:
                    x = chart_width // 2
                else:
                    x = int((i / (len(values) - 1)) * (chart_width - 1))

                # Y coordinate (normalized and inverted)
                if max_val == min_val:
                    y = chart_height // 2
                else:
                    normalized = (value - min_val) / (max_val - min_val)
                    y = int((1 - normalized) * (chart_height - 1))  # Invert Y

                points.append((x, y))

            # Draw lines between consecutive points using Bresenham algorithm
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self._draw_line_on_grid(grid, x1, y1, x2, y2, chart_width, chart_height, line_style)

            # Draw points on top of lines if enabled
            if show_points:
                for x, y in points:
                    if 0 <= x < chart_width and 0 <= y < chart_height:
                        grid[y][x] = marker_char

        # Convert grid to strings
        result = []
        for row in grid:
            result.append(''.join(row))

        return result

    def _draw_line_on_grid(self, grid: List[List[str]], x1: int, y1: int, x2: int, y2: int,
                          chart_width: int, chart_height: int, line_style: str = 'solid'):
        """Draw a line between two points using Bresenham's algorithm with style support."""

        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        x_step = 1 if x1 < x2 else -1
        y_step = 1 if y1 < y2 else -1

        error = dx - dy
        x, y = x1, y1

        while True:
            # Draw line character if position is empty
            if 0 <= x < chart_width and 0 <= y < chart_height:
                if grid[y][x] == ' ':
                    # Choose line character based on direction and style
                    if dx > dy * 2:  # More horizontal
                        grid[y][x] = self._get_line_character(line_style, 'horizontal')
                    elif dy > dx * 2:  # More vertical
                        grid[y][x] = self._get_line_character(line_style, 'vertical')
                    elif (x_step > 0 and y_step > 0) or (x_step < 0 and y_step < 0):
                        grid[y][x] = self._get_line_character(line_style, 'diagonal_down')
                    else:
                        grid[y][x] = self._get_line_character(line_style, 'diagonal_up')

            # Check if we've reached the end point
            if x == x2 and y == y2:
                break

            # Calculate next position
            error2 = 2 * error

            if error2 > -dy:
                error -= dy
                x += x_step

            if error2 < dx:
                error += dx
                y += y_step

    def _create_y_axis_labels(self, min_val: float, max_val: float, chart_height: int, y_axis_width: int) -> List[str]:
        """Create Y-axis labels for each row with format support."""
        labels = []

        # Create labels for each row of the chart
        for i in range(chart_height):
            # Calculate the value for this row (inverted because grid[0] is top)
            row_from_bottom = chart_height - 1 - i
            if chart_height == 1:
                value = (min_val + max_val) / 2
            else:
                value = min_val + (row_from_bottom / (chart_height - 1)) * (max_val - min_val)

            # Format the value
            formatted_value = self._format_value(value)

            # Right-align the label within the Y-axis width
            label = formatted_value.rjust(y_axis_width - 1) + ' '
            labels.append(label)

        return labels

    def _create_x_axis_labels(self, labels: List[str], chart_width: int, y_axis_width: int) -> str:
        """Create x-axis labels line with rotation support."""
        if not labels:
            return ""

        # Get label rotation configuration
        label_rotation = self.x_axis_config.get('label_rotation', 0)

        # Create label line with Y-axis offset
        label_chars = [' '] * (y_axis_width + 1 + chart_width)

        # Add Y-axis spacing
        for i in range(y_axis_width + 1):
            label_chars[i] = ' '

        # Calculate positions for labels and add them
        if len(labels) > 1:
            # Show up to 5 labels to avoid crowding
            step = max(1, len(labels) // 5)
            for i in range(0, len(labels), step):
                if i < len(labels):
                    label = labels[i]

                    # Handle label rotation
                    if label_rotation == 45:
                        # For 45-degree rotation, just show first few characters
                        label = label[:3] + '...' if len(label) > 3 else label
                    elif label_rotation == 90:
                        # For 90-degree rotation, show only first character
                        label = label[0] if label else ' '

                    # Calculate position
                    pos = int((i / (len(labels) - 1)) * (chart_width - 1))
                    adjusted_pos = y_axis_width + 1 + pos

                    # Truncate label to fit
                    max_label_len = min(len(label), len(label_chars) - adjusted_pos)
                    if max_label_len > 0:
                        truncated_label = label[:max_label_len]
                        for j, char in enumerate(truncated_label):
                            if adjusted_pos + j < len(label_chars):
                                label_chars[adjusted_pos + j] = char

        return ''.join(label_chars)

    def _format_value(self, value: float) -> str:
        """Format value for display with advanced formatting support."""
        # Use Y-axis format if specified
        y_format = self.y_axis_config.get('format', '{:.0f}')

        try:
            if isinstance(value, (int, float)):
                # Handle numeric formatting like "{:,.0f}" or "{:.1f}"
                if '{:' in y_format:
                    # Extract format specification
                    format_match = re.search(r'\{:([^}]+)\}', y_format)
                    if format_match:
                        format_spec = format_match.group(1)
                        formatted_number = format(value, format_spec)
                        # Replace the format placeholder with formatted number
                        return y_format.replace('{:' + format_spec + '}', formatted_number)
                    else:
                        return y_format.format(value)
                else:
                    # Simple format string
                    return y_format.format(value)
            else:
                return y_format.format(value)
        except (ValueError, TypeError):
            # Fallback to simple formatting
            if abs(value) >= 1000:
                return f"{value/1000:.1f}k"
            elif abs(value) >= 1:
                return f"{value:.0f}"
            else:
                return f"{value:.2f}"

    def _draw_grid_lines(self, chart_lines: List[str], chart_width: int, chart_height: int, y_axis_width: int) -> None:
        """Draw grid lines if configured."""
        # Check if grid is enabled
        x_grid = self.x_axis_config.get('show_grid', False)
        y_grid = self.y_axis_config.get('show_grid', False)

        if not (x_grid or y_grid):
            return

        # Get grid style
        grid_style = self.x_axis_config.get('grid_style', 'dotted')
        if grid_style == 'dashed':
            h_grid_char = '┄'
            v_grid_char = '┆'
        elif grid_style == 'dotted':
            h_grid_char = '┈'
            v_grid_char = '┊'
        else:  # solid
            h_grid_char = '─'
            v_grid_char = '│'

        # Find chart area in the output
        chart_start_line = None
        for i, line in enumerate(chart_lines):
            if '│' in line and len(line) > y_axis_width:
                chart_start_line = i
                break

        if chart_start_line is None:
            return

        # Draw horizontal grid lines (Y-grid)
        if y_grid:
            for i in range(chart_start_line, chart_start_line + chart_height):
                if i < len(chart_lines):
                    line = chart_lines[i]
                    if '│' in line:
                        # Find chart area
                        axis_pos = line.find('│')
                        if axis_pos != -1 and len(line) > axis_pos + 1:
                            # Replace spaces in chart area with grid characters
                            chart_area = line[axis_pos + 1:axis_pos + 1 + chart_width]
                            new_chart_area = ''
                            for char in chart_area:
                                if char == ' ':
                                    new_chart_area += h_grid_char
                                else:
                                    new_chart_area += char
                            chart_lines[i] = line[:axis_pos + 1] + new_chart_area + line[axis_pos + 1 + chart_width:]

        # Draw vertical grid lines (X-grid) - simplified implementation
        if x_grid:
            # Add vertical lines at regular intervals
            for col in range(0, chart_width, chart_width // 5):
                if col > 0:  # Skip first column
                    for i in range(chart_start_line, chart_start_line + chart_height):
                        if i < len(chart_lines):
                            line = chart_lines[i]
                            axis_pos = line.find('│')
                            if axis_pos != -1 and axis_pos + 1 + col < len(line):
                                char_pos = axis_pos + 1 + col
                                if char_pos < len(line) and line[char_pos] == ' ':
                                    chart_lines[i] = line[:char_pos] + v_grid_char + line[char_pos + 1:]

    def _draw_threshold_lines(self, chart_lines: List[str], chart_width: int, chart_height: int,
                             display_min: float, display_max: float, y_axis_width: int) -> None:
        """Draw threshold lines on the chart."""
        threshold_config = self.show_config.get('threshold_lines', [])
        if not threshold_config:
            return

        for threshold in threshold_config:
            if not isinstance(threshold, dict):
                continue

            value = threshold.get('value')
            if value is None:
                continue

            try:
                threshold_value = float(value)
            except (ValueError, TypeError):
                continue

            # Check if threshold is within display range
            if threshold_value < display_min or threshold_value > display_max:
                continue

            # Calculate Y position for threshold line
            if display_max == display_min:
                y_pos = chart_height // 2
            else:
                normalized = (threshold_value - display_min) / (display_max - display_min)
                y_pos = int((1 - normalized) * (chart_height - 1))  # Invert Y

            # Ensure y_pos is within bounds
            if y_pos < 0 or y_pos >= len(chart_lines) - 2:  # -2 for x-axis and labels
                continue

            # Get line style
            line_style = threshold.get('style', 'solid')
            if line_style == 'dashed':
                line_char = '┄'
            elif line_style == 'dotted':
                line_char = '┈'
            else:  # solid
                line_char = '─'

            # Get color (for display purposes, we'll use different characters)
            color = threshold.get('color', 'red')
            if color == 'red':
                line_char = '━'  # Bold line for red
            elif color == 'yellow':
                line_char = '═'  # Double line for yellow

            # Find the chart line to modify (accounting for title and legend)
            chart_line_index = None
            for i, line in enumerate(chart_lines):
                if '│' in line:  # This is a chart line
                    chart_data_start = i
                    chart_line_index = chart_data_start + y_pos
                    break

            if chart_line_index is None or chart_line_index >= len(chart_lines):
                continue

            # Modify the line to add threshold
            line = chart_lines[chart_line_index]
            if '│' in line:
                # Find the chart area (after the Y-axis)
                axis_pos = line.find('│')
                if axis_pos != -1:
                    # Replace the chart area with threshold line
                    new_line = line[:axis_pos + 1] + line_char * chart_width
                    chart_lines[chart_line_index] = new_line

                    # Add threshold label if specified
                    label = threshold.get('label', '')
                    if label:
                        # Add label at the end of the line
                        chart_lines[chart_line_index] += f' ← {label}'

    def _create_legend(self) -> List[str]:
        """Create legend lines based on configuration."""
        legend_lines = []

        # Check if legend should be shown
        if not self.legend_config.get('show', True) or len(self.y_columns) <= 1:
            return legend_lines

        # Get legend position
        position = self.legend_config.get('position', 'top_right')

        # Create legend content
        legend_content = "Legend: "
        for i, y_col in enumerate(self.y_columns):
            marker_char = self._get_marker_character(y_col.get('marker', 'circle'))
            legend_content += f"{marker_char} {y_col['label']}  "

        legend_lines.append(f"  {legend_content}")

        return legend_lines

    def render(self) -> str:
        """Render line chart with advanced configuration support."""
        labels, series_data = self._extract_chart_data()

        if not labels or not series_data:
            return self._handle_empty_data()

        # Get all values for range calculation
        all_values = []
        for series_values in series_data.values():
            all_values.extend(series_values)

        if not all_values:
            return self._handle_empty_data()

        # Calculate dimensions
        chart_width = 60  # Fixed width for consistency
        chart_height = 15  # Fixed height for consistency
        y_axis_width = 8   # Width for Y-axis labels

        # Calculate value range with padding
        min_val = min(all_values)
        max_val = max(all_values)

        # Apply min/max values from Y-axis config if specified
        config_min = self.y_axis_config.get('min_value')
        config_max = self.y_axis_config.get('max_value')

        if config_min is not None:
            min_val = min(min_val, float(config_min))
        if config_max is not None:
            max_val = max(max_val, float(config_max))

        value_range = max_val - min_val
        if value_range == 0:
            value_range = 1
        padding = value_range * 0.1
        display_min = min_val - padding
        display_max = max_val + padding

        # Build output
        chart_lines = []

        # Add title
        title = self.show_config.get('title', 'Line Chart')
        chart_lines.append(f"  {title}")
        chart_lines.append("")

        # Add legend
        legend_lines = self._create_legend()
        chart_lines.extend(legend_lines)
        if legend_lines:
            chart_lines.append("")

        # Create the chart
        chart_grid = self._create_ascii_line_chart(labels, series_data, chart_width, chart_height, display_min, display_max)

        # Create Y-axis labels
        y_labels = self._create_y_axis_labels(display_min, display_max, chart_height, y_axis_width)

        # Combine Y-axis labels with chart grid
        for i, row in enumerate(chart_grid):
            if i < len(y_labels):
                chart_lines.append(y_labels[i] + '│' + row)
            else:
                chart_lines.append(' ' * y_axis_width + '│' + row)

        # Add grid lines if configured
        self._draw_grid_lines(chart_lines, chart_width, chart_height, y_axis_width)

        # Add threshold lines
        self._draw_threshold_lines(chart_lines, chart_width, chart_height, display_min, display_max, y_axis_width)

        # Add X-axis line
        x_axis_line = ' ' * y_axis_width + '└' + '─' * chart_width
        chart_lines.append(x_axis_line)

        # Add X-axis labels
        x_labels = self._create_x_axis_labels(labels, chart_width, y_axis_width)
        if x_labels.strip():
            chart_lines.append(x_labels)

        # Add axis titles if configured
        if self.x_axis_config.get('title'):
            x_title = ' ' * (y_axis_width + chart_width // 2 - len(self.x_axis_config['title']) // 2) + self.x_axis_config['title']
            chart_lines.append("")
            chart_lines.append(x_title)

        if self.y_axis_config.get('title'):
            chart_lines.append("")
            chart_lines.append(f"  Y-axis: {self.y_axis_config['title']}")

        return '\n'.join(chart_lines)

# Register the line chart
ChartRenderer.register_chart_class('line', LineChart)