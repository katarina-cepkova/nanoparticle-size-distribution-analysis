# Developer Guide

This guide documents the architecture, technologies, and reasoning behind
key design decisions in the **Nanoparticle Size Distribution Analysis Tool**.

It draws on the project's development history to explain not just *what*
the code does, but *why* it's structured this way.

See also: **[README](../README.md)** · **[USER DOCUMENTATION](USER_DOC.md)** · **[STATISTICS](STATISTICS.md)** · **[CHEATSHEET](CHEATSHEET.md)**

---

## 1. Technologies used

| Technology | Role |
|---|---|
| Python 3.10+ | Language |
| Dash / Plotly | Interactive web-based chart and UI |
| NumPy | Numerical arrays, histogram binning |
| SciPy (`stats`, `optimize`) | Distribution fitting (MLE), Kolmogorov–Smirnov test, root-finding for FWHM |
| pandas | Reading CSV/Excel files into DataFrames |
| openpyxl | Excel file parsing (via pandas) |
| Kaleido | Server-side PNG export of Plotly figures |
| python-dotenv | Loading `.env` configuration at startup |

---

## 2. Architectural principle: strict layer separation

The codebase is deliberately split into layers with a one-directional
dependency flow. This was an explicit, recurring decision throughout
development — functions are placed according to *which layer they
conceptually belong to*, not where it's most convenient to add them.

```
configuration.py, domain_errors.py      (foundation — no internal deps)
        ↓
data_loader.py, file_loader.py          (data ingestion)
        ↓
histogram.py, fitting.py, ks_test.py,   (pure computation)
moments.py, statistics_helpers.py
        ↓
histogram_visual.py, colors.py,         (presentation)
color_utils.py, font_sizes.py
        ↓
output_printing.py, printer.py          (report output)
        ↓
app.py                                  (Dash wiring / UI callbacks)
        ↓
main.py                                 (entry point / composition root)
```

**Rule of thumb applied throughout:** computation functions return plain
dataclasses and never touch Dash, Plotly, or printing concerns; the
presentation layer never recomputes statistics that computation already
produced; `configuration.py` never imports from higher layers.

### 2.1 Data flow through the pipeline

The layers above describe *what depends on what*; this is the actual
sequence of calls `main.py` makes through them on a normal run:

```
main.py
  ├─ parse_args() 
  |     → argparse.Namespace
  |
  ├─ DirectoryLoader(...).load_data() / ConsoleLoader(...).load_data()
  │     → ParticleSizesData (data.sizes, per-source counts)
  |
  ├─ compute_moments(data.sizes)                    
  |     → MomentsResult
  |
  ├─ fit_normal / fit_lognormal / fit_lorentzian(data.sizes)
  │     → FitResult (×3)
  |
  ├─ compute_ks_test(data.sizes, fit) for each fit
  |     → KSTestResult (×3)
  |
  ├─ compute_histogram(data.sizes, BIN_WIDTH_IN_NM, ...)
  │     → HistogramResult
  |
  ├─ print_measurement_summary / print_moments_summary / 
  |  print_fit_and_ks_table(printer, ...)
  │     → written via Printer (console/file/both)
  |
  └─ build_app(...) + app.run()
        → hands control to Dash (see §7 for the callbacks that take over)
```

Everything above the `build_app()` call runs exactly once, synchronously,
before the browser is involved at all — the printed report reflects the
data as loaded, independent of anything the user later does in the
interactive chart.

---

## 3. Module reference

