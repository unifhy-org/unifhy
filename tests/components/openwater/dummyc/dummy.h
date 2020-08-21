void initialise_(int nz, int ny, int nx, double *state_a_m1);

void run_(int nz, int ny, int nx, double *transfer_j, double *transfer_m,
          double *ancillary_b, double parameter_c, double *state_a_m1,
          double *state_a_0, double constant_a, double *transfer_l,
          double *transfer_n, double *transfer_o);

void finalise_(void);
