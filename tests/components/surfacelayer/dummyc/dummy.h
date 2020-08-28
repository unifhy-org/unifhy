void initialise_(int nz, int ny, int nx, double *state_a_m1,
                 double *state_b_m1);

void run_(int nz, int ny, int nx, double *transfer_k, double *transfer_l,
          double *driving_a, double *driving_b, double *driving_c,
          double *ancillary_c, double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0, double *transfer_i,
          double *transfer_j);

void finalise_(void);
