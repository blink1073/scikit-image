#cython: cdivision=True
#cython: boundscheck=False
#cython: nonecheck=False
#cython: wraparound=False
cimport numpy as cnp

from _skimage2._shared.fused_numerics cimport np_floats

cnp.import_array()


def _brief_loop(np_floats[:, ::1] image, cnp.uint8_t[:, ::1] descriptors,
                cnp.int64_t[:, ::1] keypoints, cnp.int32_t[:, ::1] pos0,
                cnp.int32_t[:, ::1] pos1):
    """Populate BRIEF descriptors from intensity comparison tests.

    Parameters
    ----------
    image : ndarray
        Smoothed grayscale input image (float32 or float64).
    descriptors : ndarray of bool
        Output descriptor array, shape (n_keypoints, n_pairs).
    keypoints : ndarray of int
        Array of keypoint coordinates as ``(row, col)``.
    pos0 : ndarray of int
        Fist point of each intensity comparison pair.
    pos1 : ndarray of int
        Second point of each intensity comparison pair.
    """
    cdef Py_ssize_t num_pairs = pos0.shape[0]
    cdef Py_ssize_t num_keypoints = keypoints.shape[0]
    cdef Py_ssize_t p, k
    cdef Py_ssize_t pr0, pc0, pr1, pc1, kr, kc

    with nogil:
        for p in range(num_pairs):
            pr0 = pos0[p, 0]
            pc0 = pos0[p, 1]
            pr1 = pos1[p, 0]
            pc1 = pos1[p, 1]
            for k in range(num_keypoints):
                kr = keypoints[k, 0]
                kc = keypoints[k, 1]
                if image[kr + pr0, kc + pc0] < image[kr + pr1, kc + pc1]:
                    descriptors[k, p] = 1
