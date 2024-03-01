import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int ny, int nx, double *state_a_m1,
                     double *state_b_m1)

    void run_(int ny, int nx, double *transfer_c, double *transfer_d,
              double *transfer_f, double *driving_d, double *driving_e,
              double *driving_f, double *ancillary_e, double *state_a_m1,
              double *state_a_0, double *state_b_m1, double *state_b_0,
              double *transfer_a, double *transfer_b, double *transfer_h,
              double *output_x);

    void finalise_()

def initialise(cnp.ndarray[cnp.npy_float64, ndim=2] state_a_m1,
               cnp.ndarray[cnp.npy_float64, ndim=2] state_b_m1):

    cdef int ny = state_a_m1.shape[0]
    cdef int nx = state_a_m1.shape[1]

    initialise_(ny, nx, &state_a_m1[0, 0], &state_b_m1[0, 0])

def run(cnp.ndarray[cnp.npy_float64, ndim=2] transfer_c,
        cnp.ndarray[cnp.npy_float64, ndim=2] transfer_d,
        cnp.ndarray[cnp.npy_float64, ndim=2] transfer_f,
        cnp.ndarray[cnp.npy_float64, ndim=2] driving_d,
        cnp.ndarray[cnp.npy_float64, ndim=2] driving_e,
        cnp.ndarray[cnp.npy_float64, ndim=2] driving_f,
        cnp.ndarray[cnp.npy_float64, ndim=2] ancillary_e,
        cnp.ndarray[cnp.npy_float64, ndim=2] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=2] state_a_0,
        cnp.ndarray[cnp.npy_float64, ndim=2] state_b_m1,
        cnp.ndarray[cnp.npy_float64, ndim=2] state_b_0):

    cdef int ny = transfer_k.shape[0]
    cdef int nx = transfer_k.shape[1]

    cdef cnp.ndarray[cnp.npy_float64, ndim=2] transfer_a = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] transfer_b = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] transfer_h = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] output_x = np.zeros(
        (ny, nx), dtype=np.float64)

    run_(ny, nx, &transfer_c[0, 0], &transfer_d[0, 0],
         &transfer_f[0, 0], &driving_d[0, 0], &driving_e[0, 0],
         &driving_f[0, 0], &ancillary_e[0, 0], &state_a_m1[0, 0],
         &state_a_0[0, 0], &state_b_m1[0, 0], &state_b_0[0, 0],
         &transfer_a[0, 0], &transfer_b[0, 0], &transfer_h[0, 0],
         &output_x[0, 0])

    return transfer_a, transfer_b, transfer_h, output_x

def finalise():
    finalise_()
