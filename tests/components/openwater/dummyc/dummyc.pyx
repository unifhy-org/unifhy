import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int nz, int ny, int nx, double constant_c,
                     double *state_a_m1)

    void run_(int nz, int ny, int nx, double *transfer_j, double *transfer_m,
              double *ancillary_b, double *parameter_c, double *state_a_m1,
              double *state_a_0, double constant_c, double *transfer_l,
              double *transfer_n, double *transfer_o, double *output_x,
              double *output_y)

    void finalise_()

def initialise(double constant_c,
               cnp.ndarray[cnp.npy_float64, ndim=5] state_a_m1):

    cdef int nz = state_a_m1.shape[0]
    cdef int ny = state_a_m1.shape[1]
    cdef int nx = state_a_m1.shape[2]

    initialise_(nz, ny, nx, constant_c, &state_a_m1[0, 0, 0, 0, 0])

def run(cnp.ndarray[cnp.npy_float64, ndim=3] transfer_j,
        cnp.ndarray[cnp.npy_float64, ndim=3] transfer_m,
        cnp.ndarray[cnp.npy_float64, ndim=4] ancillary_b,
        cnp.ndarray[cnp.npy_float64, ndim=3] parameter_c,
        cnp.ndarray[cnp.npy_float64, ndim=5] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=5] state_a_0,
        double constant_c):

    cdef int nz = transfer_j.shape[0]
    cdef int ny = transfer_j.shape[1]
    cdef int nx = transfer_j.shape[2]

    cdef cnp.ndarray[cnp.npy_float64, ndim=3] transfer_l = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] transfer_n = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] transfer_o = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] output_x = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] output_y = np.zeros(
        (nz, ny, nx), dtype=np.float64)

    run_(nz, ny, nx, &transfer_j[0, 0, 0], &transfer_m[0, 0, 0],
         &ancillary_b[0, 0, 0, 0], &parameter_c[0, 0, 0],
         &state_a_m1[0, 0, 0, 0, 0], &state_a_0[0, 0, 0, 0, 0],
         constant_c, &transfer_l[0, 0, 0],
         &transfer_n[0, 0, 0], &transfer_o[0, 0, 0],
         &output_x[0, 0, 0], &output_y[0, 0, 0])

    return transfer_l, transfer_n, transfer_o, output_x, output_y

def finalise():
    finalise_()
