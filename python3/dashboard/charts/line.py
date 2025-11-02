"""
Line chart implementation with proper line visualization and Y-axis labels
"""

from typing import Dict, Any, List, Optional, Tuple
from .base import BaseChart, ChartRenderer
from ..utils import truncate_string

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
        """Create ASCII line chart with proper line visualization."""
        
        # Initialize empty grid
        grid = []
        for _ in range(chart_height):
            grid.append([' '] * chart_width)
        
        # Characters for different series
        point_chars = ['●', '◆', '▲', '■', '♦']
        
        # Plot each series
        for series_idx, y_col in enumerate(self.y_columns):
            column_name = y_col['column']
            if column_name not in series_data:
                continue
                
            values = series_data[column_name]
            if not values:
                continue
            
            point_char = point_chars[series_idx % len(point_chars)]
            
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
                self._draw_line_on_grid(grid, x1, y1, x2, y2, chart_width, chart_height)
            
            # Draw points on top of lines
            for x, y in points:
                if 0 <= x < chart_width and 0 <= y < chart_height:
                    grid[y][x] = point_char
        
        # Convert grid to strings
        result = []
        for row in grid:
            result.append(''.join(row))
        
        return result
    
    def _draw_line_on_grid(self, grid: List[List[str]], x1: int, y1: int, x2: int, y2: int, 
                          chart_width: int, chart_height: int):
        """Draw a line between two points using Bresenham's algorithm."""
        
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
                    # Choose line character based on direction
                    if dx > dy * 2:  # More horizontal
                        grid[y][x] = '─'
                    elif dy > dx * 2:  # More vertical  
                        grid[y][x] = '│'
                    elif (x_step > 0 and y_step > 0) or (x_step < 0 and y_step < 0):
                        grid[y][x] = '\\'  # Diagonal down-right or up-left
                    else:
                        grid[y][x] = '/'   # Diagonal down-left or up-right
            
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
        """Create Y-axis labels for each row."""
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
        """Create x-axis labels line."""
        if not labels:
            return ""
        
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
        """Format value for display."""
        # Use Y-axis format if specified
        y_format = self.y_axis_config.get('format', '{:.0f}')
        try:
            return y_format.format(value)
        except:
            # Fallback to simple formatting
            if abs(value) >= 1000:
                return f"{value/1000:.1f}k"
            elif abs(value) >= 1:
                return f"{value:.0f}"
            else:
                return f"{value:.2f}"
    
    def render(self) -> str:
        """Render line chart with proper line visualization and Y-axis labels."""
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

        # Add legend for multiple series
        if len(self.y_columns) > 1:
            legend_line = "  Legend: "
            point_chars = ['●', '◆', '▲', '■', '♦']
            for i, y_col in enumerate(self.y_columns):
                char = point_chars[i % len(point_chars)]
                legend_line += f"{char} {y_col['label']}  "
            chart_lines.append(legend_line)
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