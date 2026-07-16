import plotly.graph_objects as go
from plotly.graph_objects import Figure, Bar, Scatter
from scipy import stats
import numpy as np
import math

from fitting import FitResult, evaluate_fit_pdf
from histogram import HistogramResult
from colors import DARK_AXIS_COLOR, DARK_BORDER_COLOR, BG_COLOR, CURVE_COLORS, LEGEND_TEXT_COLOR
from color_utils import border_style_for, hex_to_rgba
from font_sizes import DEFAULT_FONT_SIZE, AXIS_TITLE_FONT_SIZE, AXIS_TICK_FONT_SIZE, LEGEND_FONT_SIZE


# graph constants
BAR_GAP_FRACTION :float = 0.05  # 5% bin width as a space
TICKS :str ="outside"
TICK_LEN :int = 6
TICK_WIDTH :int = 1

FIGURE_MARGIN :dict[str, int] = dict(l=40, r=20, t=20, b=40)

AXIS_LINE_WIDTH :int = 1
AXIS_TICK_LENGTH :int = 6
AXIS_TICK_WIDTH :int = 1

X_AXIS_TITLE :str = "Nanoparticle Size (nm)"
X_AXIS_TICK0 :float = 0
X_AXIS_DTICK :float = 0.25
X_AXIS_TICKFORMAT :str = ".2f"

Y_AXIS_TITLE :str = "Relative Frequency (%)"
Y_AXIS_TICK0 :float = 0
Y_AXIS_DTICK :float = 5
Y_AXIS_TICKFORMAT :str = ".1f"

CANDIDATE_X_TICK_STEPS :tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
CANDIDATE_Y_TICK_STEPS :tuple[float, ...] = (0.5, 1.0, 2.0, 2.5, 5.0, 10.0, 20.0, 25.0, 50.0, 75.0, 100.0)
MAX_X_TICK_COUNT :int = 20  # ceiling on how many ticks are acceptable on xaxis before escalating
MAX_Y_TICK_COUNT :int = 10


def _pick_dtick(axis_min: float, axis_max: float, tick_steps: tuple[float | int, ...], max_tick_count: int) -> float:
    """Picks the smallest candidate tick step that keeps the axis under MAX_TICK_COUNT ticks."""
    span :float = axis_max - axis_min

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
    raw_dtick :float = pick_x_dtick(axis_min, raw_max)
    rounded_max :float = _round_up_to_dtick(raw_max, raw_dtick)
    dtick :float = pick_x_dtick(axis_min, rounded_max)  # in case the rounded_max would influence the dtick value
    return dtick, rounded_max


def compute_nice_y_axis(axis_min: float, raw_max: float) -> tuple[float, float]:
    """Returns (dtick, rounded_max) so the y-axis edge lands exactly on a tick."""
    raw_dtick :float = pick_y_dtick(axis_min, raw_max)
    rounded_max :float = _round_up_to_dtick(raw_max, raw_dtick)
    dtick :float = pick_y_dtick(axis_min, rounded_max)  # in case the rounded_max would influence the dtick value
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


def build_fit_curve(
        x_min: float, 
        x_max: float, 
        bin_width: float, 
        fit: FitResult, 
        color: str, 
        n_points: int = 300
    ) -> tuple[go.Scatter, float]:
    """Creates a distribution-specific curve and finds its maximum"""

    x :np.ndarray = np.linspace(x_min, x_max, n_points)
    y_density :np.ndarray = evaluate_fit_pdf(x, fit)
    y_percentage :np.ndarray = y_density * bin_width * 100

    curve :go.Scatter = go.Scatter(x=x, y=y_percentage, mode="lines", name=fit.distribution.capitalize(), line=dict(color=color, width=2))
    curve_max :float = float(np.max(y_percentage))

    return curve, curve_max


def build_visual_histogram(
        histogram: HistogramResult, 
        color: str, 
        active_curves: list[str], 
        fit_results: dict[str, FitResult]
    ) -> tuple[Figure, float, float]:
    """Creates a visual histogram with active_curves"""
    figure :Figure = go.Figure()
    x :list[float] = []

    for i in range(histogram.bin_count):
        left :float = histogram.bin_edges[i]
        right :float = histogram.bin_edges[i+1]
        middle :float = (left + right) / 2
        x.append(middle)

    border_color, border_width = border_style_for(color)

    bar :Bar = go.Bar(
        x=x,
        y=histogram.bin_percentages,
        width=histogram.bin_width * (1-BAR_GAP_FRACTION),
        marker_color=color,
        marker_line_color=border_color,
        marker_line_width=border_width
    )

    figure.add_trace(bar)
    # maximum percentage from the active curves
    total_curve_maximum :float = 0.0

    # round the axis max up to a tick so the last tick lands on the axis edge
    x_dtick, x_max = compute_nice_x_axis(X_AXIS_TICK0, histogram.bin_edges[-1])

    # add curves
    for curve_key in active_curves:
        curve :go.Scatter
        curve_max :float
        curve, curve_max = build_fit_curve(
            X_AXIS_TICK0, 
            x_max, 
            histogram.bin_width, 
            fit_results[curve_key], 
            CURVE_COLORS[curve_key]
        )
        figure.add_trace(curve)
        total_curve_maximum = max(total_curve_maximum, curve_max)

    # y-axis must cover the entire graph - whichever (curves, histogram) is taller
    y_dtick, y_max = compute_nice_y_axis(Y_AXIS_TICK0, max(histogram.max_percentage, total_curve_maximum))

    figure.update_layout(
        autosize=True,
        uirevision="constant",
        margin=FIGURE_MARGIN,
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        font=dict(size=DEFAULT_FONT_SIZE),
        legend=dict(
            x=0.98,
            y=0.98,
            xanchor="right",
            yanchor="top",
            bgcolor=hex_to_rgba(BG_COLOR, 0.7), 
            bordercolor=hex_to_rgba(DARK_BORDER_COLOR, 0.15),
            borderwidth=1,
            font=dict(
                size=LEGEND_FONT_SIZE,
                color=LEGEND_TEXT_COLOR,
            ),
            
        ),

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