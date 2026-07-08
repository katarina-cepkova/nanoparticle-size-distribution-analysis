import plotly.graph_objects as go
from plotly.graph_objects import Figure, Bar
from histogram import HistogramResult
from colors import DARK_AXIS_COLOR
from font_sizes import DEFAULT_FONT_SIZE, AXIS_TITLE_FONT_SIZE, AXIS_TICK_FONT_SIZE


# graph constants
BAR_GAP_FRACTION :float = 0.05  # 5% bin width as a space
BG_COLOR :str = "#FFFFFF"
TICKS :str ="outside"
TICK_LEN :int = 6
TICK_WIDTH :int = 1
TICK_COLOR=DARK_AXIS_COLOR

FIGURE_MARGIN: dict[str, int] = dict(l=40, r=20, t=20, b=40)

AXIS_LINE_WIDTH: int = 1
AXIS_TICK_LENGTH: int = 6
AXIS_TICK_WIDTH: int = 1

X_AXIS_TITLE: str = "Nanoparticle Size (nm)"
X_AXIS_TICK0: float = 0
X_AXIS_DTICK: float = 0.25
X_AXIS_TICKFORMAT: str = ".2f"

Y_AXIS_TITLE: str = "Relative Frequency (%)"
Y_AXIS_DTICK: float = 5
Y_AXIS_TICKFORMAT: str = ".1f"

CANDIDATE_TICK_STEPS: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
MAX_TICK_COUNT: int = 20  # ceiling on how many ticks are acceptable before escalating


def _pick_dtick(axis_min: float, axis_max: float) -> float:
    span: float = axis_max - axis_min

    for step in CANDIDATE_TICK_STEPS:
        if span / step <= MAX_TICK_COUNT:
            return step

    return CANDIDATE_TICK_STEPS[-1]


def build_base_axis() -> dict:
    """Creates an axis"""
    return dict(
        showgrid=False,
        showline=True,
        linecolor=DARK_AXIS_COLOR,
        linewidth=AXIS_LINE_WIDTH,
        mirror=True,
        title_font=dict(size=AXIS_TITLE_FONT_SIZE),
        tickfont=dict(size=AXIS_TICK_FONT_SIZE),
        ticks="outside",
        ticklen=AXIS_TICK_LENGTH,
        tickwidth=AXIS_TICK_WIDTH,
        tickcolor=DARK_AXIS_COLOR,
    )


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
        y=histogram.bin_percentages,
        width=bin_width * (1-BAR_GAP_FRACTION),
        marker_color=color
    )

    figure.add_trace(bar)
    figure.update_layout(
        autosize=True,
        uirevision="constant",
        margin=FIGURE_MARGIN,
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        font=dict(size=DEFAULT_FONT_SIZE),

        xaxis=dict(
            **build_base_axis(),  # ** unpacks the returned dict
            title=X_AXIS_TITLE,
            tick0=X_AXIS_TICK0,
            dtick=_pick_dtick(X_AXIS_TICK0, histogram.max_value),
            tickformat=X_AXIS_TICKFORMAT,
        ),

        yaxis=dict(
            **build_base_axis(),
            title=Y_AXIS_TITLE,
            dtick=Y_AXIS_DTICK,
            tickformat=Y_AXIS_TICKFORMAT,
        )
    )
    return figure