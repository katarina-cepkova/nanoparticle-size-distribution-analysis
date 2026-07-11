from colors import DARK_BORDER_COLOR, LIGHT_TEXT_COLOR, DARK_TEXT_COLOR

DARK_LUMINANCE_THRESHOLD :float = 0.5
HISTOGRAM_BORDER_WIDTH :float = 0.5
NO_BORDER_WIDTH :float = 0


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    """Splits a '#RRGGBB' hex code into its (r, g, b) integer components."""
    hex_code = hex_code.lstrip("#")
    r, g, b = (int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
    return r, g, b


def hex_to_rgba(hex_code: str, alpha: float) -> str:
    """Formats a hex color as a CSS rgba() string with the given opacity."""
    r, g, b = hex_to_rgb(hex_code)
    return f"rgba({r}, {g}, {b}, {alpha})"


def relative_luminance(hex_code: str) -> float:
    """Perceived brightness of a hex color, from 0 (black) to 1 (white)."""
    r, g, b = hex_to_rgb(hex_code)
    return 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255)


def border_style_for(hex_code: str) -> tuple[str, float]:
    """Picks a bar border (color, width) that stays visible against a light or dark fill."""
    if relative_luminance(hex_code) < DARK_LUMINANCE_THRESHOLD:
        return hex_code, NO_BORDER_WIDTH
    else:
        return DARK_BORDER_COLOR, HISTOGRAM_BORDER_WIDTH


def text_color_with_bg_color(hex_code: str) -> str:
    """Picks a readable text color (light or dark) for a given background color."""
    if relative_luminance(hex_code) < DARK_LUMINANCE_THRESHOLD:
        return LIGHT_TEXT_COLOR
    else:
        return DARK_TEXT_COLOR
