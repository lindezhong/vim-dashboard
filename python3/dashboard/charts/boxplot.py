"""
Box plot implementation for vim-dashboard
"""

from typing import List, Dict, Any
import math
from .base import BaseChart


class BoxplotChart(BaseChart):
    """Box plot renderer using ASCII characters"""
    
    def render(self) -> str:
        """
        Render box plot data as ASCII art
        
        Returns:
            Rendered chart as string
        """
        try:
            if not self.data:
                return self._handle_empty_data()
            
            # Extract configuration from show section
            show_config = self.config.get('show', {})
            category_column = show_config.get('category_column', self.config.get('category_column', 'category'))
            value_column = show_config.get('value_column', self.config.get('value_column', 'value'))
            
            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()
            
            # Validate required columns
            for row in self.data:
                if category_column not in row or value_column not in row:
                    return f"Error: Required columns '{category_column}' or '{value_column}' not found"
                if row[category_column] is None or row[value_column] is None:
                    return f"Error: Required columns contain null values"
            
            # Group data by category
            categories = {}
            for row in self.data:
                try:
                    cat = str(row.get(category_column, ''))
                    val = float(row.get(value_column, 0))
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(val)
                except (ValueError, TypeError):
                    continue
            
            if not categories:
                return "Error: No valid data found"
            
            # Calculate statistics for each category
            box_stats = {}
            all_values = []
            
            for cat, values in categories.items():
                if not values:
                    continue
                
                values.sort()
                n = len(values)
                all_values.extend(values)
                
                # Calculate quartiles
                q1_idx = n // 4
                q2_idx = n // 2
                q3_idx = 3 * n // 4
                
                q1 = values[q1_idx] if q1_idx < n else values[0]
                q2 = values[q2_idx] if q2_idx < n else values[0]  # median
                q3 = values[q3_idx] if q3_idx < n else values[-1]
                
                # Calculate IQR and outliers
                iqr = q3 - q1
                lower_fence = q1 - 1.5 * iqr
                upper_fence = q3 + 1.5 * iqr
                
                # Find whiskers (min/max within fences)
                lower_whisker = min([v for v in values if v >= lower_fence], default=values[0])
                upper_whisker = max([v for v in values if v <= upper_fence], default=values[-1])
                
                # Find outliers
                outliers = [v for v in values if v < lower_fence or v > upper_fence]
                
                box_stats[cat] = {
                    'q1': q1,
                    'q2': q2,
                    'q3': q3,
                    'lower_whisker': lower_whisker,
                    'upper_whisker': upper_whisker,
                    'outliers': outliers,
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
            
            # Calculate overall range for scaling
            if all_values:
                global_min = min(all_values)
                global_max = max(all_values)
            else:
                return "Error: No valid numeric data found"
            
            if global_max == global_min:
                global_max = global_min + 1
            
            # Create chart
            plot_width = width - 8  # Space for axis labels
            plot_height = height - 6  # Space for title, x-axis, and category labels
            
            # Build output
            chart_lines = []
            
            # Calculate box width and positions
            num_categories = len(box_stats)
            if num_categories == 0:
                return "Error: No categories found"
            
            box_width = max(3, plot_width // (num_categories * 2))  # Leave space between boxes
            box_spacing = plot_width // num_categories
            
            # Draw the plot
            for row in range(plot_height):
                line = "       │"
                
                cat_idx = 0
                for cat, stats in box_stats.items():
                    # Calculate box position
                    box_start = cat_idx * box_spacing + (box_spacing - box_width) // 2
                    box_end = box_start + box_width
                    
                    # Scale values to plot coordinates
                    def scale_value(val):
                        return int((val - global_min) / (global_max - global_min) * (plot_height - 1))
                    
                    current_row_from_bottom = plot_height - 1 - row
                    
                    # Get scaled positions
                    q1_pos = scale_value(stats['q1'])
                    q2_pos = scale_value(stats['q2'])
                    q3_pos = scale_value(stats['q3'])
                    lower_whisker_pos = scale_value(stats['lower_whisker'])
                    upper_whisker_pos = scale_value(stats['upper_whisker'])
                    
                    # Draw box plot elements
                    for x in range(plot_width):
                        if box_start <= x < box_end:
                            # Inside box area
                            if current_row_from_bottom == q1_pos or current_row_from_bottom == q3_pos:
                                # Box edges (Q1 and Q3)
                                line += '─'
                            elif q1_pos < current_row_from_bottom < q3_pos:
                                # Inside box
                                if current_row_from_bottom == q2_pos:
                                    # Median line
                                    line += '━'
                                else:
                                    # Box fill
                                    line += '│'
                            elif current_row_from_bottom == lower_whisker_pos or current_row_from_bottom == upper_whisker_pos:
                                # Whisker ends
                                line += '┬' if current_row_from_bottom == upper_whisker_pos else '┴'
                            elif lower_whisker_pos < current_row_from_bottom < q1_pos or q3_pos < current_row_from_bottom < upper_whisker_pos:
                                # Whisker lines
                                if x == box_start + box_width // 2:
                                    line += '│'
                                else:
                                    line += ' '
                            else:
                                # Check for outliers
                                outlier_found = False
                                for outlier in stats['outliers']:
                                    outlier_pos = scale_value(outlier)
                                    if current_row_from_bottom == outlier_pos and x == box_start + box_width // 2:
                                        line += '○'
                                        outlier_found = True
                                        break
                                if not outlier_found:
                                    line += ' '
                        else:
                            line += ' '
                    
                    cat_idx += 1
                
                chart_lines.append(line)
            
            # X-axis
            x_axis_line = "       └" + "─" * plot_width
            chart_lines.append(x_axis_line)
            
            # Category labels
            cat_labels_line = "        "
            cat_idx = 0
            for cat in box_stats.keys():
                label_pos = cat_idx * box_spacing + box_spacing // 2
                # Truncate long category names
                cat_name = cat[:8] if len(cat) > 8 else cat
                
                # Add spacing to reach the label position
                while len(cat_labels_line) - 8 < label_pos - len(cat_name) // 2:
                    cat_labels_line += " "
                
                cat_labels_line += cat_name
                cat_idx += 1
            
            chart_lines.append(cat_labels_line)
            
            # Y-axis labels (value range)
            y_label_lines = []
            for i in range(5):  # 5 y-axis labels
                val = global_min + (global_max - global_min) * (4 - i) / 4
                y_label_lines.append(f"{val:6.1f}")
            
            # Insert y-axis labels
            for i, line_idx in enumerate(range(0, len(chart_lines) - 2, len(chart_lines) // 6)):
                if line_idx < len(chart_lines) and i < len(y_label_lines):
                    chart_lines[line_idx] = y_label_lines[i] + chart_lines[line_idx][6:]
            
            # Add statistics
            chart_lines.append("")
            chart_lines.append(f"Categories: {category_column} | Values: {value_column}")
            chart_lines.append(f"Range: {global_min:.2f} - {global_max:.2f}")
            
            # Add summary for each category
            for cat, stats in box_stats.items():
                chart_lines.append(f"{cat}: Q1={stats['q1']:.1f}, Median={stats['q2']:.1f}, Q3={stats['q3']:.1f}, n={stats['count']}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)