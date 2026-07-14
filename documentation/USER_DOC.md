# User Guide

This guide walks you through running the **Nanoparticle Size Distribution
Analysis Tool**, from opening a console for the first time to reading your
results. No prior programming experience is assumed.

See also: **[README](../README.md)** · **[DEVELOPER DOCUMENTATION](DEV_DOC.md)** · **[STATISTICS](STATISTICS.md)**

---

## 1. What this program does

You give it a folder of CSV or Excel files, each containing a column of
particle size measurements (in nanometers). It will:

- Compute basic statistics (mean, median, variance, skewness, etc.)
- Fit three theoretical distributions to your data (Normal, Lognormal,
  Lorentzian) and test how well each one fits
- Open an interactive chart in your web browser, where you can adjust bin
  width, toggle fit curves on and off, change colors, and export the chart
  as a PNG image
- Print a full text report to the console and/or a file

---

## 2. Opening a console (terminal)

The program is run from a **console** (also called a terminal or command
line) — a text-based window where you type commands instead of clicking
icons.

- **Windows**: Press the Start menu, type `PowerShell`, and press Enter.
- **macOS**: Open **Terminal** (find it via Spotlight search — press
  `Cmd + Space`, type `Terminal`, press Enter).
- **Linux**: Open your distribution's terminal application (commonly
  `Ctrl + Alt + T`).

A window with a blinking cursor will appear. This is where you'll type
every command in this guide.

---

## 3. Navigating to the project folder

Use the `cd` (change directory) command, followed by the path to the
project folder. For example, if the project is on your Desktop:

```
cd Desktop/nanoparticle-tool
```

**Tip:** you can type `cd ` (with a trailing space) and then drag the
project folder from your file explorer directly into the console window —
most consoles will automatically fill in the correct path for you.

---

## 4. Checking that Python is installed

Type:

```
python --version
```

You should see something like `Python 3.11.4`. Any version 3.10 or higher
is fine.
 
Which command to use depends on your operating system: 
- **Windows**
installations of Python normally register the `python` command.
- **macOS** and **Linux** often keep `python` reserved for an older
system-level Python (or don't define it at all) and instead register the
newer, project-relevant version as `python3`. So if you're on macOS or
Linux and `python --version` doesn't work as expected, try:
 
  ```
  python3 --version
  ```
 
If neither command works, Python is not installed on your computer, and
you'll need to install it before continuing (search "install Python" for
your operating system). Whichever command worked (`python` or `python3`),
use that same one everywhere else in this guide.
 

---

## 5. Activating the virtual environment

This project comes with a `.venv` folder — a self-contained Python
environment that keeps this project's dependencies separate from anything
else on your computer. Activate it before running anything:

