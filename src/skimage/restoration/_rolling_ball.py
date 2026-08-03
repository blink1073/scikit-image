from _skimage2.restoration._rolling_ball import (
    ball_kernel as ball_kernel,
    ellipsoid_kernel as ellipsoid_kernel,
    rolling_ball as rolling_ball,
)  # noqa: F401

__all__ = [
    'ball_kernel',
    'ellipsoid_kernel',
    'rolling_ball',
]

from skimage._doctest_adapters import adapt_doctests

adapt_doctests(globals())

# Temporary no-op comment: live test of path-scoped auto-benchmarks and
# the run-benchmark label override against a real PR targeting main
# (issue #8199) - this line is removed before merge.
