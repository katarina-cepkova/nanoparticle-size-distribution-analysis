# Nanoparticle Size Distribution Analysis Tool

A console-launched, browser-displayed application for analyzing nanoparticle
size measurements (from microscopy images) exported as CSV or Excel files.
It computes descriptive statistics, fits three theoretical size
distributions (Normal, Lognormal, Lorentzian), tests how well each fits the
data, and displays an interactive histogram with overlaid fit curves.

This project was built for a chemistry student who runs this kind of statistical analysis as part of their lab work with **nanoparticles**,
working around a manual CSV → Excel → OriginPro workflow. The
requirements and design decisions throughout this documentation come
from iterating directly with them as the intended user — understanding
what their existing workflow actually needed to support, rather than
designing in isolation.

Statistics is the core of this project, not just a supporting feature.
For a given batch of measurements, the tool answers three connected
questions: 
- what does the data look like on its own terms (descriptive
moments — mean, variance, skewness, and particle-science-specific
measures like the polydispersity index and Sauter mean diameter); 
- which
theoretical distribution — Normal, Lognormal, or Lorentzian — best explains that shape, fitted via **Maximum Likelihood Estimation** (MLE); 
- whether that fitted distribution is actually a statistically defensible
description of the data, checked with a **Kolmogorov–Smirnov test** rather
than left to visual judgment. The interactive chart and PNG export exist
to make that analysis easier to work with, not to replace it.

## Documentation

This documentation is split into three guides:

- **[USER DOCUMENTATION](documentation/USER_DOC.md)** — run the program
  and analyze your own data. No programming or command-line experience
  assumed. Covers setup, configuration, and day-to-day use.

- **[DEVELOPER DOCUMENTATION](documentation/DEV_DOC.md)** — read, modify,
  or extend the code. Covers architecture, module responsibilities,
  technologies used, and the reasoning behind key design decisions.

- **[STATISTICS](documentation/STATISTICS.md)** — understand the statistics on its
  own terms, independent of the code: why these distributions and tests
  were chosen, the exact formulas being computed, and no programming or
  advanced math background required to follow it.