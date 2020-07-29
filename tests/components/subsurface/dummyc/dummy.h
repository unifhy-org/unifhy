void initialise_(int nz, int ny, int nx, double *state_a_m1,
                 double *state_b_m1);

void run_(int nz, int ny, int nx, double *evaporation_soil_surface,
          double *evaporation_ponded_water, double *transpiration,
          double *throughfall, double *snowmelt, double *driving_a,
          double parameter_a, double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0, double *runoff,
          double *soil_water_stress);

void finalise_(void);
