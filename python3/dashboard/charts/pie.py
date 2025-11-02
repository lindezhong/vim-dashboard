"""
Pie chart implementation for vim-dashboard
"""

from typing import List, Dict, Any
from .base import BaseChart


class PieChart(BaseChart):
    """Pie chart renderer using ASCII characters"""
    
    def render(self) -> str:
        """
        Render pie chart data as ASCII art
        
        Returns:
            Rendered chart as string
        """
        try:
            if not self.data:
                return self._handle_empty_data()
            
            # Extract configuration from show section
            show_config = self.config.get('show', {})
            value_column = show_config.get('value_column', self.config.get('value_column', 'value'))
            label_column = show_config.get('label_column', self.config.get('label_column', 'label'))
            
            width = self._get_width() - 10  # Leave space for labels
            height = self._get_height()
            
            # Validate required columns
            for row in self.data:
                if value_column not in row or label_column not in row:
                    return f"Error: Required columns '{value_column}' or '{label_column}' not found"
                if row[value_column] is None or row[label_column] is None:
                    return f"Error: Required columns '{value_column}' or '{label_column}' contain null values"
            
            # Extract and convert data
            pie_data = []
            total = 0
            for row in self.data:
                try:
                    value = float(row.get(value_column, 0))
                    label = str(row.get(label_column, ''))
                    if value > 0:  # Only include positive values
                        pie_data.append({'label': label, 'value': value})
                        total += value
                except (ValueError, TypeError):
                    continue
            
            if not pie_data or total == 0:
                return "Error: No valid positive numeric data found"
            
            # Sort by value (largest first)
            pie_data.sort(key=lambda x: x['value'], reverse=True)
            
            # Build output
            chart_lines = []
            
            # Pie chart symbols for different percentages
            pie_chars = ['█', '▉', '▊', '▋', '▌', '▍', '▎', '▏']
            
            # Calculate and display each slice
            for i, item in enumerate(pie_data):
                value = item['value']
                label = item['label']
                percentage = (value / total) * 100
                
                # Create visual bar representation
                bar_length = int(percentage * width / 100)  # Scale to available width
                
                # Create bar with blocks
                full_blocks = bar_length // 8
                partial_block = bar_length % 8
                
                bar = '█' * full_blocks
                if partial_block > 0 and full_blocks < width // 8:
                    bar += pie_chars[8 - partial_block]
                
                # Truncate label if too long
                display_label = label[:15] if len(label) > 15 else label
                
                # Format line
                line = f"{display_label:<15} │{bar:<20}│ {percentage:6.1f}% ({value})"
                chart_lines.append(line)
            
            # Add summary
            chart_lines.append("")
            chart_lines.append("─" * 50)
            chart_lines.append(f"Total: {total}")
            chart_lines.append(f"Slices: {len(pie_data)}")
            
            # Add legend explanation
            chart_lines.append("")
            chart_lines.append("Legend:")
            chart_lines.append("█ = Full block (12.5%)")
            chart_lines.append("▉▊▋▌▍▎▏ = Partial blocks")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._handle_error(e)