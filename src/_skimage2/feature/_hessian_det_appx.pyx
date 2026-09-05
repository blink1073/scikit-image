#cython: cdivision=True
#cython: boundscheck=False
#cython: nonecheck=False
#cython: wraparound=False
import numpy as np
cimport numpy as cnp

cnp.import_array()


cdef inline cnp.intp_t _clip(cnp.intp_t x, cnp.intp_t low,
                             cnp.intp_t high) noexcept nogil:
    """Clip coordinate between low and high values."""
    if x > high:
        return high
    elif x < low:
        return low
    else:
        return x


cdef inline cnp.float64_t _integ(cnp.float64_t[:, ::1] img,
                                 cnp.intp_t r, cnp.intp_t c,
                                 cnp.intp_t rl, cnp.intp_t cl) noexcept nogil:
    """Integrate over the 2D integral image in the given window."""
    cdef cnp.float64_t ans
    cdef cnp.intp_t height = img.shape[0]
    cdef cnp.intp_t width = img.shape[1]
    cdef cnp.intp_t r2, c2

    r = _clip(r, 0, height - 1)
    c = _clip(c, 0, width - 1)
    r2 = _clip(r + rl, 0, height - 1)
    c2 = _clip(c + cl, 0, width - 1)

    ans = img[r, c] + img[r2, c2] - img[r, c2] - img[r2, c]
    return ans if ans > 0.0 else 0.0


def _hessian_matrix_det(cnp.float64_t[:, ::1] img, double sigma):
    """Compute the approximate Hessian Determinant over a 2D image.

    This method uses box filters over integral images to compute the
    approximate Hessian Determinant as described in [1]_.

    Parameters
    ----------
    img : array
        The integral image over which to compute Hessian Determinant.
    sigma : float
        Standard deviation used for the Gaussian kernel, used for the Hessian
        matrix.

    Returns
    -------
    out : array
        The array of the Determinant of Hessians.

    References
    ----------
    .. [1] Herbert Bay, Andreas Ess, Tinne Tuytelaars, Luc Van Gool,
           "SURF: Speeded Up Robust Features"
           ftp://ftp.vision.ee.ethz.ch/publications/articles/eth_biwi_00517.pdf

    Notes
    -----
    The running time of this method only depends on size of the image. It is
    independent of `sigma` as one would expect. The downside is that the
    result for `sigma` less than `3` is not accurate, i.e., not similar to
    the result obtained if someone computed the Hessian and took its
    determinant.
    """
    cdef cnp.intp_t height = img.shape[0]
    cdef cnp.intp_t width = img.shape[1]
    cdef cnp.intp_t size = <cnp.intp_t>(3 * sigma)
    cdef cnp.intp_t s2 = (size - 1) // 2
    cdef cnp.intp_t s3 = size // 3
    cdef cnp.intp_t w = size
    cdef double w_i = 1.0 / size / size
    cdef cnp.intp_t r, c
    cdef double tl, br, bl, tr, dxy, mid, side, dxx, dyy

    cdef cnp.ndarray[cnp.float64_t, ndim=2] out = \
        np.empty((height, width), dtype=np.float64)
    cdef cnp.float64_t[:, ::1] out_view = out

    if size % 2 == 0:
        size += 1

    with nogil:
        for r in range(height):
            for c in range(width):
                tl = _integ(img, r - s3, c - s3, s3, s3)  # top left
                br = _integ(img, r + 1, c + 1, s3, s3)  # bottom right
                bl = _integ(img, r - s3, c + 1, s3, s3)  # bottom left
                tr = _integ(img, r + 1, c - s3, s3, s3)  # top right

                dxy = bl + tr - tl - br
                dxy = -dxy * w_i

                mid = _integ(img, r - s3 + 1, c - s2, 2 * s3 - 1, w)
                side = _integ(img, r - s3 + 1, c - s3 // 2, 2 * s3 - 1, s3)

                dxx = mid - 3 * side
                dxx = -dxx * w_i

                mid = _integ(img, r - s2, c - s3 + 1, w, 2 * s3 - 1)
                side = _integ(img, r - s3 // 2, c - s3 + 1, s3, 2 * s3 - 1)

                dyy = mid - 3 * side
                dyy = -dyy * w_i

                out_view[r, c] = dxx * dyy - 0.81 * (dxy * dxy)

    return out
