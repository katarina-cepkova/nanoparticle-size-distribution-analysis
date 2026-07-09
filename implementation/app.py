from dash import Dash, dcc, html
# dcc = Dash Core Components (dcc.Graph, dcc.Slider interactive elements)
# html = module with HTML elements

import numpy as np

from histogram import HistogramResult, compute_marks
from configuration import BIN_WIDTH_IN_NM

from colors import HISTOGRAM_COLORS, ORIGIN_CLASSIC_COLORS, DEFAULT_HISTOGRAM_COLOR, DARK_BORDER_COLOR
from colors import PANEL_BORDER_COLOR, PANEL_SHADOW_COLOR, BG_COLOR, LAYOUT_COLOR
from colors import SAVE_PNG_BTN_COLOR, PRINT_HISTOGRAM_BTN_COLOR, CHANGE_COLOR_BTN_COLOR
from colors import NORMAL_CURVE_COLOR, LOGNORMAL_CURVE_COLOR, LORENTZIAN_CURVE_COLOR, CURVE_INACTIVE_COLOR
from color_utils import hex_to_rgba, text_color_with_bg_color


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
        "border": "none",
        "borderRadius": "6px",
        "cursor": "pointer",
        "fontSize": "14px",
    }
    if extra_style:
        style.update(extra_style)

    return html.Button(label, id=button_id, style=style, **kwargs)


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
    return html.Div(
        id="page",
        children=[
            html.H1("Nanoparticle size distribution", style={"textAlign": "center", "margin": "0 0 20px 0", "flex": "0 0 auto"}),
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
            )
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

