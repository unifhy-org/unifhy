void initialise_(int ny, int nx, double *state_a_m1,
                 double *state_b_m1);

void run_(int ny, int nx, double *transfer_c, double *transfer_d,
          double *transfer_f, double *driving_d, double *driving_e
          double *driving_f, double *ancillary_e, double *state_a_m1,
          double *state_a_0, double *state_b_m1, double *state_b_0,
          double *transfer_a, double *transfer_b, double *transfer_h,
          double *output_x);

void finalise_(void);
