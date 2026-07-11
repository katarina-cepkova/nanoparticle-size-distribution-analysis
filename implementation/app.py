from dash import Dash, dash, dcc, html, Input, Output, State, Patch, ALL, ctx
# dcc = Dash Core Components (dcc.Graph, dcc.Slider interactive elements)
# html = module with HTML elements

from dash.exceptions import PreventUpdate
from plotly.graph_objects import Figure
import numpy as np
import os
from typing import Any
from pathlib import Path

from histogram import HistogramResult, compute_marks, compute_histogram
from histogram_visual import build_visual_histogram, pick_x_dtick, pick_y_dtick, compute_nice_x_axis, compute_nice_y_axis
from histogram_visual import X_AXIS_TICK0, Y_AXIS_TICK0, Y_AXIS_HARD_MAX
from configuration import BIN_WIDTH_IN_NM, OUTPUT_GRAPH_PATH, OUTPUT_GRAPH_NAME_PREFIX, INPUT_DATA_PATH
from configuration import PNG_EXPORT_WIDTH_IN_PIXELS, PNG_EXPORT_HEIGHT_IN_PIXELS, PNG_EXPORT_SCALE
from file_loader import derive_dataset_label

from colors import HISTOGRAM_COLORS, ORIGIN_CLASSIC_COLORS, DEFAULT_HISTOGRAM_COLOR, DARK_BORDER_COLOR
from colors import PANEL_BORDER_COLOR, PANEL_SHADOW_COLOR, BG_COLOR, LAYOUT_COLOR, BTN_HOVER_BORDER_COLOR
from colors import SAVE_PNG_BTN_COLOR, PRINT_HISTOGRAM_BTN_COLOR, CHANGE_COLOR_BTN_COLOR
from colors import NORMAL_CURVE_COLOR, LOGNORMAL_CURVE_COLOR, LORENTZIAN_CURVE_COLOR, CURVE_INACTIVE_COLOR
from color_utils import hex_to_rgba, text_color_with_bg_color, border_style_for


# color picker grid layout
COLOR_CELL_SIZE = "24px"
COLOR_GRID_COLUMNS = 13

# color picker swatch/panel styling
SWATCH_UNSELECTED_BORDER_OPACITY: float = 0.25
SEPARATOR_BORDER_OPACITY: float = 0.15
PANEL_SHADOW_OPACITY: float = 0.12

SWATCH_SELECTED_BORDER_WIDTH: str = "3px"
SWATCH_UNSELECTED_BORDER_WIDTH: str = "1px"

# bin-width slider bounds
SLIDER_MIN :float = 0.01
SLIDER_STEP :float = 0.01

# curve toggle buttons: (key, label, active color)
CURVE_OPTIONS: list[tuple[str, str, str]] = [
    ("normal", "Normal", NORMAL_CURVE_COLOR),
    ("lognormal", "Lognormal", LOGNORMAL_CURVE_COLOR),
    ("lorentzian", "Lorentzian", LORENTZIAN_CURVE_COLOR),
]

#region BUTTONS
def _build_button(label: str, background_color: str, button_id: str | dict[str, str], extra_style: dict | None = None, **kwargs) -> html.Button:
    """Builds a styled Dash button, picking a readable text color for the given background."""
    style = {
        "padding": "8px 16px",
        "backgroundColor": background_color,
        "color": text_color_with_bg_color(background_color),
        "borderRadius": "6px",
        "cursor": "pointer",
        "fontSize": "14px",
        "--hover-border-color": BTN_HOVER_BORDER_COLOR
    }
    if extra_style:
        style.update(extra_style)

    return html.Button(label, id=button_id, className="app-button", style=style, **kwargs)


def _build_curve_toggle_button(curve_key: str, label: str, active_color: str, active_curves: list[str]) -> html.Button:
    """Builds one curve-toggle button, colored active_color if its curve is currently shown."""
    is_active :bool = curve_key in active_curves
    background_color :str = active_color if is_active else CURVE_INACTIVE_COLOR
    return _build_button(
        label,
        background_color,
        button_id={"type": "curve-toggle", "curve": curve_key},
        extra_style={"width": "100%", "marginBottom": "8px"},
        n_clicks=0,
    )


def _build_curve_toggles(active_curves: list[str]) -> html.Div:
    """Builds the column of curve-toggle buttons, one per entry in CURVE_OPTIONS."""
    return html.Div(
        [_build_curve_toggle_button(key, label, color, active_curves) for key, label, color in CURVE_OPTIONS],
        id="curve-toggle-panel",
    )


