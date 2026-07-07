import plotly.graph_objects as go
from plotly.graph_objects import Figure, Bar
from histogram import HistogramResult


def build_visual_histogram(histogram: HistogramResult, color: str) -> Figure:
    """Creates a visual histogram"""
    figure :Figure = go.Figure()
    # calculate bin width and the middle value on the x axis (bin centres)
    bin_width :float = histogram.bin_edges[1] - histogram.bin_edges[0]
    x :list[float] = []

    for i in range(histogram.bin_count):
        left :float = histogram.bin_edges[i]
        right :float = histogram.bin_edges[i+1]
        middle :float = (left + right) / 2
        x.append(middle)

    bar :Bar = go.Bar(
        x=x,
        y=histogram.bin_counts,
        width=bin_width,
        marker_color=color,
        marker_line_color="rgba(0, 0, 0, 0.4)",
        marker_line_width=1,
    )

    figure.add_trace(bar)
    figure.update_layout(
        autosize=True,
        uirevision="constant",
        margin=dict(l=40, r=20, t=20, b=40)
    )
    return figure