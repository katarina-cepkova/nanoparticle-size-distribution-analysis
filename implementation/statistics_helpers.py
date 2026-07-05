from domain_errors import InvalidInputError
import logging


def compute_cv(std: float | None, mean: float | None) -> float | None:
    """
    Coefficient of variation = std / mean — relative variability, dimensionless.
 
    Returns None if either input is None (e.g. Cauchy's mean/std are
    mathematically undefined, not just missing). Raises InvalidInputError if
    mean is exactly zero, since division by zero signals invalid input rather
    than a "not defined for this distribution" case.
    """
    if std is None or mean is None:
        return None
    
    elif (mean == 0):  # only if we have positive and negative values - particles cannot have negative size = invalid input
        er :InvalidInputError = InvalidInputError("Mean is zero, cannot compute coefficient of variation.")
        logging.error(er.message)
        raise er
    
    return std/mean


def compute_PDI(cv: float | None) -> float | None:
    """
    Polydispersity index = CV^2.
 
    Returns None if cv is None (propagates the "not defined" case from compute_cv).
    """
    if cv is None:
        return None
    return cv ** 2