- **Windows (PowerShell)**:
  ```
  .venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```
  source .venv/bin/activate
  ```

You'll know it worked when you see `(.venv)` appear at the start of your
console prompt.

**You must re-run this activation command every time you open a new
console window**, before running the program.

---

## 6. Installing dependencies

With the virtual environment active, install the required packages
(only needs to be done once, or after the project's requirements change):

```
pip install -r requirements.txt
```

---

## 7. Setting up your configuration file

The project ships with a template file named **`.env.example`**. You need
to make your own copy named exactly **`.env`** (no `.example` at the end):

- **Windows (PowerShell)**:
  ```
  copy .env.example .env
  ```
- **macOS / Linux**:
  ```
  cp .env.example .env
  ```

Alternatively, you can do this in your file explorer: duplicate
`.env.example` and rename the copy to `.env`.

The `.env` file is where all the program's settings live. Open it in any
text editor (Notepad, TextEdit, VS Code, etc.) to change values. You do
not need to change anything to get started — the defaults work out of the
box — but here's what each setting controls, if you want to customize it:

| Setting | Default | What it controls |
|---|---|---|
| `SEPARATOR` | `---` | When entering data by typing into the console (see `--source console` below), the line you type to mark the end of one file/image's measurements and the start of the next. |
| `END_OF_INPUT` | `END` | When entering data by typing, the line you type to signal you're done entering all data. |
| `INPUT_DATA_PATH` | `data/input_data` | The folder the program scans for your CSV/Excel files (used with `--source file`, see below). |
| `CSV_COLUMN_NAME` | `Length` | The column header in your CSV files that contains the particle size measurements. Change this if your CSV uses a different column name. |
| `XLSX_COLUMN_INDEX` | `-1` | Which column in your Excel files holds the measurements, counted from the left starting at 0. `-1` means "the last column." |
| `OUTPUT_DATA_PATH` | `data/output_data` | Where the text report is saved (when writing to a file — see `--output` below). |
| `OUTPUT_GRAPH_PATH` | `data/output_data/graphs` | Where exported PNG chart images are saved. |
| `OUTPUT_GRAPH_NAME_PREFIX` | `histogram` | The prefix used in exported PNG filenames. |
| `PNG_EXPORT_WIDTH_IN_PIXELS` | `1600` | Width of exported PNG chart images. |
| `PNG_EXPORT_HEIGHT_IN_PIXELS` | `900` | Height of exported PNG chart images. |
| `PNG_EXPORT_SCALE` | `2` | A multiplier applied to the PNG's resolution (2 = double-resolution, sharper image). |
| `LOG_DIR` | `logs` | Where the technical log file (`app.log`) is written. This is a diagnostic log for troubleshooting, separate from your statistical report. |
| `DECIMAL_PLACES` | `6` | How many decimal places are shown for most numeric values in the printed report. |
| `PERCENTAGE_DECIMAL_PLACES` | `2` | How many decimal places are shown for percentage values in the printed report. |
| `ALPHA` | `0.05` | The significance level used in the Kolmogorov–Smirnov goodness-of-fit test (standard statistical convention; leave as-is unless you have a specific reason to change it). |
| `BIN_WIDTH` | `0.25` | The starting bin width (in nanometers) for the histogram when the interactive chart first opens. You can still adjust this with the slider afterward. |

---

## 8. Preparing your data

By default, the program looks inside the `data/input_data` folder
(configurable via `INPUT_DATA_PATH`, see above). Place your CSV and/or
Excel files there — you can organize them into one subfolder per dataset
if you like (the subfolder name will then be used to label your reports
and charts).

- **CSV files** need a column named `Length` (or whatever you set
  `CSV_COLUMN_NAME` to) containing the size measurements.
- **Excel files** must **not** have a header row — the measurements need
  to start on the very first row. The program reads by column position,
  not by column name — by default the last column
  (`XLSX_COLUMN_INDEX = -1`).

---

## 9. Running the program

With your console open, the virtual environment activated, and your
`.env` file and data in place, run:

```
python main.py
```

This uses all the defaults: reads data from your input folder, prints the
report to both the console and a file, and opens the interactive chart in
your browser.

### Optional command-line switches

You can customize how it runs by adding switches after `python main.py`:

| Switch | Options | Default | Meaning |
|---|---|---|---|
| `--source` | `console`, `file` | `file` | Where particle measurements come from: `file` reads your CSV/Excel files; `console` lets you type measurements in directly. |
| `--output` | `console`, `file` (one or both, space-separated) | `console file` | Where the printed report goes. |
| `--output-file` | any file path | auto-generated name in your output folder | Custom name/location for the report file (only relevant if `file` is included in `--output`). |

**Examples:**

Only print the report to the console, skip the file:
```
python main.py --output console
```

Type measurements in by hand instead of reading files:
```
python main.py --source console
```
When typing measurements this way, you can use either `.` or `,` as the
decimal separator (e.g. `12.5` or `12,5` both work). This only applies to
typed console input — when you later type an exact number directly into
the chart's axis (see §10), only the `.` format is accepted, since that's
a browser input field, not this program's own console parsing.


Save the report to a specific file:
```
python main.py --output-file my_results.txt
```

---

## 10. Using the interactive chart

Once the program runs, it prints a local web address (something like
`Dash is running on http://127.0.0.1:8050/`). It does **not** open
automatically — you need to open it yourself:
 
