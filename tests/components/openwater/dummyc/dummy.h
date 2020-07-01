void initialise_(int nz, int ny, int nx, double *state_a_m1, double *state_a_0);

void run_(int nz, int ny, int nx, double *evaporation_openwater, double *runoff,
          double *ancillary_a, double parameter_a, double *state_a_m1,
          double *state_a_0, double constant_a, double *discharge);

void finalise_(void);
