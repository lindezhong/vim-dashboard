"""
Scatter plot implementation for vim-dashboard
"""

from typing import List, Dict, Any
from .base import BaseChart


class ScatterChart(BaseChart):
    """Scatter plot renderer using ASCII characters"""
    
    def render(self) -> str:
        """
        Render scatter plot data as ASCII art
        
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
            x_values = []
            y_values = []
            
            for row in self.data:
                try:
                    x_val = float(row.get(x_column, 0))
                    y_val = float(row.get(y_column, 0))
                    x_values.append(x_val)
                    y_values.append(y_val)
                except (ValueError, TypeError):
                    continue
            
            if not x_values or not y_values:
                return "Error: No valid numeric data found"
            
            # Calculate ranges
            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)
            
            if x_min == x_max:
                x_min -= 1
                x_max += 1
            if y_min == y_max:
                y_min -= 1
                y_max += 1
            
            # Create plot grid
            plot_width = width - 8  # Reserve space for y-axis labels
            plot_height = height - 4  # Reserve space for x-axis and title
            
            # Initialize grid
            grid = [[' ' for _ in range(plot_width)] for _ in range(plot_height)]
            
            # Plot points
            for x_val, y_val in zip(x_values, y_values):
                # Scale to grid coordinates
                x_pos = int((x_val - x_min) / (x_max - x_min) * (plot_width - 1))
                y_pos = int((y_val - y_min) / (y_max - y_min) * (plot_height - 1))
                
                # Flip y-axis (higher values at top)
                y_pos = plot_height - 1 - y_pos
                
                # Ensure within bounds
                x_pos = max(0, min(plot_width - 1, x_pos))
                y_pos = max(0, min(plot_height - 1, y_pos))
                
                # Place point (use different symbols for overlapping points)
                if grid[y_pos][x_pos] == ' ':
                    grid[y_pos][x_pos] = '●'
                elif grid[y_pos][x_pos] == '●':
                    grid[y_pos][x_pos] = '◉'
                else:
                    grid[y_pos][x_pos] = '⬢'
            
            # Build output
            chart_lines = []
            
            # Y-axis labels and grid
            for i, row in enumerate(grid):
                # Calculate y-value for this row
                y_ratio = (plot_height - 1 - i) / (plot_height - 1) if plot_height > 1 else 0
                y_value = y_min + y_ratio * (y_max - y_min)
                
                # Y-axis label (every few rows)
                if i % max(1, plot_height // 5) == 0 or i == plot_height - 1:
                    y_label = f"{y_value:6.1f}"
                else:
                    y_label = "      "
                
                # Add row with y-axis label
                row_str = ''.join(row)
                chart_lines.append(f"{y_label} │{row_str}")
            
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
                x_value = x_min + x_ratio * (x_max - x_min)
                x_labels.append(f"{x_value:6.1f}")
            
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
            
            # Add axis titles and statistics
            chart_lines.append("")
            chart_lines.append(f"X: {x_column} | Y: {y_column}")
            chart_lines.append(f"Points: {len(x_values)}")
            chart_lines.append(f"X range: {x_min:.2f} - {x_max:.2f}")
            chart_lines.append(f"Y range: {y_min:.2f} - {y_max:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)