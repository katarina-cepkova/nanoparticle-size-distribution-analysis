from dataclasses import dataclass
import numpy as np
from scipy import stats
from statistics_helpers import compute_cv, compute_PDI

@dataclass
class MomentsResult:
    mean: float       # μ (mu) - arithmetic mean of the data
    variance: float   # σ² - variance, measure of spread around the mean
    std: float        # σ (sigma) - standard deviation, sqrt(variance)
    skewness: float   # skewness - measure of distribution asymmetry (0 = symmetric)
    cv: float | None  # coefficient of variation - relative variability (std/mean); None only if mean is undefined for this data
    median: float     # median - middle value of sorted data (robust to outliers)
    PDI: float | None # polydispersity index - measure of size distribution width/uniformity; None only if PDI is undefined for this data
    D32: float        # Sauter mean diameter - sum(d^3) / sum(d^2), surface-area-weighted mean size


def compute_moments(data: np.ndarray) -> MomentsResult:
    """Compute descriptive statistical moments and related dispersion measures for the data."""
    mean : float = float(np.mean(data))                     # μ

    # ddof=1: gives an unbiased estimate of variance (divide MLE by n-1 instead of n)
    variance: float = float(np.var(data, ddof=1))           # σ²
    std: float = float(np.std(data, ddof=1))                # σ

    # bias=False: same correction as ddof=1, applied to skewness estimation
    # positive = right-skewed, negative = left-skewed
    skewness : float = float(stats.skew(data, bias=False))
             
    cv: float | None = compute_cv(std, mean)
    median : float = float(np.median(data))

    # PDI = (σ/μ)² = cv² - expresses how "polydisperse" (wide/non-uniform) the
    # size distribution is vs. "monodisperse" (narrow, similar particle sizes)
    PDI: float | None = compute_PDI(cv)

    # D32 (Sauter mean diameter) = sum(d^3) / sum(d^2) - weights larger particles
    # more heavily than the arithmetic mean; common in particle-size analysis
    # since it reflects surface-area-to-volume ratio, not just count
    D32 : float = float(np.sum(data**3) / np.sum(data**2))

    return MomentsResult(mean, variance, std, skewness, cv, median, PDI, D32)