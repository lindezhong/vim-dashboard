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
            y_column = show_config.get('y_column', self.config.get('y_column', 'y'))
            
            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()
            
            # Validate required columns
            for row in self.data:
                if x_column not in row or y_column not in row:
                    return f"Error: Required columns '{x_column}' or '{y_column}' not found"
                if row[x_column] is None or row[y_column] is None:
                    return f"Error: Required columns '{x_column}' or '{y_column}' contain null values"
            
            # Extract and convert data
            points = []
            for row in self.data:
                try:
                    x_val = float(row.get(x_column, 0))
                    y_val = float(row.get(y_column, 0))
                    points.append((x_val, y_val))
                except (ValueError, TypeError):
                    continue
            
            if not points:
                return "Error: No valid numeric data found"
            
            # Sort by x-value for proper area rendering
            points.sort(key=lambda p: p[0])
            
            # Calculate ranges
            x_values = [p[0] for p in points]
            y_values = [p[1] for p in points]
            
            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)
            
            # Handle edge cases
            if x_max == x_min:
                x_max = x_min + 1
            if y_max == y_min:
                y_max = y_min + 1
            
            # Ensure y_min is 0 or lower for proper area effect
            if y_min > 0:
                y_min = 0
            
            # Create grid
            plot_width = width - 8  # Space for axis labels
            plot_height = height - 4  # Space for title and x-axis
            grid = [[' ' for _ in range(plot_width)] for _ in range(plot_height)]
            
            # Plot area
            for i in range(len(points)):
                x_val, y_val = points[i]
                
                # Calculate position
                x_pos = int((x_val - x_min) / (x_max - x_min) * (plot_width - 1))
                y_pos = int((y_val - y_min) / (y_max - y_min) * (plot_height - 1))
                
                # Flip y-axis (higher values at top)
                y_pos = plot_height - 1 - y_pos
                
                # Ensure within bounds
                x_pos = max(0, min(plot_width - 1, x_pos))
                y_pos = max(0, min(plot_height - 1, y_pos))
                
                # Fill area from bottom to current point
                bottom_y = plot_height - 1  # Bottom of chart
                for fill_y in range(y_pos, bottom_y + 1):
                    if fill_y < plot_height:
                        if fill_y == y_pos:
                            # Top line of area
                            grid[fill_y][x_pos] = '●'
                        elif fill_y == bottom_y:
                            # Bottom line (baseline)
                            grid[fill_y][x_pos] = '▁'
                        else:
                            # Fill area
                            grid[fill_y][x_pos] = '█'
                
                # Connect points with lines if not first point
                if i > 0:
                    prev_x, prev_y = points[i-1]
                    prev_x_pos = int((prev_x - x_min) / (x_max - x_min) * (plot_width - 1))
                    prev_y_pos = int((prev_y - y_min) / (y_max - y_min) * (plot_height - 1))
                    prev_y_pos = plot_height - 1 - prev_y_pos
                    
                    prev_x_pos = max(0, min(plot_width - 1, prev_x_pos))
                    prev_y_pos = max(0, min(plot_height - 1, prev_y_pos))
                    
                    # Draw line between points
                    if prev_x_pos != x_pos:
                        # Interpolate between points
                        steps = abs(x_pos - prev_x_pos)
                        for step in range(1, steps):
                            interp_x = prev_x_pos + step * (x_pos - prev_x_pos) // steps
                            interp_y = prev_y_pos + step * (y_pos - prev_y_pos) // steps
                            
                            if 0 <= interp_x < plot_width and 0 <= interp_y < plot_height:
                                # Fill area for interpolated points
                                for fill_y in range(interp_y, bottom_y + 1):
                                    if fill_y < plot_height:
                                        if fill_y == interp_y:
                                            grid[fill_y][interp_x] = '●'
                                        elif fill_y == bottom_y:
                                            grid[fill_y][interp_x] = '▁'
                                        else:
                                            grid[fill_y][interp_x] = '█'
            
            # Build output
            chart_lines = []
            
            # Y-axis labels and grid
            for i, row in enumerate(grid):
                # Calculate y-value for this row
                y_ratio = (plot_height - 1 - i) / (plot_height - 1) if plot_height > 1 else 0
                y_val = y_min + y_ratio * (y_max - y_min)
                
                # Y-axis label (every few rows)
                if i % max(1, plot_height // 5) == 0 or i == plot_height - 1:
                    y_label = f"{y_val:6.1f}"
                else:
                    y_label = "      "
                
                chart_lines.append(f"{y_label} │{''.join(row)}")
            
            # X-axis
            x_axis_line = "       └" + "─" * plot_width
            chart_lines.append(x_axis_line)
            
            # X-axis labels
            x_labels = []
            num_labels = min(5, plot_width // 8)  # Max 5 labels, spaced appropriately
            for i in range(num_labels):
                if num_labels == 1:
                    x_ratio = 0.5
                else:
                    x_ratio = i / (num_labels - 1)
                x_val = x_min + x_ratio * (x_max - x_min)
                x_labels.append(f"{x_val:6.1f}")
            
            # Format x-axis labels
            if x_labels:
                label_spacing = plot_width // len(x_labels) if len(x_labels) > 1 else plot_width // 2
                x_axis_labels = "        "
                for i, label in enumerate(x_labels):
                    if i == 0:
                        x_axis_labels += label
                    else:
                        # Add spacing
                        spaces_needed = label_spacing - len(x_labels[i-1]) // 2 - len(label) // 2
                        x_axis_labels += " " * max(1, spaces_needed) + label
                chart_lines.append(x_axis_labels)
            
            # Add axis titles
            chart_lines.append("")
            chart_lines.append(f"X: {x_column} | Y: {y_column}")
            chart_lines.append(f"X range: {x_min:.2f} - {x_max:.2f}")
            chart_lines.append(f"Y range: {y_min:.2f} - {y_max:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)