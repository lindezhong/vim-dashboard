"""
Bubble chart implementation for vim-dashboard
"""

from typing import List, Dict, Any
from .base import BaseChart


class BubbleChart(BaseChart):
    """Bubble chart renderer using ASCII characters"""
    
    def render(self) -> str:
        """
        Render bubble chart data as ASCII art
        
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
            size_column = show_config.get('size_column', self.config.get('size_column', 'size'))
            label_column = show_config.get('label_column', self.config.get('label_column'))
            
            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()
            
            # Validate required columns
            required_columns = [x_column, y_column, size_column]
            for row in self.data:
                for col in required_columns:
                    if col not in row or row[col] is None:
                        return f"Error: Required column '{col}' not found or contains null values"
            
            # Extract and convert data
            points = []
            for row in self.data:
                try:
                    x_val = float(row.get(x_column, 0))
                    y_val = float(row.get(y_column, 0))
                    size_val = float(row.get(size_column, 1))
                    label = str(row.get(label_column, '')) if label_column else ''
                    points.append({
                        'x': x_val,
                        'y': y_val,
                        'size': size_val,
                        'label': label
                    })
                except (ValueError, TypeError):
                    continue
            
            if not points:
                return "Error: No valid numeric data found"
            
            # Calculate ranges
            x_values = [p['x'] for p in points]
            y_values = [p['y'] for p in points]
            size_values = [p['size'] for p in points]
            
            x_min, x_max = min(x_values), max(x_values)
            y_min, y_max = min(y_values), max(y_values)
            size_min, size_max = min(size_values), max(size_values)
            
            # Handle edge cases
            if x_max == x_min:
                x_max = x_min + 1
            if y_max == y_min:
                y_max = y_min + 1
            if size_max == size_min:
                size_max = size_min + 1
            
            # Create grid
            plot_width = width - 8  # Space for axis labels
            plot_height = height - 4  # Space for title and x-axis
            grid = [[' ' for _ in range(plot_width)] for _ in range(plot_height)]
            
            # Bubble symbols by size (small to large)
            bubble_symbols = ['·', '○', '◯', '●', '◉', '⬢', '⬣']
            
            # Plot points
            for point in points:
                # Calculate position
                x_pos = int((point['x'] - x_min) / (x_max - x_min) * (plot_width - 1))
                y_pos = int((point['y'] - y_min) / (y_max - y_min) * (plot_height - 1))
                
                # Flip y-axis (higher values at top)
                y_pos = plot_height - 1 - y_pos
                
                # Ensure within bounds
                x_pos = max(0, min(plot_width - 1, x_pos))
                y_pos = max(0, min(plot_height - 1, y_pos))
                
                # Calculate bubble size (0-6 index for symbols)
                size_ratio = (point['size'] - size_min) / (size_max - size_min)
                symbol_index = int(size_ratio * (len(bubble_symbols) - 1))
                symbol = bubble_symbols[symbol_index]
                
                # Place bubble (handle overlapping)
                if grid[y_pos][x_pos] == ' ':
                    grid[y_pos][x_pos] = symbol
                else:
                    # Use largest symbol for overlapping bubbles
                    current_symbol = grid[y_pos][x_pos]
                    if current_symbol in bubble_symbols:
                        current_index = bubble_symbols.index(current_symbol)
                        if symbol_index > current_index:
                            grid[y_pos][x_pos] = symbol
            
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
            
            # Add axis titles and legend
            chart_lines.append("")
            chart_lines.append(f"X: {x_column} | Y: {y_column} | Size: {size_column}")
            
            # Size legend
            chart_lines.append("Size Legend:")
            legend_line = ""
            for i, symbol in enumerate(bubble_symbols):
                size_val = size_min + (i / (len(bubble_symbols) - 1)) * (size_max - size_min)
                legend_line += f"{symbol}({size_val:.1f}) "
            chart_lines.append(legend_line)
            
            # Data ranges
            chart_lines.append(f"X range: {x_min:.2f} - {x_max:.2f}")
            chart_lines.append(f"Y range: {y_min:.2f} - {y_max:.2f}")
            chart_lines.append(f"Size range: {size_min:.2f} - {size_max:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)