| Module | Responsibility |
|---|---|
| `configuration.py` | Loads `.env`, exposes typed constants, creates required directories, sets up logging, ensures Kaleido's headless Chrome is available |
| `domain_errors.py` | Custom exception hierarchy (`AppError` → `InvalidInputError`, `InvalidFileFormatError`, etc.), each carrying a human-readable `.message` |
| `data_loader.py` | `DataLoader` ABC with `ConsoleLoader` (interactive stdin input) and `DirectoryLoader` (recursive folder scan) implementations; aggregates results into `ParticleSizesData` |
| `file_loader.py` | `FileLoader` ABC with `CsvFileLoader` / `ExcelFileLoader`; also `derive_dataset_label()`, used for labeling output filenames/reports based on a single input subfolder |
| `histogram.py` | `HistogramResult` dataclass and `compute_histogram()` — bins data, computes per-bin percentages, empirical mode, and stores `bin_width` as a first-class field |
| `fitting.py` | `FitResult` dataclass and `fit_normal()` / `fit_lognormal()` / `fit_lorentzian()` — MLE fitting via `scipy.stats`, plus FWHM via root-finding |
| `ks_test.py` | Kolmogorov–Smirnov goodness-of-fit test against each fitted distribution |
| `moments.py` | `MomentsResult` dataclass — mean, variance, std, skewness, CV, median, PDI, D32 (Sauter mean diameter) |
| `statistics_helpers.py` | Shared helpers (`compute_cv`, `compute_PDI`) used by both `moments.py` and `fitting.py` |
| `histogram_visual.py` | Builds the Plotly `Figure` — bars, fit curves, axis tick/range logic |
| `colors.py` / `color_utils.py` | Color palettes and color-derived styling (luminance-based border/text contrast) |
| `printer.py` | `Printer` ABC with `ConsolePrinter`, `FilePrinter`, and `CompositePrinter` implementations |
| `output_printing.py` | Formats and prints the statistical report tables using a `Printer` |
| `app.py` | Builds the Dash layout and wires up all callbacks (bin width, color, curve toggles, PNG export, axis pan/zoom/reset) |
| `main.py` | Composition root: parses CLI args, selects a data loader, builds printers, runs the full analysis pipeline, launches the Dash app |

> **First-run note:** `configuration.py`'s `_ensure_chrome_available()`
> calls `kaleido.get_chrome_sync()`, which downloads a headless Chrome
> binary the first time the app runs (needed for PNG export). This
> requires internet access on that first run; subsequent runs reuse the
> already-downloaded binary and work fully offline.

---

## 4. Key design decisions

### 4.1 Computation returns dataclasses, not tuples or dicts

`HistogramResult`, `FitResult`, `MomentsResult`, and `KSTestResult` are all
`@dataclass`. Fields are added to these as new information is needed by
downstream consumers, rather than recomputing that information at each
call site. A few concrete examples:
 
- **`HistogramResult.bin_width`** was added directly to the dataclass
  rather than re-derived from `bin_edges[1] - bin_edges[0]` wherever it
  was needed, because it's an input the computation layer already
  receives — storing it keeps that fact in one place instead of
  re-deriving it (fragile, since it silently assumes equal-width bins)
  in every consumer.
- **`HistogramResult.max_value` / `max_percentage`** are computed once
  inside `compute_histogram()` and stored, rather than having
  `app.py` or `histogram_visual.py` call `np.max(...)` themselves each
  time they need the current bounds — this keeps "what's the tallest bar"
  as a computation-layer fact, not something the presentation layer
  derives from raw arrays it wasn't given ownership of.
- **`FitResult.theoretical_mode` / `theoretical_median` / `theoretical_std`
  / `fwhm` / `rel_fwhm`**, etc. are all computed once, right when the
  distribution is fitted in `fitting.py`, and stored on the dataclass —
  rather than having `output_printing.py` or `histogram_visual.py`
  reconstruct a `scipy.stats` distribution object from `params`/`loc`/
  `scale` and recompute these values themselves whenever they're
  displayed.
- **`MomentsResult.D32` / `PDI` / `cv`** follow the same pattern: computed
  once in `compute_moments()`, using the shared `compute_cv()` /
  `compute_PDI()` helpers, and stored as plain fields rather than
  functions the report-printing code would need to call again with the
  right inputs.

The common thread: whichever module *first* has the raw data needed to
compute a value is responsible for computing it exactly once and storing
it on the dataclass it returns; every other layer treats that dataclass
as the **single source of truth** rather than recomputing from more primitive inputs.

### 4.2 Custom exception hierarchy with explicit messages

All domain errors inherit from `AppError`, which stores a `.message`
string alongside the standard exception behavior. Call sites do
`logging.error(er.message)` immediately before raising, so every error is
logged at the point it's detected, not just where it's eventually caught.

