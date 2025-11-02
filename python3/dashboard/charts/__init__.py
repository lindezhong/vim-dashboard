"""
Chart rendering module for vim-dashboard using Rich
"""

from .base import ChartRenderer, BaseChart
from .table import TableChart
from .bar import BarChart
from .line import LineChart
from .pie import PieChart
from .scatter import ScatterChart
from .area import AreaChart
from .histogram import HistogramChart
from .boxplot import BoxplotChart
from .heatmap import HeatmapChart
from .bubble import BubbleChart

# Register all chart types
ChartRenderer.register_chart_class('table', TableChart)
ChartRenderer.register_chart_class('bar', BarChart)
ChartRenderer.register_chart_class('line', LineChart)
ChartRenderer.register_chart_class('pie', PieChart)
ChartRenderer.register_chart_class('scatter', ScatterChart)
ChartRenderer.register_chart_class('area', AreaChart)
ChartRenderer.register_chart_class('histogram', HistogramChart)
ChartRenderer.register_chart_class('boxplot', BoxplotChart)
ChartRenderer.register_chart_class('heatmap', HeatmapChart)
ChartRenderer.register_chart_class('bubble', BubbleChart)

__all__ = [
    'ChartRenderer',
    'BaseChart',
    'TableChart',
    'BarChart',
    'LineChart',
    'PieChart',
    'ScatterChart',
    'AreaChart',
    'HistogramChart',
    'BoxplotChart',
    'HeatmapChart',
    'BubbleChart'
]