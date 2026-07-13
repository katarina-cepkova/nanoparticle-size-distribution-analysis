# Nanoparticle Size Distribution Analysis Tool

A console-launched, browser-displayed application for analyzing nanoparticle
size measurements (from microscopy images) exported as CSV or Excel files.
It computes descriptive statistics, fits three theoretical size
distributions (Normal, Lognormal, Lorentzian), tests how well each fits the
data, and displays an interactive histogram with overlaid fit curves.

## Documentation

This documentation is split into two guides, depending on who you are:

- **[USER DOCUMENTATION](documentation/USER_DOC.md)** — for someone who wants to *run* the
  program and analyze their own data, with no assumed programming or
  command-line experience. Covers setup, configuration, and day-to-day use.

- **[DEVELOPER DOCUMENTATION](documentation/DEV_DOC.md)** — for someone who wants to
  *read, modify, or extend* the code. Covers architecture, module
  responsibilities, technologies used, and the reasoning behind key design
  decisions made during development.

Start with the User Guide to run the program and analyze data. Go to the
Developer Guide to work on the code itself.