### 4.3 Printer abstraction: single-target interface, fan-out via composition

Rather than have every `print_*` function in `output_printing.py` accept
a *list* of printers (which would force every such function to implement
its own fan-out loop), `Printer` stays a single-target interface
(`ConsolePrinter`, `FilePrinter`), and `CompositePrinter` wraps a list of
`Printer`s behind that same interface:

```python
printers: list[Printer] = []
if "console" in args.output:
    printers.append(ConsolePrinter())
if "file" in args.output:
    printers.append(FilePrinter(args.output_file))
printer: Printer = CompositePrinter(printers)
```

Every `print_*` function still just calls `printer.print(...)` once. This
was chosen over the list-based alternative specifically to avoid
duplicating fan-out logic across every printing function — it belongs in
exactly one place (`CompositePrinter.print()`).

### 4.4 Dash axis behavior: `Patch()` vs. full rebuild, and `uirevision`

The chart is either patched in place or fully rebuilt, depending on what
triggered the callback (`ctx.triggered_id`). Three cases:
 
1. **Color change.** `Patch()` updates only the marker color/border,
   leaving the current zoom/pan state untouched.
2. **Pan, zoom, or "Reset axes"** (`relayoutData`). `Patch()` updates
   only the axis or axes reported in that event. Plotly sends only one
   axis bound per relayout event, so two `dcc.Store`s (`x-axis-range`,
   `y-axis-range`) track the last-known full range, letting each new
   event merge with it instead of overwriting the other axis. On a
   reset specifically, `compute_nice_x_axis()` / `compute_nice_y_axis()`
   round the recomputed maximum up to the nearest tick step — and
   because `autorange=True` alone does not trigger Plotly's internal
   recomputation inside a `Patch()`, the reset must set `range`, `dtick`,
   and `autorange=False` together, explicitly.
3. **Bin width slider change, initial load, or curve toggle.** A full
   rebuild via `build_visual_histogram()`, with `uirevision="constant"`.
   A `Patch()` isn't sufficient here because the underlying data itself
   changes — different bin edges, or curves added/removed — not just a
   cosmetic property of the existing figure.

### 4.5 Y-axis must account for both histogram and fit curves

`build_visual_histogram()` computes the y-axis maximum from
`max(histogram.max_percentage, total_curve_maximum)`, not from the
histogram alone. A fitted curve's peak (especially Lorentzian, which has
a sharper peak than Normal for the same data spread) can legitimately
exceed the tallest histogram bar, since **MLE fitting optimizes for overall
shape fit**, not for matching any single bar's height. `build_fit_curve()`
returns both the `Scatter` trace and its own max value
(`tuple[go.Scatter, float]`), following the same pattern
`build_visual_histogram()` itself uses toward its caller (`app.py`) —
returning the figure *and* the values needed outside it, rather than
burying them only inside the figure object.

Curves are built (and their maxima collected) *before*
`compute_nice_y_axis()` is called, since the axis calculation depends on
knowing the tallest curve.

### 4.6 X-axis must use `bin_edges[-1]`, not `max_value`

The x-axis is computed from `histogram.bin_edges[-1]` (the true right
edge of the last bin) rather than `histogram.max_value` (the largest
individual measurement). Bin edges are built via
`np.arange(0.0, max_value + bin_width, bin_width)`, so the last bin can
extend meaningfully past the actual data maximum, especially with a large
bin width. Using `max_value` for the axis caused the last bar to appear
visually clipped, and — since `max_value` never changes with bin width —
made the x-axis appear "stuck" regardless of the bin width slider.
Fit curves are then drawn out to this same rounded `x_max`, so they don't
visually stop short of the last bar.


---

## 5. Coding conventions

- Type annotations on all variables, in the form `name :type = value`
  (colon directly after the name, no space before it, one space after).
- Two blank lines between top-level definitions.
- `float(...)` / `cast(float, ...)` wrappers on NumPy/SciPy return values
  at module boundaries, so downstream code deals with plain Python types.
