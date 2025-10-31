"""
Scatter plot implementation for vim-dashboard
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from .base import BaseChart


class ScatterChart(BaseChart):
    """Scatter plot renderer using ASCII characters"""
    
    def __init__(self, console: Console):
        super().__init__(console)
        self.chart_type = "scatter"
    
    def render(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """
        Render scatter plot data as ASCII art
        
        Args:
            data: List of dictionaries containing chart data
            config: Chart configuration
            
        Returns:
            Rendered chart as string
        """
        try:
            if not data:
                return self._render_error("No data available for scatter plot")
            
            # Extract configuration
            x_column = config.get('x_column', 'x')
            y_column = config.get('y_column', 'y')
            title = config.get('title', 'Scatter Plot')
            width = config.get('width', 60)
            height = config.get('height', 20)
            
            # Validate required columns
            if not all(row.get(x_column) is not None and row.get(y_column) is not None for row in data):
                return self._render_error(f"Required columns '{x_column}' or '{y_column}' not found or contain null values")
            
            # Extract and convert data
            x_values = []
            y_values = []
            
            for row in data:
                try:
                    x_val = float(row.get(x_column, 0))
                    y_val = float(row.get(y_column, 0))
                    x_values.append(x_val)
                    y_values.append(y_val)
                except (ValueError, TypeError):
                    continue
            
            if not x_values or not y_values:
                return self._render_error("No valid numeric data found")
            
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
            plot_width = width - 10  # Reserve space for y-axis labels
            plot_height = height - 3  # Reserve space for x-axis and title
            
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
            chart_lines.append(f"📊 {title}")
            chart_lines.append("=" * len(f"📊 {title}"))
            chart_lines.append("")
            
            # Y-axis labels and grid
            for i, row in enumerate(grid):
                # Calculate y-value for this row
                y_ratio = (plot_height - 1 - i) / (plot_height - 1) if plot_height > 1 else 0
                y_value = y_min + y_ratio * (y_max - y_min)
                
                # Format y-axis label
                y_label = f"{y_value:6.1f}"
                
                # Add row with y-axis label
                row_str = ''.join(row)
                chart_lines.append(f"{y_label} │{row_str}│")
            
            # X-axis
            x_axis_line = " " * 7 + "└" + "─" * plot_width + "┘"
            chart_lines.append(x_axis_line)
            
            # X-axis labels
            x_labels = []
            num_labels = min(5, plot_width // 10)  # Limit number of labels
            for i in range(num_labels + 1):
                if num_labels > 0:
                    x_ratio = i / num_labels
                else:
                    x_ratio = 0
                x_value = x_min + x_ratio * (x_max - x_min)
                x_labels.append(f"{x_value:.1f}")
            
            # Format x-axis labels
            label_spacing = plot_width // max(1, len(x_labels) - 1) if len(x_labels) > 1 else plot_width
            x_axis_labels = " " * 8
            for i, label in enumerate(x_labels):
                if i == 0:
                    x_axis_labels += label
                elif i == len(x_labels) - 1:
                    x_axis_labels = x_axis_labels.ljust(8 + plot_width - len(label)) + label
                else:
                    pos = 8 + i * label_spacing - len(label) // 2
                    while len(x_axis_labels) < pos:
                        x_axis_labels += " "
                    x_axis_labels += label
            
            chart_lines.append(x_axis_labels)
            chart_lines.append("")
            chart_lines.append(f"X: {x_column}, Y: {y_column}")
            chart_lines.append(f"Points: {len(x_values)}")
            chart_lines.append(f"X range: {x_min:.2f} - {x_max:.2f}")
            chart_lines.append(f"Y range: {y_min:.2f} - {y_max:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._render_error(f"Error rendering scatter plot: {str(e)}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate scatter plot configuration
        
        Args:
            config: Chart configuration to validate
            
        Returns:
            True if configuration is valid
        """
        required_fields = ['x_column', 'y_column']
        
        for field in required_fields:
            if field not in config:
                return False
        
        return True