ORIGIN_CLASSIC_COLORS = [
    "#000000",  # Black
    "#404040",  # Dark Gray
    "#808080",  # Gray
    "#C0C0C0",  # LT Gray
    "#FFFFFF",  # White

    "#808000",  # Dark Yellow
    "#FFFF80",  # LT Yellow
    "#FFFF00",  # Yellow
    "#FF8000",  # Orange

    "#FF0000",  # Red
    "#FF0080",  # Pink
    "#FF00FF",  # Magenta
    "#FF80FF",  # LT Magenta

    "#800000",  # Wine
    "#800080",  # Purple
    "#8000FF",  # Violet

    "#000080",  # Navy
    "#0000A0",  # Royal
    "#0000FF",  # Blue
    "#00FFFF",  # Cyan
    "#80FFFF",  # LT Cyan

    "#008080",  # Dark Cyan
    "#008000",  # Olive
    "#00FF00",  # Green
]


HISTOGRAM_COLORS :list[str] = [
    "#F00082", "#FA3C3C", "#F08228", "#E6AF2D", "#E6DC32",
    "#A0E632", "#00DC00", "#00D28C", "#00C8C8", "#00A0FF",
    "#1E3CFF", "#6E00DC", "#A000C8",

    "#FFB3DD", "#FDC1C1", "#FBD9BD", "#F8E7C0", "#F8F4C0",
    "#E1F8C0", "#B0FFB0", "#AEFFE4", "#ACFFFF", "#B7E4FF",
    "#BBC4FF", "#D8B0FF", "#EEACFF",

    "#FF7DC5", "#FC9898", "#F8BF92", "#F2D797", "#F2EE97",
    "#CEF297", "#75FF75", "#71FFD0", "#6FFFFF", "#82D0FF",
    "#8E9CFF", "#BA75FF", "#E26FFF",

    "#FF44AB", "#FB6F6F", "#F4A666", "#EDC669", "#EDE76D",
    "#BAED6D", "#3CFF3C", "#35FFBD", "#31FFFF", "#4FBDFF",
    "#5E72FF", "#9D3CFF", "#D631FF",

    "#A20059", "#CB0505", "#AF550C", "#A67A13", "#A79F14",
    "#6CA714", "#009300", "#008C5F", "#008686", "#006BAC",
    "#0018BF", "#490093", "#6B0086",

    "#6C003C", "#870303", "#753909", "#6F510D", "#706A0E",
    "#48700E", "#006200", "#005E3F", "#005959", "#004873",
    "#001080", "#310062", "#470059",
]


# button colors
SAVE_PNG_BTN_COLOR :str = "#095256"
PRINT_HISTOGRAM_BTN_COLOR :str = "#087F8C"
CHANGE_COLOR_BTN_COLOR :str = "#5AAA95"

NORMAL_CURVE_COLOR = "#ECC8AF"
LOGNORMAL_CURVE_COLOR = "#E7AD99"
LORENTZIAN_CURVE_COLOR = "#CE796B"

CURVE_INACTIVE_COLOR = "#B0B0B0"


DEFAULT_HISTOGRAM_COLOR: str = HISTOGRAM_COLORS[64]
BG_COLOR :str = "#FFFFFF"
LIGHT_BORDER_COLOR = "#F0F0F0"
DARK_BORDER_COLOR = "#404040"
DARK_AXIS_COLOR = "#000000"

TEXT_COLOR: str = "#000000"          # page text — currently duplicates DARK_BORDER_COLOR's value?
SWATCH_SELECTED_BORDER_COLOR: str = "#0b0b0b"   # was "rgba(11, 11, 11, 1)" via #111 typo, or intentional?
SWATCH_UNSELECTED_BORDER_OPACITY: float = 0.25
SEPARATOR_BORDER_OPACITY: float = 0.15
PANEL_BORDER_COLOR: str = "#DDDDDD"
PANEL_SHADOW_COLOR: str = "rgba(0, 0, 0, 0.12)"