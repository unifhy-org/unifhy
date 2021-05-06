void initialise_(int nz, int ny, int nx, double *state_a_m1,
                 double *state_b_m1);

void run_(int nz, int ny, int nx, double *transfer_i, double *transfer_n,
          double *driving_a, double *parameter_a, double *state_a_m1,
          double *state_a_0, double *state_b_m1, double *state_b_0,
          double *transfer_k, double *transfer_m, double *output_x);

void finalise_(void);
