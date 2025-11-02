"""
Heatmap implementation for vim-dashboard
"""

from typing import List, Dict, Any
from .base import BaseChart


class HeatmapChart(BaseChart):
    """Heatmap renderer using ASCII characters and color intensity"""
    
    def render(self) -> str:
        """
        Render heatmap data as ASCII art
        
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
            value_column = show_config.get('value_column', self.config.get('value_column', 'value'))
            
            width = self._get_width() - 15  # Leave space for labels
            height = self._get_height()
            
            # Validate required columns
            for row in self.data:
                required_cols = [x_column, y_column, value_column]
                for col in required_cols:
                    if col not in row or row[col] is None:
                        return f"Error: Required column '{col}' not found or contains null values"
            
            # Extract and organize data
            heatmap_data = {}
            x_values = set()
            y_values = set()
            all_values = []
            
            for row in self.data:
                try:
                    x_val = str(row.get(x_column, ''))
                    y_val = str(row.get(y_column, ''))
                    val = float(row.get(value_column, 0))
                    
                    x_values.add(x_val)
                    y_values.add(y_val)
                    all_values.append(val)
                    
                    if y_val not in heatmap_data:
                        heatmap_data[y_val] = {}
                    heatmap_data[y_val][x_val] = val
                    
                except (ValueError, TypeError):
                    continue
            
            if not heatmap_data:
                return "Error: No valid data found"
            
            # Sort values for consistent ordering
            x_sorted = sorted(x_values)
            y_sorted = sorted(y_values)
            
            # Calculate value range for color mapping
            min_val = min(all_values)
            max_val = max(all_values)
            
            if max_val == min_val:
                max_val = min_val + 1
            
            # Define intensity characters (from light to dark)
            intensity_chars = [' ', '░', '▒', '▓', '█']
            
            def get_intensity_char(value):
                """Map value to intensity character"""
                if max_val == min_val:
                    return intensity_chars[2]  # Middle intensity
                
                ratio = (value - min_val) / (max_val - min_val)
                char_index = int(ratio * (len(intensity_chars) - 1))
                return intensity_chars[char_index]
            
            # Calculate cell dimensions
            max_x_label_len = max(len(x) for x in x_sorted) if x_sorted else 1
            max_y_label_len = max(len(y) for y in y_sorted) if y_sorted else 1
            
            # Adjust for available space
            cell_width = max(1, (width - max_y_label_len - 2) // len(x_sorted)) if x_sorted else 1
            cell_height = 1  # Each row is one character high
            
            # Build output
            chart_lines = []
            
            # Header with x-axis labels
            header_line = " " * (max_y_label_len + 2)
            for x_val in x_sorted:
                # Truncate x labels to fit cell width
                x_label = x_val[:cell_width] if len(x_val) > cell_width else x_val
                # Center the label in the cell
                padding = (cell_width - len(x_label)) // 2
                header_line += " " * padding + x_label + " " * (cell_width - len(x_label) - padding)
            chart_lines.append(header_line)
            
            # Separator line
            separator = " " * (max_y_label_len + 2) + "─" * (len(x_sorted) * cell_width)
            chart_lines.append(separator)
            
            # Data rows
            for y_val in y_sorted:
                # Y-axis label
                y_label = y_val[:max_y_label_len] if len(y_val) > max_y_label_len else y_val
                y_label = y_label.rjust(max_y_label_len)
                
                row_line = y_label + " │"
                
                for x_val in x_sorted:
                    # Get value for this cell
                    cell_value = heatmap_data.get(y_val, {}).get(x_val, 0)
                    
                    # Get intensity character
                    intensity_char = get_intensity_char(cell_value)
                    
                    # Fill cell with intensity character
                    cell_content = intensity_char * cell_width
                    row_line += cell_content
                
                chart_lines.append(row_line)
            
            # Add legend
            chart_lines.append("")
            chart_lines.append("Intensity Legend:")
            legend_line = ""
            for i, char in enumerate(intensity_chars):
                if i == 0:
                    val = min_val
                elif i == len(intensity_chars) - 1:
                    val = max_val
                else:
                    val = min_val + (i / (len(intensity_chars) - 1)) * (max_val - min_val)
                legend_line += f"{char}({val:.1f}) "
            chart_lines.append(legend_line)
            
            # Add statistics
            chart_lines.append("")
            chart_lines.append(f"X: {x_column} | Y: {y_column} | Values: {value_column}")
            chart_lines.append(f"Dimensions: {len(x_sorted)} x {len(y_sorted)}")
            chart_lines.append(f"Value range: {min_val:.2f} - {max_val:.2f}")
            
            # Calculate and show statistics
            mean_val = sum(all_values) / len(all_values)
            chart_lines.append(f"Mean: {mean_val:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)