import numpy as np
cimport numpy as cnp

cdef extern from "dummy.h":

    void initialise_(int nz, int ny, int nx, double *state_a_m1,
                     double *state_a_0, double *state_b_m1, double *state_b_0)

    void run_(int nz, int ny, int nx, double *evaporation_soil_surface,
              double *evaporation_ponded_water, double *evaporation_openwater,
              double *throughfall, double *snowmelt, double *driving_a,
              double parameter_a, double *state_a_m1, double *state_a_0,
              double *state_b_m1, double *state_b_0, double *runoff,
              double *soil_water_stress)

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

def run(cnp.ndarray[cnp.npy_float64, ndim=3] evaporation_soil_surface,
        cnp.ndarray[cnp.npy_float64, ndim=3] evaporation_ponded_water,
        cnp.ndarray[cnp.npy_float64, ndim=3] transpiration,
        cnp.ndarray[cnp.npy_float64, ndim=3] throughfall,
        cnp.ndarray[cnp.npy_float64, ndim=3] snowmelt,
        cnp.ndarray[cnp.npy_float64, ndim=3] driving_a,
        double parameter_a,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_a_0,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_b_m1,
        cnp.ndarray[cnp.npy_float64, ndim=3] state_b_0):

    cdef int nz = evaporation_soil_surface.shape[0]
    cdef int ny = evaporation_soil_surface.shape[1]
    cdef int nx = evaporation_soil_surface.shape[2]

    cdef cnp.ndarray[cnp.npy_float64, ndim=3] runoff = np.zeros(
        (nz, ny, nx), dtype=np.float64)
    cdef cnp.ndarray[cnp.npy_float64, ndim=3] soil_water_stress = np.zeros(
        (nz, ny, nx), dtype=np.float64)

    run_(nz, ny, nx, &evaporation_soil_surface[0, 0, 0],
         &evaporation_ponded_water[0, 0, 0], &transpiration[0, 0, 0],
         &throughfall[0, 0, 0], &snowmelt[0, 0, 0], &driving_a[0, 0, 0],
         parameter_a, &state_a_m1[0, 0, 0], &state_a_0[0, 0, 0],
         &state_b_m1[0, 0, 0], &state_b_0[0, 0, 0], &runoff[0, 0, 0],
         &soil_water_stress[0, 0, 0])

    return runoff, soil_water_stress

def finalise():
    finalise_()
