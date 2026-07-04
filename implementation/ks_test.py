from scipy import stats
import numpy as np
from dataclasses import dataclass
from fitting import FitResult

@dataclass
class KSTestResult:
    statistic: float
    p_value: float


def ks_test_normal(data: np.ndarray, mu: float, sigma: float) -> KSTestResult:
    """
    Kolmogorov-Smirnov test against a fitted normal distribution.
    Returns (statistic, p_value).
    """
    # lambda instead of args=(mu, sigma): passing them via kstest's args
    # mechanism misforwards params down to ndtr(), which raises a TypeError
    # on this scipy version. The lambda evaluates the CDF ourselves instead.
    # scipy's norm CDF takes (loc=mu, scale=sigma)
    statistic, p_value = stats.kstest(data, lambda x: stats.norm.cdf(x, loc=mu, scale=sigma))
    test_result = KSTestResult(statistic=float(statistic), p_value=float(p_value))
    return test_result


def ks_test_lognormal(data: np.ndarray, mu: float, sigma: float) -> KSTestResult:
    """
    Kolmogorov-Smirnov test against a fitted log-normal distribution.
    Returns (statistic, p_value).
    """
    scale = np.exp(mu)
    # lambda used for the same reason as in ks_test_normal (see above)
    # scipy's lognorm CDF takes (s=sigma, loc=0, scale=exp(mu))
    statistic, p_value = stats.kstest(data, lambda x: stats.lognorm.cdf(x, s=sigma, loc=0, scale=scale))
    test_result = KSTestResult(statistic=float(statistic), p_value=float(p_value))
    return test_result


def ks_test_lorentzian(data: np.ndarray, x0: float, gamma: float) -> KSTestResult:
    """
    Kolmogorov-Smirnov test against a fitted Lorentzian (Cauchy) distribution.
    Returns (statistic, p_value).
    """
    # lambda used for the same reason as in ks_test_normal (see above)
    # scipy's cauchy CDF takes (loc=x0, scale=gamma)
    statistic, p_value = stats.kstest(data, lambda x: stats.cauchy.cdf(x, x0, gamma))
    test_result = KSTestResult(statistic=float(statistic), p_value=float(p_value))
    return test_result


def compute_ks_test(data: np.ndarray, fit: FitResult) -> KSTestResult:
    """Runs the Kolmogorov-Smirnov test for a single fit against its distribution."""
    if fit.distribution == "normal":
        return ks_test_normal(data, fit.params["mu"], fit.params["sigma"])
    elif fit.distribution == "lognormal":
        return ks_test_lognormal(data, fit.params["mu"], fit.params["sigma"])
    else:  # fit.distribution == "lorentzian"
        return ks_test_lorentzian(data, fit.params["x0"], fit.params["gamma"])