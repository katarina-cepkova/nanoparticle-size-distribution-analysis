from scipy import stats
import numpy as np
from dataclasses import dataclass
from fitting import FitResult
from typing import Callable, cast

N_BOOTSTRAP_SAMPLES :int = 1000  # tradeoff: higher = more precise p-value estimate, 
                                 # but linearly slower (this many extra fit+test cycles per distribution)

@dataclass
class KSTestResult:
    """Result of a KS goodness-of-fit test. Use corrected_p_value for the
    accept/reject decision — p_value is systematically biased because the
    fitted distribution's parameters come from the same data being tested."""
    statistic :float
    p_value :float             # naive p-value — kept for transparency, biased (see STATISTICS.md)
    corrected_p_value :float   # bootstrap-corrected, accounts for params fit from the same data


def _calibrate_pvalue(
        observed_statistic: float,
        n: int,
        generate_sample: Callable[[int], np.ndarray],
        refit_and_test: Callable[[np.ndarray], float],
        n_bootstrap: int = N_BOOTSTRAP_SAMPLES,
    ) -> float: 
    """Runs the fit+test procedure on n_bootstrap synthetic samples drawn from the
    fitted distribution, and returns the fraction whose KS statistic is at least
    as large as the one observed on the real data — the bootstrap-corrected p-value.

    This exists because the naive p-value from stats.kstest() is biased: the
    distribution's parameters were fit from the same data being tested, so the
    classic KS reference distribution (which assumes independent parameters)
    doesn't apply. See STATISTICS.md for the full explanation.

    generate_sample(n): draws one synthetic sample of size n from the fitted
    distribution — the "if this fit were exactly right" reference data.
    refit_and_test(sample): re-fits the distribution on that synthetic sample
    and returns the resulting KS statistic, i.e. one full repetition of the
    same fit+test procedure used on the real data, run on data known to
    actually come from the fitted curve."""
    exceed_count :int = 0

    for _ in range(n_bootstrap):
        synthetic :np.ndarray = generate_sample(n)
        synthetic_statistic :float = refit_and_test(synthetic)
        if synthetic_statistic >= observed_statistic:
            exceed_count += 1

    return exceed_count / n_bootstrap


def ks_test_normal(data: np.ndarray, mu: float, sigma: float) -> KSTestResult:
    """Kolmogorov-Smirnov test against a fitted Normal distribution, with a bootstrap-corrected p-value."""
    # lambda instead of args=(mu, sigma): passing them via kstest's args
    # mechanism misforwards params down to ndtr(), which raises a TypeError
    # on this scipy version. The lambda evaluates the CDF ourselves instead.
    # scipy's norm CDF takes (loc=mu, scale=sigma)
    statistic, naive_p_value = stats.kstest(data, lambda x: stats.norm.cdf(x, loc=mu, scale=sigma))

    def refit_and_test(synthetic: np.ndarray) -> float:
        # synth_ prefix: these are refit on the synthetic sample
        synth_mu, synth_sigma = stats.norm.fit(synthetic)
        synth_statistic, _ = stats.kstest(synthetic, lambda x: stats.norm.cdf(x, loc=synth_mu, scale=synth_sigma))
        return float(synth_statistic)

    corrected_p_value :float = _calibrate_pvalue(
        observed_statistic=float(statistic),
        n=len(data),
        # cast: scipy's .rvs() isn't fully typed, so Pylance can't infer it returns
        # an ndarray here — same cast used in fitting.py for the same reason.
        generate_sample=lambda n: cast(np.ndarray, stats.norm.rvs(loc=mu, scale=sigma, size=n)),
        refit_and_test=refit_and_test,
    )
    test_result :KSTestResult = KSTestResult(
        statistic=float(statistic), 
        p_value=float(naive_p_value), 
        corrected_p_value=corrected_p_value)
    return test_result


def ks_test_lognormal(data: np.ndarray, mu: float, sigma: float) -> KSTestResult:
    """Kolmogorov-Smirnov test against a fitted Lognormal distribution, with a bootstrap-corrected p-value."""
    scale :float = np.exp(mu)
    # lambda used for the same reason as in ks_test_normal (see above)
    # scipy's lognorm CDF takes (s=sigma, loc=0, scale=exp(mu))
    statistic, naive_p_value = stats.kstest(data, lambda x: stats.lognorm.cdf(x, s=sigma, loc=0, scale=scale))

    def refit_and_test(synthetic: np.ndarray) -> float:
        # synth_ prefix: these are refit on the synthetic sample
        synth_sigma, _, synth_scale = stats.lognorm.fit(synthetic, floc=0)
        synth_statistic, _ = stats.kstest(synthetic, lambda x: stats.lognorm.cdf(x, s=synth_sigma, loc=0, scale=synth_scale))
        return float(synth_statistic)

    corrected_p_value :float = _calibrate_pvalue(
        observed_statistic=float(statistic),
        n=len(data),
        # cast used for the same reason as in ks_test_normal (see above)
        generate_sample=lambda n: cast(np.ndarray, stats.lognorm.rvs(sigma, loc=0, scale=scale, size=n)),
        refit_and_test=refit_and_test,
    )
    test_result :KSTestResult = KSTestResult(
        statistic=float(statistic), 
        p_value=float(naive_p_value), 
        corrected_p_value=corrected_p_value
    )
    return test_result


def ks_test_lorentzian(data: np.ndarray, x0: float, gamma: float) -> KSTestResult:
    """Kolmogorov-Smirnov test against a fitted Lorentzian (Cauchy) distribution, with a bootstrap-corrected p-value."""
    # lambda used for the same reason as in ks_test_normal (see above)
    # scipy's cauchy CDF takes (loc=x0, scale=gamma)
    statistic, naive_p_value = stats.kstest(data, lambda x: stats.cauchy.cdf(x, x0, gamma))

    def refit_and_test(synthetic: np.ndarray) -> float:
        # synth_ prefix: these are refit on the synthetic sample
        synth_x0, synth_gamma = stats.cauchy.fit(synthetic)
        synth_statistic, _ = stats.kstest(synthetic, lambda x: stats.cauchy.cdf(x, synth_x0, synth_gamma))
        return float(synth_statistic)

    corrected_p_value :float = _calibrate_pvalue(
        observed_statistic=float(statistic),
        n=len(data),
        # cast used for the same reason as in ks_test_normal (see above)
        generate_sample=lambda n: cast(np.ndarray, stats.cauchy.rvs(loc=x0, scale=gamma, size=n)),
        refit_and_test=refit_and_test,
    )
    test_result :KSTestResult = KSTestResult(
        statistic=float(statistic), 
        p_value=float(naive_p_value), 
        corrected_p_value=corrected_p_value
    )

    return test_result


def compute_ks_test(data: np.ndarray, fit: FitResult) -> KSTestResult:
    """Runs the Kolmogorov-Smirnov test for a single fit against its distribution."""
    if fit.distribution == "normal":
        return ks_test_normal(data, fit.params["mu"], fit.params["sigma"])
    elif fit.distribution == "lognormal":
        return ks_test_lognormal(data, fit.params["mu"], fit.params["sigma"])
    else:  # fit.distribution == "lorentzian"
        return ks_test_lorentzian(data, fit.params["x0"], fit.params["gamma"])