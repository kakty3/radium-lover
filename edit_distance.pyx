__author__ = 'Sergey Demurin'

import numpy as np
cimport numpy as np
cimport cython

#cdef inline float float_min(float a, float b): return a if a <= b else b

DTYPE = np.float
ctypedef np.float_t DTYPE_t

#def get_edit_distance(char * from_str, char * to_str):
@cython.boundscheck(False)
def get_edit_distance(from_str, to_str, similar_symbols=None):
    """
    Wagner-Fischer algorithm
    """

    # TODO: weights for deletion/insertion of narrow symbols,
    # substitution of similar ones
    # TODO: cythonize substitution_addition
    cdef int m = len(from_str) + 1
    cdef int n = len(to_str) + 1

    substitution_addition = 1

    cdef np.ndarray[DTYPE_t, ndim=2] d = np.zeros((m, n), dtype=DTYPE)

    d[:, 0] = range(m)
    d[0] = range(n)

    cdef unsigned int i, j

    for j in xrange(1, n):
        for i in xrange(1, m):
            if from_str[i - 1] == to_str[j - 1]:
                d[i, j] = d[i - 1, j - 1]
            else:
                if similar_symbols is not None:
                    for (symbols, addition) in similar_symbols:
                        if from_str[i - 1] in symbols and to_str[j - 1] in symbols:
                            substitution_addition = addition
                d[i, j] = min(
                    d[i - 1, j] + 1,  # deletion
                    d[i, j - 1] + 1,  # insertion
                    d[i - 1, j - 1] + substitution_addition,  # substitution
                )
    return d[m - 1, n - 1]