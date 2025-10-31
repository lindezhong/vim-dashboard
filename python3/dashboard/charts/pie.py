"""
Pie chart implementation for vim-dashboard
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from .base import BaseChart


class PieChart(BaseChart):
    """Pie chart renderer using ASCII characters"""
    
    def __init__(self, console: Console):
        super().__init__(console)
        self.chart_type = "pie"
    
    def render(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """
        Render pie chart data as ASCII art
        
        Args:
            data: List of dictionaries containing chart data
            config: Chart configuration
            
        Returns:
            Rendered chart as string
        """
        try:
            if not data:
                return self._render_error("No data available for pie chart")
            
            # Extract configuration
            value_column = config.get('value_column', 'value')
            label_column = config.get('label_column', 'label')
            title = config.get('title', 'Pie Chart')
            
            # Validate required columns
            if not data[0].get(value_column) or not data[0].get(label_column):
                return self._render_error(f"Required columns '{value_column}' or '{label_column}' not found")
            
            # Calculate percentages
            total = sum(float(row.get(value_column, 0)) for row in data)
            if total == 0:
                return self._render_error("Total value is zero, cannot create pie chart")
            
            # Create pie chart representation
            chart_lines = []
            chart_lines.append(f"📊 {title}")
            chart_lines.append("=" * len(f"📊 {title}"))
            chart_lines.append("")
            
            # Pie chart symbols
            pie_chars = ['█', '▉', '▊', '▋', '▌', '▍', '▎', '▏']
            colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 'white']
            
            for i, row in enumerate(data):
                value = float(row.get(value_column, 0))
                label = str(row.get(label_column, ''))
                percentage = (value / total) * 100
                
                # Create visual bar representation
                bar_length = int(percentage / 2)  # Scale down for display
                color = colors[i % len(colors)]
                
                # Create bar with blocks
                full_blocks = bar_length // 8
                partial_block = bar_length % 8
                
                bar = '█' * full_blocks
                if partial_block > 0:
                    bar += pie_chars[8 - partial_block]
                
                # Format line
                line = f"{label:<20} │{bar:<25}│ {percentage:6.1f}% ({value})"
                chart_lines.append(line)
            
            chart_lines.append("")
            chart_lines.append(f"Total: {total}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return self._render_error(f"Error rendering pie chart: {str(e)}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate pie chart configuration
        
        Args:
            config: Chart configuration to validate
            
        Returns:
            True if configuration is valid
        """
        required_fields = ['value_column', 'label_column']
        
        for field in required_fields:
            if field not in config:
                return False
        
        return True