- In most consoles/terminals, hold **Ctrl** (or **Cmd** on macOS) and
  click the printed address directly.
- If you're running the program from inside **VS Code**, its integrated
  terminal recognizes the address as a link too — Ctrl/Cmd-click it the
  same way.
- Otherwise, just copy the address and paste it into any browser's
  address bar.

From there you can:

- Drag the **bin width slider** to change how the data is grouped
- Toggle the **Normal / Lognormal / Lorentzian** buttons on the right to
  show or hide each fitted curve
- Click **Change color** to pick a different bar color
- Click **Save PNG** to export the current chart as an image
- Click **Print Histogram Info** to print a summary of the current view
  to your chosen output (console/file)
- Zoom, pan, and use the **Reset axes** control on the chart itself. To
  change just one axis's range, move your cursor to the very edge of
  that axis (the numbers along the bottom or the left side) until the
  cursor changes into a double-headed arrow (`↔` for the x-axis, `↕` for
  the y-axis) — then click and drag to stretch or shrink that axis, or click once and type an exact number directly. 

---

## 11. Stopping the program

The program keeps running (and the browser chart stays interactive) until
you stop it. Go back to your console window and press:

```
Ctrl + C
```

This is the standard way to stop any locally running web application —
it's not a workaround, it's the expected way to shut it down.

---

## 12. If something goes wrong

The program is designed to tell you clearly what happened rather than
crash silently. Here are the messages you might see, grouped by cause:
 
**Problems with your input files:**
 
- **"Missing column '...' in '...'"** — your CSV/Excel file doesn't have
  the expected column. Check `CSV_COLUMN_NAME` / `XLSX_COLUMN_INDEX` in
  your `.env` file against your actual file.
- **"The input file '...' has an invalid format."** — the file couldn't
  be parsed as a valid CSV or Excel file (e.g. it's corrupted, or it's
  actually a different file type saved with the wrong extension), or a
  column that should contain numbers has non-numeric values in it.
- **"The input file '...' has an unsupported file type."** — the file's
  extension isn't `.csv`, `.xlsx`, or `.xls`.
- **"No valid measurements found in '...'."** — a specific file was read
  successfully but contained no usable data; it's skipped rather than
  stopping the whole run.
- **"... file(s) could not be loaded and were skipped: ..."** — a
  summary listing every file from the batch above that had a problem;
  fix or remove the named files and rerun.
- **"No valid particle size measurements were found in the provided
  files."** — none of your files contained usable data at all;
  double-check the input folder and column settings.
- **File not found / permission errors** — the program couldn't open a
  file at all, e.g. it's been deleted, moved, or is currently open in
  another program (common with Excel files open in Microsoft Excel —
  close the file and try again).

**Problems with the data itself (even if the files loaded fine):**
 
- **"Bin width must be positive, got '...'."** — only relevant if you're
  changing bin width via configuration or code; the slider in the chart
  itself won't let you pick an invalid value.
- **"Mode of the fitted normal distribution is zero, cannot compute
  relative FWHM."** — a distribution fit produced a peak position of
  exactly zero, which the width calculations can't handle. This usually
  points to unusual data (e.g. all measurements clustered right at zero)
  rather than a bug to fix on your end.
- **"Mean is zero, cannot compute coefficient of variation."** — similar
  to the above; a statistic that requires dividing by the mean can't be
  computed if the mean is exactly zero.
**Generic errors:**
 
- **"Error: ..."** printed just before the program exits — this is the
  catch-all message for any of the above; the text after "Error:" always
  names the specific problem, so start there.

If you're stuck, check the detailed log file in your `logs` folder
(`app.log`) — it contains more technical detail than the console output.