"""
Bar chart implementation using Rich
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.text import Text
from rich.align import Align
from .base import BaseChart, ChartRenderer, ASCIIChartHelper
from ..utils import truncate_string


class BarChart(BaseChart):
    """Bar chart implementation using ASCII characters."""
    
    def __init__(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        super().__init__(data, config)
        self.show_config = config.get('show', {})
        self.x_column = self.show_config.get('x_column', 'x')
        self.y_column = self.show_config.get('y_column', 'y')
        
    def _extract_chart_data(self) -> tuple[List[str], List[float]]:
        """Extract x and y data from the dataset."""
        labels = []
        values = []
        
        for row in self.data:
            x_val = row.get(self.x_column, '')
            y_val = row.get(self.y_column, 0)
            
            # Convert label to string and truncate if needed
            label = str(x_val)
            max_label_length = self.style.get('max_label_length', 15)
            if max_label_length:
                label = truncate_string(label, max_label_length)
            
            # Convert value to float
            try:
                value = float(y_val) if y_val is not None else 0.0
            except (ValueError, TypeError):
                value = 0.0
            
            labels.append(label)
            values.append(value)
        
        return labels, values
    
    def _get_chart_dimensions(self) -> tuple[int, int]:
        """Get chart dimensions."""
        width = self._get_width()
        height = self._get_height()
        
        # Reserve space for labels and axes
        chart_width = max(20, width - 20) if width else 60
        chart_height = max(5, height - 5)
        
        return chart_width, chart_height
    
    def _create_horizontal_bar_chart(self, labels: List[str], values: List[float]) -> List[str]:
        """Create horizontal bar chart."""
        if not values:
            return ["No data to display"]
        
        chart_width, chart_height = self._get_chart_dimensions()
        max_value = max(values) if values else 1
        max_label_width = max(len(label) for label in labels) if labels else 0
        max_label_width = min(max_label_width, 15)  # Limit label width
        
        # Calculate bar width (reserve space for labels and padding)
        bar_width = max(10, chart_width - max_label_width - 10)
        
        lines = []
        
        # Limit number of bars to fit in height
        max_bars = min(len(labels), chart_height)
        
        for i in range(max_bars):
            label = labels[i]
            value = values[i]
            
            # Create bar
            bar_chars = ASCIIChartHelper.get_bar_char(value, max_value, bar_width)
            
            # Format value display
            value_str = self._format_value(value)
            
            # Create line with label, bar, and value
            label_part = f"{label:<{max_label_width}}"
            line = f"{label_part} │{bar_chars}│ {value_str}"
            lines.append(line)
        
        # Add truncation indicator if needed
        if len(labels) > max_bars:
            lines.append(f"{'...':<{max_label_width}} │{'':>{bar_width}}│ ({len(labels) - max_bars} more)")
        
        return lines
    
    def _create_vertical_bar_chart(self, labels: List[str], values: List[float]) -> List[str]:
        """Create vertical bar chart."""
        if not values:
            return ["No data to display"]
        
        chart_width, chart_height = self._get_chart_dimensions()
        max_value = max(values) if values else 1
        
        # Limit number of bars to fit in width
        max_bars = min(len(labels), chart_width // 3)  # Each bar needs at least 3 chars
        
        if max_bars == 0:
            return ["Chart too narrow"]
        
        # Calculate bar positions
        bar_width = max(1, chart_width // max_bars)
        
        lines = []
        
        # Create chart from top to bottom
        for row in range(chart_height - 2, -1, -1):  # Reserve bottom row for labels
            line_chars = []
            
            for i in range(max_bars):
                value = values[i]
                # Calculate bar height for this value
                bar_height = int((value / max_value) * (chart_height - 2))
                
                if row < bar_height:
                    # This row should have bar content
                    bar_char = ASCIIChartHelper.CHART_CHARS['bar']['full']
                else:
                    bar_char = ' '
                
                # Add bar character(s) with spacing
                line_chars.extend([bar_char] * (bar_width - 1))
                line_chars.append(' ')  # Spacing between bars
            
            lines.append(''.join(line_chars[:chart_width]))
        
        # Add x-axis line
        axis_line = '─' * chart_width
        lines.append(axis_line)
        
        # Add labels
        label_line_chars = []
        for i in range(max_bars):
            label = labels[i]
            # Truncate label to fit bar width
            truncated_label = truncate_string(label, bar_width - 1)
            label_line_chars.extend(list(f"{truncated_label:<{bar_width - 1}}"))
            label_line_chars.append(' ')
        
        lines.append(''.join(label_line_chars[:chart_width]))
        
        # Add truncation indicator if needed
        if len(labels) > max_bars:
            lines.append(f"... ({len(labels) - max_bars} more bars)")
        
        return lines
    
    def _format_value(self, value: float) -> str:
        """Format value for display."""
        format_str = self.style.get('value_format', '{:.1f}')
        try:
            return format_str.format(value)
        except:
            return str(value)
    
    def render(self) -> str:
        """Render bar chart."""
        labels, values = self._extract_chart_data()
        
        if not labels or not values:
            return self._handle_empty_data()
        
        # Choose chart orientation
        orientation = self.show_config.get('orientation', 'horizontal')
        
        if orientation == 'vertical':
            chart_lines = self._create_vertical_bar_chart(labels, values)
        else:
            chart_lines = self._create_horizontal_bar_chart(labels, values)
        
        # Join lines and return
        chart_content = '\n'.join(chart_lines)
        
        # Add statistics if enabled
        if self.style.get('show_stats', False):
            stats = self._generate_stats(values)
            chart_content += '\n\n' + stats
        
        return chart_content
    
    def _generate_stats(self, values: List[float]) -> str:
        """Generate statistics for the chart."""
        if not values:
            return ""
        
        total = sum(values)
        avg = total / len(values)
        max_val = max(values)
        min_val = min(values)
        
        stats_lines = [
            f"Total: {self._format_value(total)}",
            f"Average: {self._format_value(avg)}",
            f"Max: {self._format_value(max_val)}",
            f"Min: {self._format_value(min_val)}"
        ]
        
        return ' | '.join(stats_lines)


# Register the bar chart
ChartRenderer.register_chart_class('bar', BarChart)