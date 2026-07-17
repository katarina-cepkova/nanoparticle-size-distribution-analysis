# Quick Reference Cheatsheet


Every command from the User Documentation, in one place — no explanations,
just the commands. See **[USER DOCUMENTATION](USER_DOC.md)**
if you need the full walkthrough or a refresher on what any of this does.

See also: **[README](../README.md)** · **[DEVELOPER DOCUMENTATION](DEV_DOC.md)** · **[STATISTICS](STATISTICS.md)**

---

## Setup (once per machine)

```bash
# create the virtual environment (once)
python -m venv .venv

# activate the virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# install dependencies
pip install -r requirements.txt

# create your config file (once)
copy .env.example .env          # Windows
cp .env.example .env            # macOS / Linux
```

## Every time you open a new console

```bash
.venv\Scripts\activate           # Windows
source .venv/bin/activate        # macOS / Linux
```

## Running the program

```bash
python main.py
```

| Flag | Options | Default | Effect |
|---|---|---|---|
| `--source` | `console`, `file` | `file` | Where measurements come from |
| `--output` | `console`, `file` (one or both) | `console file` | Where the report is written |
| `--output-txt-file` | any path | auto-generated | Custom path for the `.txt` report (needs `file` in `--output` and `txt` in `--format`) |
| `--output-csv-file` | any path | auto-generated | Custom path for the `.csv` report (needs `file` in `--output` and `csv` in `--format`) |
| `--format` | `txt`, `csv` (one or both) | `txt` | Which file format(s) to write, when `file` is included in `--output` |

```bash
# common examples
python main.py --output console                        # skip the report file entirely
python main.py --source console                          # type measurements in by hand
python main.py --format csv                               # only write the CSV report, not txt
python main.py --format txt csv                           # write both txt and csv reports
python main.py --output-csv-file my_results.csv           # custom CSV report filename
python main.py --source console --output file             # type data in, only save to file
```

## Checking Python is installed

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

## Stopping the program

```
Ctrl + C
```
(run in the console window, once you're done with the chart)

## Opening the chart

The printed local address does **not** open automatically:

- **Ctrl/Cmd + click** the printed address in the console (or in VS
  Code's integrated terminal), **or**
- copy it and paste it into a browser's address bar

## Console data entry (`--source console`)

- Decimal separator: `.` or `,` both work (`12.5` or `12,5`)
- Line to separate measurement groups: value of `SEPARATOR` in `.env`
  (default `---`)
- Line to finish entry: value of `END_OF_INPUT` in `.env` (default `END`)

## Chart interactions

| Action | How |
|---|---|
| Change bin width | Drag the slider |
| Show/hide a fit curve | Click its toggle button |
| Change bar color | **Change color** → pick a swatch |
| Export current chart | **Save PNG** |
| Print current view's summary | **Print Histogram Info** — writes to console (or nothing, per `--output`) plus `.txt`/`.csv` per `--format`, into `data/output_data/txt_histograms/` and `data/output_data/csv_histograms/` |
| Zoom/pan one axis | Hover the axis edge until the cursor becomes `↔`/`↕`, then drag — or click once and type an exact number |
| Reset zoom/pan | **Reset axes** control on the chart |