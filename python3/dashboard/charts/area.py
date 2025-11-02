"""
Area chart implementation for vim-dashboard
"""

from typing import List, Dict, Any
from .base import BaseChart


class AreaChart(BaseChart):
    """Area chart renderer using ASCII characters"""
    
    def render(self) -> str:
        """
        Render area chart data as ASCII art
        
        Returns:
            Rendered chart as string
        """
        try:
            if not self.data:
                return self._handle_empty_data()
            
            # Extract configuration from show section
            show_config = self.config.get('show', {})
            x_column = show_config.get('x_column', self.config.get('x_column', 'x'))

            # Support both single y_column and multiple y_columns
            y_columns_config = show_config.get('y_columns', self.config.get('y_columns', []))
            y_column_single = show_config.get('y_column', self.config.get('y_column', 'y'))

            # Determine y columns to use
            if y_columns_config:
                # Multiple columns configuration
                y_columns = []
                for col_config in y_columns_config:
                    if isinstance(col_config, dict):
                        y_columns.append({
                            'column': col_config.get('column', 'y'),
                            'label': col_config.get('label', col_config.get('column', 'y')),
                            'color': col_config.get('color', '#3498db')
                        })
                    else:
                        # Simple string format
                        y_columns.append({
                            'column': str(col_config),
                            'label': str(col_config),
                            'color': '#3498db'
                        })
            else:
                # Single column configuration
                y_columns = [{
                    'column': y_column_single,
                    'label': y_column_single,
                    'color': '#3498db'
                }]

            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()

            # Validate required columns exist in data
            required_columns = [x_column] + [col['column'] for col in y_columns]
            for row in self.data:
                for col in required_columns:
                    if col not in row:
                        return f"Error: Required column '{col}' not found in data"
                    if row[col] is None:
                        return f"Error: Required column '{col}' contains null values"

            # Extract and convert data for all series
            all_series = []
            all_y_values = []

            for y_col_config in y_columns:
                y_col = y_col_config['column']
                series_points = []

                for row in self.data:
                    try:
                        x_val = str(row.get(x_column, ''))  # Keep x as string for labels
                        y_val = float(row.get(y_col, 0))
                        series_points.append((x_val, y_val))
                        all_y_values.append(y_val)
                    except (ValueError, TypeError):
                        continue

                if series_points:
                    all_series.append({
                        'points': series_points,
                        'label': y_col_config['label'],
                        'column': y_col
                    })

            if not all_series or not all_y_values:
                return "Error: No valid numeric data found"

            # Get unique x values (preserve order from data)
            x_values = []
            seen_x = set()
            for row in self.data:
                x_val = str(row.get(x_column, ''))
                if x_val not in seen_x:
                    x_values.append(x_val)
                    seen_x.add(x_val)

            # Calculate y range
            y_min, y_max = min(all_y_values), max(all_y_values)

            # Handle edge cases
            if y_max == y_min:
                y_max = y_min + 1

            # Ensure y_min is 0 or lower for proper area effect
            if y_min > 0:
                y_min = 0

            # Create grid
            plot_width = width - 12  # Space for axis labels
            plot_height = height - 6  # Space for title, legend and x-axis
            grid = [[' ' for _ in range(plot_width)] for _ in range(plot_height)]

            # Characters for different series (stacked areas)
            area_chars = ['█', '▓', '▒', '░', '▪']
            line_chars = ['●', '◆', '▲', '■', '♦']

            # Plot stacked areas
            stacked = show_config.get('style', {}).get('stacked', True)

            if stacked:
                # For stacked areas, accumulate values
                x_to_cumulative = {}
                for x_val in x_values:
                    x_to_cumulative[x_val] = 0

                # Process each series and stack them
                for series_idx, series in enumerate(all_series):
                    char = area_chars[series_idx % len(area_chars)]
                    line_char = line_chars[series_idx % len(line_chars)]

                    # Create mapping from x to y for this series
                    x_to_y = {}
                    for x_val, y_val in series['points']:
                        x_to_y[x_val] = y_val

                    # Plot this series stacked on previous ones
                    for i, x_val in enumerate(x_values):
                        if x_val in x_to_y:
                            y_val = x_to_y[x_val]
                            base_y = x_to_cumulative[x_val]
                            top_y = base_y + y_val

                            # Update cumulative for next series
                            x_to_cumulative[x_val] = top_y

                            # Calculate positions
                            x_pos = int(i / (len(x_values) - 1) * (plot_width - 1)) if len(x_values) > 1 else plot_width // 2

                            base_y_pos = int((base_y - y_min) / (y_max - y_min) * (plot_height - 1))
                            top_y_pos = int((top_y - y_min) / (y_max - y_min) * (plot_height - 1))

                            # Flip y-axis (higher values at top)
                            base_y_pos = plot_height - 1 - base_y_pos
                            top_y_pos = plot_height - 1 - top_y_pos

                            # Ensure within bounds
                            x_pos = max(0, min(plot_width - 1, x_pos))
                            base_y_pos = max(0, min(plot_height - 1, base_y_pos))
                            top_y_pos = max(0, min(plot_height - 1, top_y_pos))

                            # Fill area from base to top
                            for fill_y in range(top_y_pos, base_y_pos + 1):
                                if 0 <= fill_y < plot_height:
                                    if fill_y == top_y_pos:
                                        # Top line
                                        grid[fill_y][x_pos] = line_char
                                    else:
                                        # Fill area
                                        grid[fill_y][x_pos] = char
            else:
                # Non-stacked areas (overlapping)
                for series_idx, series in enumerate(all_series):
                    char = area_chars[series_idx % len(area_chars)]
                    line_char = line_chars[series_idx % len(line_chars)]

                    # Create mapping from x to y for this series
                    x_to_y = {}
                    for x_val, y_val in series['points']:
                        x_to_y[x_val] = y_val

                    # Plot this series
                    for i, x_val in enumerate(x_values):
                        if x_val in x_to_y:
                            y_val = x_to_y[x_val]

                            # Calculate positions
                            x_pos = int(i / (len(x_values) - 1) * (plot_width - 1)) if len(x_values) > 1 else plot_width // 2
                            y_pos = int((y_val - y_min) / (y_max - y_min) * (plot_height - 1))

                            # Flip y-axis (higher values at top)
                            y_pos = plot_height - 1 - y_pos

                            # Ensure within bounds
                            x_pos = max(0, min(plot_width - 1, x_pos))
                            y_pos = max(0, min(plot_height - 1, y_pos))

                            # Fill area from bottom to current point
                            bottom_y = plot_height - 1  # Bottom of chart
                            for fill_y in range(y_pos, bottom_y + 1):
                                if 0 <= fill_y < plot_height:
                                    if fill_y == y_pos:
                                        # Top line
                                        grid[fill_y][x_pos] = line_char
                                    else:
                                        # Fill area (only if empty or lower priority)
                                        if grid[fill_y][x_pos] == ' ':
                                            grid[fill_y][x_pos] = char

            # Build output
            chart_lines = []

            # Title
            title = show_config.get('title', 'Area Chart')
            chart_lines.append(f"  {title}")
            chart_lines.append("")

            # Legend
            legend_config = show_config.get('legend', {})
            if legend_config.get('show', True) and len(all_series) > 1:
                legend_line = "  Legend: "
                for i, series in enumerate(all_series):
                    char = line_chars[i % len(line_chars)]
                    legend_line += f"{char} {series['label']}  "
                chart_lines.append(legend_line)
                chart_lines.append("")

            # Y-axis labels and grid
            for i, row in enumerate(grid):
                # Calculate y-value for this row
                y_ratio = (plot_height - 1 - i) / (plot_height - 1) if plot_height > 1 else 0
                y_val = y_min + y_ratio * (y_max - y_min)

                # Y-axis label (every few rows)
                if i % max(1, plot_height // 5) == 0 or i == plot_height - 1:
                    y_label = f"{y_val:8.1f}"
                else:
                    y_label = "        "

                chart_lines.append(f"{y_label} │{''.join(row)}")

            # X-axis
            x_axis_line = "         └" + "─" * plot_width
            chart_lines.append(x_axis_line)

            # X-axis labels
            if x_values:
                num_labels = min(5, len(x_values))  # Show max 5 labels
                label_indices = []
                if num_labels == 1:
                    label_indices = [0]
                else:
                    step = (len(x_values) - 1) / (num_labels - 1)
                    label_indices = [int(i * step) for i in range(num_labels)]

                x_axis_labels = "          "
                label_spacing = plot_width // num_labels if num_labels > 0 else plot_width

                for i, idx in enumerate(label_indices):
                    label = str(x_values[idx])[:8]  # Truncate long labels
                    if i == 0:
                        x_axis_labels += label
                    else:
                        # Add spacing
                        spaces_needed = label_spacing - len(str(x_values[label_indices[i-1]]))//2 - len(label)//2
                        x_axis_labels += " " * max(1, spaces_needed) + label

                chart_lines.append(x_axis_labels)

            # Add summary info
            chart_lines.append("")
            chart_lines.append(f"X: {x_column} | Y: {', '.join([col['column'] for col in y_columns])}")
            chart_lines.append(f"Y range: {y_min:.2f} - {y_max:.2f} | Data points: {len(x_values)}")
            if stacked:
                chart_lines.append("Mode: Stacked areas")
            else:
                chart_lines.append("Mode: Overlapping areas")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)