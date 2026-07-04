from dataclasses import dataclass
import numpy as np
from scipy import stats, optimize
from typing import cast
import logging
from domain_errors import InvalidInputError

@dataclass
class FitResult:
    distribution: str
    params: dict[str, float]
    log_likelihood: float
    theoretical_mode: float
    theoretical_median: float
    fwhm: float
    rel_fwhm: float
    loc: float
    scale: float


def fit_lognormal(data: np.ndarray) -> FitResult:
    """Fit a log-normal distribution to data via MLE and return the result."""
    # floc=0: no location shift — log-normal requires strictly positive values
    sigma_hat, _, scale = stats.lognorm.fit(data, floc=0)
    # scipy encodes mu as log(scale), so recover it here
    mu_hat :float = float(np.log(scale))  # mu: mean of ln(X), i.e. the centre on the log scale

    # sigma_hat: std dev of ln(X), i.e. how spread out the log values are
    # scale = exp(mu_hat): median of X on the original scale
    log_likelihood :float = float(np.sum(stats.lognorm.logpdf(data, sigma_hat, loc=0, scale=scale)))
    mode :float = float(np.exp(mu_hat - sigma_hat**2))  # mode of log-normal: exp(mu - sigma^2)
    
    if mode == 0:
        er = InvalidInputError("Mode of the fitted normal distribution is zero, cannot compute relative FWHM.")
        logging.error(er.message)
        raise er
    
    theoretical_median = float(stats.lognorm.median(sigma_hat, loc=0, scale=scale))

    peak_height = stats.lognorm.pdf(mode, sigma_hat, loc=0, scale=scale)
    half_max = peak_height / 2

    def shifted_pdf(x):
        return stats.lognorm.pdf(x, sigma_hat, loc=0, scale=scale) - half_max

    # brentq - without fulll_output = True - it returns only the root
    # left root: search between a tiny positive number and the mode
    x_left :float = cast(float, optimize.brentq(shifted_pdf, 1e-10, mode))
    # right root: search between the mode and a point far enough right
    x_right :float = cast(float, optimize.brentq(shifted_pdf, mode, mode + 10 * scale))

    fwhm :float = x_right - x_left
    rel_fwhm :float = fwhm / mode
    d32 :float = float(np.sum(data**3) / np.sum(data**2))

    return FitResult(
        distribution="lognormal",
        params={"mu": mu_hat, "sigma": float(sigma_hat)},
        log_likelihood=log_likelihood,
        theoretical_mode=mode,
        theoretical_median=theoretical_median,
        fwhm=fwhm,
        rel_fwhm=rel_fwhm,
        loc=0.0,
        scale=scale
    )


def fit_normal(data: np.ndarray) -> FitResult:
    """Fit a normal distribution to data via MLE and return the result."""
    mu_hat, sigma_hat = stats.norm.fit(data)  # mu: mean (centre), sigma: std dev (spread)

    # loc=mu_hat: shifts the bell curve to the estimated mean
    # scale=sigma_hat: sets the width (larger → flatter curve)
    log_likelihood :float = float(np.sum(stats.norm.logpdf(data, loc=mu_hat, scale=sigma_hat)))
    
    mode :float = float(mu_hat)  # mode of normal distribution is the mean

    if mode == 0:
        er = InvalidInputError("Mode of the fitted normal distribution is zero, cannot compute relative FWHM.")
        logging.error(er.message)
        raise er
    theoretical_median = float(stats.norm.median(loc=mu_hat, scale=sigma_hat))

    fwhm :float = float(2 * np.sqrt(2 * np.log(2)) * sigma_hat)  # FWHM = 2*sqrt(2*ln(2))*sigma
    rel_fwhm :float = fwhm / mode
    d32 :float = float(np.sum(data**3) / np.sum(data**2))

    return FitResult(
        distribution="normal",
        params={"mu": float(mu_hat), "sigma": float(sigma_hat)},
        log_likelihood=log_likelihood,
        theoretical_mode=mode,
        theoretical_median=theoretical_median,
        fwhm=fwhm,
        rel_fwhm=rel_fwhm,
        loc=float(mu_hat),
        scale=float(sigma_hat)
    )


def fit_lorentzian(data: np.ndarray) -> FitResult:
    """Fit a Lorentzian (Cauchy) distribution to data via MLE and return the result."""
    x0_hat, gamma_hat = stats.cauchy.fit(data)  # x0: peak position, gamma: half-width at half-maximum

    # loc=x0_hat: centre of the peak
    # scale=gamma_hat: half-width at half-maximum — larger → broader, heavier tails than normal
    log_likelihood: float = float(np.sum(stats.cauchy.logpdf(data, loc=x0_hat, scale=gamma_hat)))
    
    mode: float = float(x0_hat)  # mode of Cauchy distribution is the peak position

    if mode == 0:
        er = InvalidInputError("Mode of the fitted normal distribution is zero, cannot compute relative FWHM.")
        logging.error(er.message)
        raise er
    
    theoretical_median = float(stats.cauchy.median(loc=x0_hat, scale=gamma_hat))
    
    fwhm: float = float(2 * gamma_hat)
    rel_fwhm : float = fwhm / mode

    return FitResult(
        distribution="lorentzian",
        params={"x0": float(x0_hat), "gamma": float(gamma_hat)},
        log_likelihood=log_likelihood,
        theoretical_mode=mode,
        theoretical_median=theoretical_median,
        fwhm=fwhm,
        rel_fwhm=rel_fwhm,
        loc=float(x0_hat),
        scale=float(gamma_hat)
    )



 