import warnings


class DesignError(Exception):
    pass  # deprecated


class AnalysisError(Exception):
    pass


class ModelError(Exception):
    pass


class ModelWarning(Warning):
    pass


def deprecation(message):
    warnings.warn(message, stacklevel=3)
