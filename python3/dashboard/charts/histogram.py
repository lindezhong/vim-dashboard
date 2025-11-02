"""
Histogram implementation for vim-dashboard
"""

from typing import List, Dict, Any
import math
from .base import BaseChart


class HistogramChart(BaseChart):
    """Histogram renderer using ASCII characters"""
    
    def render(self) -> str:
        """
        Render histogram data as ASCII art
        
        Returns:
            Rendered chart as string
        """
        try:
            if not self.data:
                return self._handle_empty_data()
            
            # Extract configuration from show section
            show_config = self.config.get('show', {})
            value_column = show_config.get('value_column', self.config.get('value_column', 'value'))
            bins = show_config.get('bins', self.config.get('bins', 10))  # Number of bins
            
            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()
            
            # Validate required columns
            for row in self.data:
                if value_column not in row or row[value_column] is None:
                    return f"Error: Required column '{value_column}' not found or contains null values"
            
            # Extract and convert data
            values = []
            for row in self.data:
                try:
                    val = float(row.get(value_column, 0))
                    values.append(val)
                except (ValueError, TypeError):
                    continue
            
            if not values:
                return "Error: No valid numeric data found"
            
            # Calculate histogram bins
            min_val = min(values)
            max_val = max(values)
            
            if max_val == min_val:
                # All values are the same
                bin_counts = [len(values)]
                bin_edges = [min_val, min_val + 1]
                bin_centers = [min_val + 0.5]
            else:
                # Create bins
                bin_width = (max_val - min_val) / bins
                bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
                bin_counts = [0] * bins
                bin_centers = [min_val + (i + 0.5) * bin_width for i in range(bins)]
                
                # Count values in each bin
                for value in values:
                    # Find which bin this value belongs to
                    bin_index = int((value - min_val) / bin_width)
                    # Handle edge case where value equals max_val
                    if bin_index >= bins:
                        bin_index = bins - 1
                    bin_counts[bin_index] += 1
            
            # Create chart
            plot_width = width - 8  # Space for axis labels
            plot_height = height - 4  # Space for title and x-axis
            
            max_count = max(bin_counts) if bin_counts else 1
            
            # Build output
            chart_lines = []
            
            # Draw histogram bars
            for row in range(plot_height):
                line = "       │"
                
                for bin_idx in range(len(bin_counts)):
                    # Calculate bar width for this bin
                    bar_width = max(1, plot_width // len(bin_counts))
                    
                    # Calculate bar height for this row
                    bar_height_ratio = bin_counts[bin_idx] / max_count if max_count > 0 else 0
                    bar_height = int(bar_height_ratio * plot_height)
                    
                    # Determine if this row should have a bar
                    current_row_from_bottom = plot_height - 1 - row
                    
                    if current_row_from_bottom < bar_height:
                        # This row has a bar
                        if current_row_from_bottom == bar_height - 1:
                            # Top of bar
                            bar_char = '▀'
                        else:
                            # Middle of bar
                            bar_char = '█'
                        
                        line += bar_char * bar_width
                    else:
                        # Empty space
                        line += ' ' * bar_width
                
                chart_lines.append(line)
            
            # X-axis
            x_axis_line = "       └" + "─" * plot_width
            chart_lines.append(x_axis_line)
            
            # X-axis labels (bin centers)
            x_labels = []
            num_labels = min(5, len(bin_centers))  # Max 5 labels
            if num_labels > 0:
                step = len(bin_centers) // num_labels if num_labels > 1 else 1
                for i in range(0, len(bin_centers), step):
                    if i < len(bin_centers):
                        x_labels.append(f"{bin_centers[i]:.1f}")
                
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
            
            # Y-axis labels (frequency counts)
            y_label_lines = []
            for i in range(5):  # 5 y-axis labels
                count_val = (max_count * (4 - i)) // 4
                y_label_lines.append(f"{count_val:6d}")
            
            # Insert y-axis labels
            for i, line_idx in enumerate(range(0, len(chart_lines) - 2, len(chart_lines) // 6)):
                if line_idx < len(chart_lines) and i < len(y_label_lines):
                    chart_lines[line_idx] = y_label_lines[i] + chart_lines[line_idx][6:]
            
            # Add statistics
            chart_lines.append("")
            chart_lines.append(f"Column: {value_column}")
            chart_lines.append(f"Total samples: {len(values)}")
            chart_lines.append(f"Bins: {len(bin_counts)}")
            chart_lines.append(f"Range: {min_val:.2f} - {max_val:.2f}")
            chart_lines.append(f"Mean: {sum(values) / len(values):.2f}")
            
            # Calculate standard deviation
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = math.sqrt(variance)
            chart_lines.append(f"Std Dev: {std_dev:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)