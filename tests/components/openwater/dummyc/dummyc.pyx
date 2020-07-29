import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int nz, int ny, int nx, double *state_a_m1)

    void run_(int nz, int ny, int nx, double *evaporation, double *runoff,
              double *ancillary_a, double parameter_a, double *state_a_m1,
              double *state_a_0, double constant_a, double *discharge)

    void finalise_()

def initialise(cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1):

    cdef int nz = state_a_m1.shape[0]
    cdef int ny = state_a_m1.shape[1]
    cdef int nx = state_a_m1.shape[2]

    initialise_(nz, ny, nx, &state_a_m1[0, 0, 0])

def run(cnp.ndarray[cnp.npy_float64, ndim=3] evaporation_openwater,
        cnp.ndarray[cnp.npy_float64, ndim=3] runoff,
        cnp.ndarray[cnp.npy_float64, ndim=3] ancillary_a,
        double parameter_a,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_0,
        double constant_a):

    cdef int nz = evaporation_openwater.shape[0]
    cdef int ny = evaporation_openwater.shape[1]
    cdef int nx = evaporation_openwater.shape[2]

    cdef cnp.ndarray[cnp.npy_float64, ndim=3] discharge = np.zeros(
        (nz, ny, nx), dtype=np.float64)

    run_(nz, ny, nx, &evaporation_openwater[0, 0, 0], &runoff[0, 0, 0],
         &ancillary_a[0, 0, 0], parameter_a, &state_a_m1[0, 0, 0],
         &state_a_0[0, 0, 0], constant_a, &discharge[0, 0, 0])

    return discharge

def finalise():
    finalise_()
