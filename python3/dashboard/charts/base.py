"""
Base chart rendering classes using Rich
"""

import os
import shutil
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.columns import Columns
from ..utils import format_error_message, truncate_string

class BaseChart(ABC):
    """Abstract base class for all chart types."""

    def __init__(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        self.data = data
        self.config = config
        self.style = config.get('style', {})
        self.console = Console(width=self._get_width(), legacy_windows=False)

    def _get_width(self) -> Optional[int]:
        """Get chart width from config or terminal."""
        width = self.style.get('width')
        if width:
            return int(width)

        # Auto-detect terminal width
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80  # Default fallback

    def _get_height(self) -> int:
        """Get chart height from config."""
        return int(self.style.get('height', 20))

    def _get_title(self) -> Optional[str]:
        """Get chart title."""
        base_title = self.config.get('title') or self.style.get('title')

        # Add countdown information if available
        countdown_info = self.config.get('_countdown_info')
        if countdown_info:
            countdown_display = countdown_info.get('countdown_display', '')
            if countdown_display:
                if base_title:
                    return f"{base_title} | Next refresh: {countdown_display}"
                else:
                    return f"Dashboard | Next refresh: {countdown_display}"

        return base_title

    def _get_title_style(self) -> str:
        """Get title style."""
        return self.style.get('title_style', 'bold magenta')

    def _format_title(self, title: str) -> Text:
        """Format chart title with style."""
        return Text(title, style=self._get_title_style())

    def _render_variables_info(self) -> Optional[Panel]:
        """Render variables information panel if variables exist."""
        variables_info = self.config.get('_variables_info')
        if not variables_info:
            return None

        # Create variables table
        variables_table = Table(show_header=True, header_style="bold blue", box=None)
        variables_table.add_column("Variable", style="cyan", width=20)
        variables_table.add_column("Type", style="yellow", width=10)
        variables_table.add_column("Current Value", style="green", width=25)
        variables_table.add_column("Description", style="dim", width=30)

        # Add each variable to the table
        for var_name, var_info in variables_info.items():
            var_type = var_info.get('type', 'string')
            current_value = str(var_info.get('current_value', ''))
            description = var_info.get('description', '')

            # Truncate long values for display
            if len(current_value) > 23:
                current_value = current_value[:20] + "..."
            if len(description) > 28:
                description = description[:25] + "..."

            variables_table.add_row(var_name, var_type, current_value, description)

        # Create help text
        help_text = Text("Press 'v' to modify variables, 'r' to refresh", style="dim italic")

        # Combine table and help text
        content = Columns([variables_table, help_text], equal=False, expand=True)

        return Panel(
            content,
            title="[bold cyan]Variables[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )

    def _create_panel(self, content: Union[str, Text], title: Optional[str] = None) -> Panel:
        """Create a Rich panel with optional title."""
        panel_title = None
        if title:
            panel_title = self._format_title(title)

        border_style = self.style.get('border_style', 'blue')

        return Panel(
            content,
            title=panel_title,
            border_style=border_style,
            padding=(0, 1)
        )

    def _handle_empty_data(self) -> str:
        """Handle case when no data is available."""
        message = "No data available"
        return str(Align.center(Text(message, style="dim")))

    def _handle_error(self, error: Exception) -> str:
        """Handle rendering errors."""
        error_msg = format_error_message(error, "Chart Rendering")
        return str(Align.center(Text(error_msg, style="bold red")))

    @abstractmethod
    def render(self) -> str:
        """Render the chart and return as string."""
        pass

    def render_to_string(self) -> str:
        """Render chart to string with error handling."""
        try:
            # Render variables info panel if available
            variables_panel = self._render_variables_info()

            # Render main chart content
            if not self.data:
                chart_content = self._handle_empty_data()
            else:
                chart_content = self.render()

            # Create main chart panel
            title = self._get_title()
            if title:
                chart_panel = self._create_panel(chart_content, title)
            else:
                chart_panel = chart_content

            # Combine variables panel and chart
            with self.console.capture() as capture:
                if variables_panel:
                    self.console.print(variables_panel)
                    self.console.print()  # Add spacing

                if isinstance(chart_panel, Panel):
                    self.console.print(chart_panel)
                else:
                    self.console.print(chart_panel)

            return capture.get()
                
        except Exception as e:
            return self._handle_error(e)


class ChartRenderer:
    """Factory class for creating and rendering charts."""
    
    # Registry of chart classes
    _chart_classes = {}
    
    @classmethod
    def register_chart_class(cls, chart_type: str, chart_class: type):
        """Register a chart class for a chart type."""
        cls._chart_classes[chart_type] = chart_class
    
    @classmethod
    def create_chart(cls, chart_type: str, data: List[Dict[str, Any]], config: Dict[str, Any]) -> BaseChart:
        """Create appropriate chart based on type."""
        if chart_type not in cls._chart_classes:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        chart_class = cls._chart_classes[chart_type]
        return chart_class(data, config)
    
    @classmethod
    def render_chart(cls, chart_type: str, data: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Create and render chart in one step."""
        chart = cls.create_chart(chart_type, data, config)
        return chart.render_to_string()
    
    @classmethod
    def get_supported_charts(cls) -> List[str]:
        """Get list of supported chart types."""
        return list(cls._chart_classes.keys())
    
    @classmethod
    def is_supported(cls, chart_type: str) -> bool:
        """Check if chart type is supported."""
        return chart_type in cls._chart_classes


class ASCIIChartHelper:
    """Helper class for ASCII character-based chart rendering."""
    
    # Chart characters for different elements
    CHART_CHARS = {
        'bar': {
            'full': '█',
            'partial': ['▏', '▎', '▍', '▌', '▋', '▊', '▉'],
            'empty': ' '
        },
        'line': {
            'point': '●',
            'line_h': '─',
            'line_v': '│',
            'corner_tl': '┌',
            'corner_tr': '┐',
            'corner_bl': '└',
            'corner_br': '┘',
            'cross': '┼',
            'tee_up': '┴',
            'tee_down': '┬',
            'tee_left': '┤',
            'tee_right': '├'
        },
        'scatter': {
            'points': ['●', '○', '◆', '◇', '▲', '△', '■', '□', '★', '☆']
        },
        'pie': {
            'segments': ['◐', '◑', '◒', '◓', '●', '○', '◉', '◎']
        }
    }
    
    @classmethod
    def get_bar_char(cls, value: float, max_value: float, width: int) -> str:
        """Get bar character representation for a value."""
        if max_value == 0:
            return cls.CHART_CHARS['bar']['empty'] * width
        
        ratio = value / max_value
        filled_width = ratio * width
        full_blocks = int(filled_width)
        partial_block = filled_width - full_blocks
        
        result = cls.CHART_CHARS['bar']['full'] * full_blocks
        
        if partial_block > 0 and full_blocks < width:
            partial_chars = cls.CHART_CHARS['bar']['partial']
            partial_index = int(partial_block * len(partial_chars))
            if partial_index < len(partial_chars):
                result += partial_chars[partial_index]
                full_blocks += 1
        
        # Fill remaining with empty spaces
        remaining = width - len(result)
        if remaining > 0:
            result += cls.CHART_CHARS['bar']['empty'] * remaining
        
        return result
    
    @classmethod
    def create_axis(cls, width: int, height: int, x_labels: List[str] = None, y_labels: List[str] = None) -> List[str]:
        """Create ASCII axis for charts."""
        lines = []
        
        # Create chart area
        for i in range(height):
            if i == height - 1:  # Bottom line (x-axis)
                line = cls.CHART_CHARS['line']['corner_bl']
                line += cls.CHART_CHARS['line']['line_h'] * (width - 2)
                line += cls.CHART_CHARS['line']['corner_br']
            else:  # Side lines
                line = cls.CHART_CHARS['line']['line_v']
                line += ' ' * (width - 2)
                line += cls.CHART_CHARS['line']['line_v']
            lines.append(line)
        
        return lines
    
    @classmethod
    def normalize_data(cls, values: List[float], target_range: tuple = (0, 1)) -> List[float]:
        """Normalize data values to target range."""
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return [target_range[0]] * len(values)
        
        range_size = max_val - min_val
        target_size = target_range[1] - target_range[0]
        
        normalized = []
        for val in values:
            norm_val = ((val - min_val) / range_size) * target_size + target_range[0]
            normalized.append(norm_val)
        
        return normalized