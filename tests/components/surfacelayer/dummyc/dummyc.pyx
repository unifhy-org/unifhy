import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int nz, int ny, int nx, double *state_a_m1,
                     double *state_a_0, double *state_b_m1, double *state_b_0)

    void run_(int nz, int ny, int nx, double *soil_water_stress,
              double *driving_a, double *driving_b, double *driving_c,
              double *ancillary_a, double *state_a_m1, double *state_a_0,
              double *state_b_m1, double *state_b_0, double *throughfall,
              double *snowmelt, double *transpiration,
              double *evaporation_soil_surface, double *evaporation_ponded_water,
              double *evaporation_openwater)

    void finalise_()

def initialise(int nz, int ny, int nx):

    cdef cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1 = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] state_a_0 = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] state_b_m1 = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] state_b_0 = np.zeros(
        (nz, ny, nx), dtype=np.float64)

    initialise_(nz, ny, nx, &state_a_m1[0, 0, 0], &state_a_0[0, 0, 0],
                &state_b_m1[0, 0, 0], &state_b_0[0, 0, 0])

    return state_a_m1, state_a_0, state_b_m1, state_b_0

def run(cnp.ndarray[cnp.npy_float64, ndim=3] soil_water_stress,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_a,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_b,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_c,
        cnp.ndarray[cnp.npy_float64, ndim=3] ancillary_a,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_0,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_b_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_b_0):

    cdef int nz = soil_water_stress.shape[0]
    cdef int ny = soil_water_stress.shape[1]
    cdef int nx = soil_water_stress.shape[2]

    cdef cnp.ndarray[cnp.npy_float64, ndim=3] throughfall = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] snowmelt = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] transpiration = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] evaporation_soil_surface = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] evaporation_ponded_water = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] evaporation_openwater = np.zeros(
        (nz, ny, nx), dtype=np.float64)

    run_(nz, ny, nx, &soil_water_stress[0, 0, 0], &driving_a[0, 0, 0],
         &driving_b[0, 0, 0], &driving_c[0, 0, 0], &ancillary_a[0, 0, 0],
         &state_a_m1[0, 0, 0], &state_a_0[0, 0, 0], &state_b_m1[0, 0, 0],
         &state_b_0[0, 0, 0], &throughfall[0, 0, 0], &snowmelt[0, 0, 0],
         &transpiration[0, 0, 0], &evaporation_soil_surface[0, 0, 0],
         &evaporation_ponded_water[0, 0, 0], &evaporation_openwater[0, 0, 0])

    return (throughfall, snowmelt, transpiration, evaporation_soil_surface,
            evaporation_ponded_water, evaporation_openwater)

def finalise():
    finalise_()