- Named constants are introduced only when a value repeats or carries
  derived logic — not applied universally to every literal.
- Filename-formatting logic and printed-text-formatting logic are kept as
  separate, parallel `if`/`else` branches rather than unified into one
  shared helper, since they're considered distinct concerns despite
  surface-level similarity.

---

## 6. Areas for future work

- The `Y_AXIS_HARD_MAX` cap (previously applied only in the zoom/pan
  relayout branch) was removed as not applicable to curve-inclusive axis
  scaling; consider whether any upper bound is still desirable for
  extreme fit shapes.
- No automated tests currently exist; correctness has so far been
  verified through manual testing against purpose-built sample data
  files.

---

## 7. Dash callback reference

`app.py` wires up six callbacks. This is the quick map of what triggers
each one and what it's responsible for — useful before adding a seventh:

| Callback | Input(s) | Output(s) | Responsibility |
|---|---|---|---|
| `update_histogram` | `bin-width-slider.value`, `color-picker.data`, `histogram.relayoutData`, `active-curves.data` | `histogram.figure`, `x-axis-range.data`, `y-axis-range.data`, `histogram-stats.data`, `histogram-id.data` | The main chart callback — branches on `ctx.triggered_id` into color patch / pan-zoom-reset patch / full rebuild (see §4.4) |
| `highlight_selected_color` | `color-picker.data` | `color-grid.children` | Redraws the swatch grid so the current color shows a thicker outline |
| `select_color` | `{type: color-swatch}.n_clicks` (pattern-matching) | `color-picker.data` | Sets the selected color to whichever swatch was clicked |
| `toggle_color_panel` | `change-color-button.n_clicks` | `color-panel.style` | Shows/hides the popover color grid, alternating on click count |
| `save_histogram_png` | `save-button.n_clicks` | `save-button.n_clicks` (self, to satisfy Dash's one-output-per-callback-input rule) | Exports the current figure to PNG via Kaleido |
| `print_histogram_data` | `print-info-button.n_clicks` | `print-info-button.n_clicks` (same self-output pattern) | Recomputes the histogram at the current bin width and prints its summary |
| `toggle_curve` | `{type: curve-toggle}.n_clicks` (pattern-matching) | `active-curves.data` | Adds/removes the clicked curve's key from the active list |
| `highlight_active_curves` | `active-curves.data` | `curve-toggle-panel.children` | Redraws the curve-toggle buttons so active ones are colored |

**Why pattern-matching at all:** `select_color` and `toggle_curve` react
to clicks on buttons generated dynamically (per color in
`HISTOGRAM_COLORS`, per fit in `fits`) — the exact IDs aren't known
ahead of time, and a normal `Input("some-id", ...)` needs one fixed ID
written directly in the callback. A structured ID like
`{"type": "color-swatch", "index": i}` lets the callback instead declare
`Input({"type": "color-swatch", "index": ALL}, "n_clicks")` — "catch a
click on any button of this type, however many exist."
 
Pattern-matching callbacks (`select_color`, `toggle_curve`) both guard
against spurious triggers on button regeneration with
`if not any(_n_clicks): raise PreventUpdate` — without this, redrawing
the button list (which happens on every color/curve change) would
re-trigger the very callback that caused the redraw.

---

## 8. Testing strategy

There is no automated test suite. Correctness has been verified manually
throughout development, primarily by:

- Running the full pipeline against a small set of purpose-built CSV/XLSX
  files covering the edge cases the exception hierarchy is meant to
  catch (missing column, non-numeric values, empty file, wrong file
  type, unreadable/locked file).
- Visually inspecting the interactive chart after each change to axis or
  curve logic (bin-width changes, curve toggles, pan/zoom/reset) against
  the expected behavior described in §4.4–4.6.
- Cross-checking statistical outputs (moments, fit parameters, KS
  results) against values computed independently for a known sample.

If automated tests are added later, the layer separation in §2 makes the
computation modules (`histogram.py`, `fitting.py`, `moments.py`,
`ks_test.py`, `statistics_helpers.py`) the natural place to start — they
take plain NumPy arrays and return dataclasses, with no Dash or I/O
dependency to mock.