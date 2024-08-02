import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int ny, int nx, double constant_d,
                     double *state_a_m1)

    void run_(int ny, int nx, double *transfer_b, double *transfer_e,
              double *transfer_p, double *ancillary_d, double *parameter_e,
              double *state_a_m1, double *state_a_0, double constant_d,
              double *transfer_d, double *transfer_f, double *transfer_g,
              double *output_x, double *output_y)

    void finalise_()

def initialise(double constant_d,
               cnp.ndarray[cnp.npy_float64, ndim=4] state_a_m1):

    cdef int ny = state_a_m1.shape[0]
    cdef int nx = state_a_m1.shape[1]

    initialise_(ny, nx, constant_d, &state_a_m1[0, 0, 0, 0])

def run(cnp.ndarray[cnp.npy_float64, ndim=2] transfer_b,
        cnp.ndarray[cnp.npy_float64, ndim=2] transfer_e,
        cnp.ndarray[cnp.npy_float64, ndim=2] transfer_p,
        cnp.ndarray[cnp.npy_float64, ndim=3] ancillary_d,
        cnp.ndarray[cnp.npy_float64, ndim=2] parameter_e,
        cnp.ndarray[cnp.npy_float64, ndim=4] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=4] state_a_0,
        double constant_d):

    cdef int ny = transfer_b.shape[0]
    cdef int nx = transfer_b.shape[1]

    cdef cnp.ndarray[cnp.npy_float64, ndim=2] transfer_d = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] transfer_f = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] transfer_g = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] output_x = np.zeros(
        (ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=2] output_y = np.zeros(
        (ny, nx), dtype=np.float64)

    run_(ny, nx, &transfer_b[0, 0], &transfer_e[0, 0], &transfer_p[0, 0],
         &ancillary_d[0, 0, 0], &parameter_e[0, 0],
         &state_a_m1[0, 0, 0, 0], &state_a_0[0, 0, 0, 0],
         constant_d, &transfer_d[0, 0],
         &transfer_f[0, 0], &transfer_g[0, 0],
         &output_x[0, 0], &output_y[0, 0])

    return transfer_d, transfer_f, transfer_g, output_x, output_y

def finalise():
    finalise_()