def _build_button_panel() -> html.Div:
    """Builds the side panel: save/print/color-change buttons plus the curve toggles."""
    return html.Div(
        [
            html.Div(
                [
                    _build_button("Save PNG", SAVE_PNG_BTN_COLOR, "save-button", extra_style={"width": "100%", "marginBottom": "8px"}),
                    _build_button("Print Histogram Info", PRINT_HISTOGRAM_BTN_COLOR, "print-info-button", 
                                  extra_style={"width": "100%", "marginBottom": "8px"}),
                    _build_change_color_div()
                ],
            ),
            _build_curve_toggles(["normal", "lognormal", "lorentzian"]),
        ],
        style={
            "width": "180px",
            "flex": "0 0 auto",
            "paddingLeft": "16px",
            "paddingTop": "40px",
            "paddingBottom": "80px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        }
    )

#endregion


def _color_swatch(hex_code: str, selected_color: str | None) -> html.Button:
    """Builds one clickable color swatch, outlined thicker when it's the selected color."""
    is_selected = hex_code == selected_color
    return html.Button(
        id={"type": "color-swatch", "hex": hex_code},
        title=hex_code,
        n_clicks=0,
        style={
            "backgroundColor": hex_code,
            "width": COLOR_CELL_SIZE,
            "height": COLOR_CELL_SIZE,
            "borderRadius": "2px",
            "border": f"{SWATCH_SELECTED_BORDER_WIDTH} solid {DARK_BORDER_COLOR}" if is_selected 
                else f"{SWATCH_UNSELECTED_BORDER_WIDTH} solid {hex_to_rgba(DARK_BORDER_COLOR, SWATCH_UNSELECTED_BORDER_OPACITY)}",
            "boxSizing": "border-box",
            "cursor": "pointer",
            "padding": 0
        }
    )


def _color_row_separator() -> html.Div:
    """Builds a thin divider line between the classic and histogram color rows."""
    return html.Div(style={
        "gridColumn": "1 / -1",
        "borderTop": f"1px solid {hex_to_rgba(DARK_BORDER_COLOR, SEPARATOR_BORDER_OPACITY)}",
        "margin": "4px 0",
    })


def _build_color_swatches(selected_color: str | None = None) -> list[html.Button | html.Div]:
    """Builds the full swatch list: classic colors, a separator, then the histogram palette."""
    swatches: list[html.Button | html.Div] = [
        _color_swatch(hex_code, selected_color) for hex_code in ORIGIN_CLASSIC_COLORS]
    swatches.append(_color_row_separator())
    swatches.extend(_color_swatch(hex_code, selected_color) for hex_code in HISTOGRAM_COLORS)

    return swatches


def _build_color_grid(selected_color: str | None = None) -> html.Div:
    """Lays out the color swatches in a fixed-column grid."""
    return html.Div(
        _build_color_swatches(selected_color),
        id="color-grid",
        style={
            "display": "grid",
            "gridTemplateColumns": f"repeat({COLOR_GRID_COLUMNS}, {COLOR_CELL_SIZE})",
            "gap": "2px",
            "padding": "6px",
        },
    )


def _build_change_color_div() -> html.Div:
    """Builds the 'Change color' button and its (initially hidden) popover color grid."""
    return html.Div(
        [
            _build_button("Change color", CHANGE_COLOR_BTN_COLOR, "change-color-button", extra_style={"width": "100%"}, n_clicks=0),
            dcc.Store(id="color-picker", data=DEFAULT_HISTOGRAM_COLOR),
            html.Div(
                _build_color_grid(DEFAULT_HISTOGRAM_COLOR),
                id="color-panel",
                style={
                    "display": "none",
                    "position": "absolute",
                    "top": "0",
                    "right": "calc(100% + 6px)",
                    "width": "fit-content",
                    "maxHeight": "70vh",
                    "overflowY": "auto",
                    "border": f"1px solid {PANEL_BORDER_COLOR}",
                    "borderRadius": "8px",
                    "padding": "4px",
                    "backgroundColor": BG_COLOR,
                    "boxShadow": f"0 4px 12px {hex_to_rgba(PANEL_SHADOW_COLOR, PANEL_SHADOW_OPACITY)}",
                    "zIndex": 10,
                }
            ),
        ],
        style={"position": "relative"},
    )


def build_page_title(input_data_path: Path) -> str:
    """Builds the H1 text, appending the dataset folder name when meaningful."""
    label :str | None = derive_dataset_label(input_data_path)
    title_prefix :str = "Nanoparticle size distribution"
    if label:
        return f"{title_prefix} – {label}"
    return title_prefix



def _build_graph() -> dcc.Graph:
    """Builds the histogram graph."""
    return dcc.Graph(
        id="histogram",
        style={"height": "100%", "width": "100%", "flex": "1 1 auto", "minWidth": 0},
        config={"responsive": True}
    )


def _build_slider(max_value: float) -> dcc.Slider:
    """Builds slider for bin width in nanometers."""
    return dcc.Slider(
        id="bin-width-slider", 
        min=SLIDER_MIN, 
        max=max_value, 
        step=SLIDER_STEP,
        value=BIN_WIDTH_IN_NM, 
        marks=compute_marks(max_value)
    )


def _build_layout(initial_histogram: HistogramResult) -> html.Div:
    """Builds the page layout (graph, button panel, bin-width slider)."""

    _, initial_x_max = compute_nice_x_axis(X_AXIS_TICK0, initial_histogram.max_value)
    _, initial_y_max = compute_nice_y_axis(Y_AXIS_TICK0, initial_histogram.max_percentage)

    return html.Div(
        id="page",
        children=[
            html.H1(build_page_title(INPUT_DATA_PATH), style={"textAlign": "center", "margin": "0 0 20px 0", "flex": "0 0 auto"}),
            html.Div(
                [
                    _build_graph(),
                    _build_button_panel()
                ],
                style={"width": "100%", "flex": "1 1 auto", "minHeight": 0, "display": "flex", "flexDirection": "row"}
            ),
            html.Div(
                _build_slider(initial_histogram.max_value),
                style={"flex": "0 0 auto", "paddingTop": "16px"}
            ),
            dcc.Store(id="x-axis-range", data=[X_AXIS_TICK0, initial_x_max]),
            dcc.Store(id="y-axis-range", data=[Y_AXIS_TICK0, initial_y_max]),
            # holds the actual counted max_value/max_percentage, so an axis reset
            # can rebuild a nice tick-aligned max after the bin width changes
            dcc.Store(id="histogram-stats", data={
                    "max_value": initial_histogram.max_value,
                    "max_percentage": initial_histogram.max_percentage
                }
            ),
            dcc.Store(id="histogram-id", data=0)
        ],
        style={
        "backgroundColor": BG_COLOR,
        "color": LAYOUT_COLOR,
        "height": "100vh",
        "boxSizing": "border-box",
        "padding": "16px",
        "display": "flex",
        "flexDirection": "column",
        "overflow": "hidden",
        }
    )


def build_app(app: Dash, data: np.ndarray, initial_histogram: HistogramResult) -> None:
    """Builds the page layout (graph, button panel, bin-width slider)."""
    app.layout = _build_layout(initial_histogram)
    label :str | None = derive_dataset_label(INPUT_DATA_PATH)
    dataset_label :str
    if not label:
        dataset_label = ""
    else:
        dataset_label = f"_{label}"

    @app.callback(
        Output("histogram", "figure"),
        Output("x-axis-range", "data"),
        Output("y-axis-range", "data"),
        Output("histogram-stats", "data"),
        Output("histogram-id", "data"),
        Input("bin-width-slider", "value"),
        Input("color-picker", "data"),
        Input("histogram", "relayoutData"),
        State("x-axis-range", "data"),
        State("y-axis-range", "data"),
        State("histogram-stats", "data"),
        State("histogram-id", "data")
    )
    def update_histogram(
        bin_width_slider: float,
        color: str,
        relayout_data: dict | None,
        x_range_state: list[float],
        y_range_state: list[float],
        histogram_stats: dict[str, float],
        histogram_id: int
    ) -> tuple[Figure | Patch, list[float] | Any, list[float] | Any, dict[str, float] | Any, int | Any]:
        """Rebuilds or patches the histogram figure for a bin-width, color, or pan/zoom/reset change."""
        # state: x/y-axis-range stores carry the last-seen range so a relayout
        # event (which only reports the axis that changed) can merge with it.
        # histogram_stats carries the actual counted max_value/max_percentage,
        # needed to rebuild a nice axis on reset after the bin width changes.

        # case: color change -> patch marker color only, ranges untouched
        if ctx.triggered_id == "color-picker":
            patched = Patch()
            patched["data"][0]["marker"]["color"] = color
            border_color, border_width = border_style_for(color)
            patched["data"][0]["marker"]["line"]["color"] = border_color
            patched["data"][0]["marker"]["line"]["width"] = border_width
            return patched, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # case: pan/zoom/reset -> patch only the axis/axes relayout_data reports
        if ctx.triggered_id == "histogram":
            if not relayout_data:
                raise PreventUpdate

            patched = Patch()
            updated = False
            x_min, x_max = x_range_state
            y_min, y_max = y_range_state

            if "xaxis.range[0]" in relayout_data or "xaxis.range[1]" in relayout_data:
                # x zoom/pan
                x_min = relayout_data.get("xaxis.range[0]", x_min)
                x_max = relayout_data.get("xaxis.range[1]", x_max)
                patched["layout"]["xaxis"]["dtick"] = pick_x_dtick(x_min, x_max)
                updated = True
            elif relayout_data.get("xaxis.autorange"):
                # x reset: recompute a tick-aligned max from the counted stats,
                # and pin range/tickmode explicitly (autorange wouldn't be nice)
                x_min = X_AXIS_TICK0
                (x_dtick, x_max) = compute_nice_x_axis(X_AXIS_TICK0, histogram_stats["max_value"])
                patched["layout"]["xaxis"]["tickmode"] = "linear"
                patched["layout"]["xaxis"]["range"] = [x_min, x_max]
                patched["layout"]["xaxis"]["dtick"] = x_dtick
                patched["layout"]["xaxis"]["autorange"] = False
                updated = True

            if "yaxis.range[0]" in relayout_data or "yaxis.range[1]" in relayout_data:
                # y zoom/pan, capped below Y_AXIS_HARD_MAX
                y_min = relayout_data.get("yaxis.range[0]", y_min)
                y_max = min(relayout_data.get("yaxis.range[1]", y_max), Y_AXIS_HARD_MAX)
                patched["layout"]["yaxis"]["dtick"] = pick_y_dtick(y_min, y_max)
                patched["layout"]["yaxis"]["range"] = [y_min, y_max]
                updated = True
            elif relayout_data.get("yaxis.autorange"):
                # y reset: same as x reset above
                y_min = Y_AXIS_TICK0
                (y_dtick, y_max) = compute_nice_y_axis(Y_AXIS_TICK0, histogram_stats["max_percentage"])
                patched["layout"]["yaxis"]["tickmode"] = "linear"
                patched["layout"]["yaxis"]["range"] = [y_min, y_max]
                patched["layout"]["yaxis"]["dtick"] = y_dtick
                patched["layout"]["yaxis"]["autorange"] = False
                updated = True

            if not updated:
                raise PreventUpdate  # untracked relayout event, nothing to patch

            return patched, [x_min, x_max], [y_min, y_max], dash.no_update, dash.no_update

        # case: bin-width slider change or initial load -> full rebuild, new histogram id
        histogram = compute_histogram(data, bin_width_slider, initial_histogram.max_value, initial_histogram.nanoparticle_count)
        figure, x_max, y_max = build_visual_histogram(histogram, color)
        # max_value is fixed by the dataset; max_percentage depends on bin width,
        # so it's recounted here and stored for the next axis reset
        stats = {"max_value": initial_histogram.max_value, "max_percentage": histogram.max_percentage}
        new_id = histogram_id + 1

        return (
            figure, 
            [X_AXIS_TICK0, x_max], 
            [Y_AXIS_TICK0, y_max],
            stats,
            new_id
        )
    
        # changing selected color
    @app.callback(
        Output("color-grid", "children"),
        Input("color-picker", "data"),
    )
    def highlight_selected_color(color: str) -> list[html.Button | html.Div]:
        """Redraws the swatch grid so the selected color is outlined."""
        return _build_color_swatches(color)


    @app.callback(
        Output("color-picker", "data"),
        Input({"type": "color-swatch", "hex": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def select_color(_n_clicks: list[int]) -> str:
        """Sets the selected color to the swatch that was clicked."""
        if not ctx.triggered_id or not any(_n_clicks):
            raise PreventUpdate
        return ctx.triggered_id["hex"]


    @app.callback(
        Output("color-panel", "style"),
        Input("change-color-button", "n_clicks"),
        State("color-panel", "style"),
    )
    def toggle_color_panel(n_clicks: int, current_style: dict) -> dict:
        """Shows or hides the color panel on each click of the change-color button."""
        if not n_clicks:
            raise PreventUpdate
        
        style = current_style.copy()

        if n_clicks % 2 == 1:
            style["display"] = "block"
        else:
            style["display"] = "none"

        return style

    
    @app.callback(
        Output("save-button", "n_clicks"),
        Input("save-button", "n_clicks"),
        State("histogram", "figure"),
        State("histogram-id", "data"),
        prevent_initial_call=True,
    )
    def save_histogram_png(n_clicks: int, figure_data: dict, histogram_id: int) -> int:
        if not n_clicks:
            raise PreventUpdate

        figure = Figure(figure_data)
        
        filename :str = f"{OUTPUT_GRAPH_NAME_PREFIX}{dataset_label}_{histogram_id}.png"
        output_path :Path = Path(os.path.join(OUTPUT_GRAPH_PATH, filename))
        figure.write_image(output_path, width=PNG_EXPORT_WIDTH_IN_PIXELS, height=PNG_EXPORT_HEIGHT_IN_PIXELS, scale=PNG_EXPORT_SCALE)

        return n_clicks


    