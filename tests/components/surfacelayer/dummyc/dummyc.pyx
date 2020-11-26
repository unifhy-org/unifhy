import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int nz, int ny, int nx, double *state_a_m1,
                     double *state_b_m1)

    void run_(int nz, int ny, int nx, double *transfer_k, double *transfer_l,
              double *transfer_n, double *driving_a, double *driving_b,
              double *driving_c, double *ancillary_c, double *state_a_m1,
              double *state_a_0, double *state_b_m1, double *state_b_0,
              double *transfer_i, double *transfer_j, double *output_x)

    void finalise_()

def initialise(cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1,
               cnp.ndarray[cnp.npy_float64, ndim=3] state_b_m1):

    cdef int nz = state_a_m1.shape[0]
    cdef int ny = state_a_m1.shape[1]
    cdef int nx = state_a_m1.shape[2]

    initialise_(nz, ny, nx, &state_a_m1[0, 0, 0], &state_b_m1[0, 0, 0])

def run(cnp.ndarray[cnp.npy_float64, ndim=3] transfer_k,
        cnp.ndarray[cnp.npy_float64, ndim=3] transfer_l,
        cnp.ndarray[cnp.npy_float64, ndim=3] transfer_n,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_a,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_b,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_c,
        cnp.ndarray[cnp.npy_float64, ndim=3] ancillary_c,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_0,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_b_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_b_0):

    cdef int nz = transfer_k.shape[0]
    cdef int ny = transfer_k.shape[1]
    cdef int nx = transfer_k.shape[2]

    cdef cnp.ndarray[cnp.npy_float64, ndim=3] transfer_i = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] transfer_j = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] output_x = np.zeros(
        (nz, ny, nx), dtype=np.float64)

    run_(nz, ny, nx, &transfer_k[0, 0, 0], &transfer_l[0, 0, 0],
         &transfer_n[0, 0, 0], &driving_a[0, 0, 0], &driving_b[0, 0, 0],
         &driving_c[0, 0, 0], &ancillary_c[0, 0, 0], &state_a_m1[0, 0, 0],
         &state_a_0[0, 0, 0], &state_b_m1[0, 0, 0], &state_b_0[0, 0, 0],
         &transfer_i[0, 0, 0], &transfer_j[0, 0, 0], &output_x[0, 0, 0])

    return transfer_i, transfer_j, output_x

def finalise():
    finalise_()
