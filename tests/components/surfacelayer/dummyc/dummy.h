void initialise_(int nz, int ny, int nx, double *state_a_m1,
                 double *state_b_m1);

void run_(int nz, int ny, int nx, double *soil_water_stress,
          double *driving_a, double *driving_b, double *driving_c,
          double *ancillary_a, double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0, double *throughfall,
          double *snowmelt, double *transpiration,
          double *evaporation_soil_surface, double *evaporation_ponded_water,
          double *evaporation_openwater);

void finalise_(void);
