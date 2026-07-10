import plotly.graph_objects as go
from plotly.graph_objects import Figure, Bar
import math

from histogram import HistogramResult
from colors import DARK_AXIS_COLOR, BG_COLOR
from color_utils import border_style_for
from font_sizes import DEFAULT_FONT_SIZE, AXIS_TITLE_FONT_SIZE, AXIS_TICK_FONT_SIZE


# graph constants
BAR_GAP_FRACTION :float = 0.05  # 5% bin width as a space
TICKS :str ="outside"
TICK_LEN :int = 6
TICK_WIDTH :int = 1

FIGURE_MARGIN: dict[str, int] = dict(l=40, r=20, t=20, b=40)

AXIS_LINE_WIDTH: int = 1
AXIS_TICK_LENGTH: int = 6
AXIS_TICK_WIDTH: int = 1

X_AXIS_TITLE: str = "Nanoparticle Size (nm)"
X_AXIS_TICK0: float = 0
X_AXIS_DTICK: float = 0.25
X_AXIS_TICKFORMAT: str = ".2f"

Y_AXIS_TITLE: str = "Relative Frequency (%)"
Y_AXIS_TICK0 :float = 0
Y_AXIS_DTICK: float = 5
Y_AXIS_TICKFORMAT: str = ".1f"
Y_AXIS_HARD_MAX: float = 100.0

CANDIDATE_X_TICK_STEPS: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
CANDIDATE_Y_TICK_STEPS: tuple[float, ...] = (0.5, 1.0, 2.0, 2.5, 5.0, 10.0, 20.0)
MAX_X_TICK_COUNT: int = 20  # ceiling on how many ticks are acceptable on xaxis before escalating
MAX_Y_TICK_COUNT: int = 10 


def _pick_dtick(axis_min: float, axis_max: float, tick_steps: tuple[float | int, ...], max_tick_count: int) -> float:
    """Picks the smallest candidate tick step that keeps the axis under MAX_TICK_COUNT ticks."""
    span: float = axis_max - axis_min

    for step in tick_steps:
        if span / step <= max_tick_count:
            return step

    return tick_steps[-1]

def pick_x_dtick(axis_min: float, axis_max: float) -> float:
    """Picks the smallest candidate tick step that keeps the x-axis under MAX_X_TICK_COUNT ticks."""
    return _pick_dtick(axis_min, axis_max, CANDIDATE_X_TICK_STEPS, MAX_X_TICK_COUNT)


def pick_y_dtick(axis_min: float, axis_max: float) -> float:
    """Picks the smallest candidate tick step that keeps the y-axis under MAX_Y_TICK_COUNT ticks."""
    return _pick_dtick(axis_min, axis_max, CANDIDATE_Y_TICK_STEPS, MAX_Y_TICK_COUNT)


def _round_up_to_dtick(value: float, dtick: float) -> float:
    """Rounds value up to the nearest multiple of dtick, so the axis edge lands on a tick."""
    return math.ceil(value / dtick) * dtick


def compute_nice_x_axis(axis_min: float, raw_max: float) -> tuple[float, float]:
    """Returns (dtick, rounded_max) so the x-axis edge lands exactly on a tick."""
    raw_dtick = pick_x_dtick(axis_min, raw_max)
    rounded_max = _round_up_to_dtick(raw_max, raw_dtick)
    dtick = pick_x_dtick(axis_min, rounded_max)  # in case the rounded_max would influence the dtick value
    return dtick, rounded_max


def compute_nice_y_axis(axis_min: float, raw_max: float) -> tuple[float, float]:
    """Returns (dtick, rounded_max) so the y-axis edge lands exactly on a tick."""
    raw_dtick = pick_y_dtick(axis_min, raw_max)
    rounded_max = _round_up_to_dtick(raw_max, raw_dtick)
    dtick = pick_y_dtick(axis_min, rounded_max)  # in case the rounded_max would influence the dtick value
    return dtick, rounded_max


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


def build_visual_histogram(histogram: HistogramResult, color: str) -> tuple[Figure, float, float]:
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

    border_color, border_width = border_style_for(color)
    # round the axis max up to a tick so the last tick lands on the axis edge
    x_dtick, x_max = compute_nice_x_axis(X_AXIS_TICK0, histogram.max_value)
    y_dtick, y_max = compute_nice_y_axis(Y_AXIS_TICK0, histogram.max_percentage)

    bar :Bar = go.Bar(
        x=x,
        y=histogram.bin_percentages,
        width=bin_width * (1-BAR_GAP_FRACTION),
        marker_color=color,
        marker_line_color=border_color,
        marker_line_width=border_width
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
            range=[X_AXIS_TICK0, x_max],
            dtick=x_dtick,
            tickformat=X_AXIS_TICKFORMAT,
        ),

        yaxis=dict(
            **build_base_axis(),
            title=Y_AXIS_TITLE,
            tick0=Y_AXIS_TICK0,
            range=[Y_AXIS_TICK0, y_max],
            dtick=y_dtick,
            tickformat=Y_AXIS_TICKFORMAT,
        )
    )
    return figure, x_max, y_max