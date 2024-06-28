void initialise_(int ny, int nx, double constant_d, double *state_a_m1);

void run_(int ny, int nx, double *transfer_b, double *transfer_e,
          double *transfer_p, double *ancillary_d, double *parameter_e,
          double *state_a_m1, double *state_a_0, double constant_d,
          double *transfer_d, double *transfer_f, double *transfer_g,
          double *output_x, double *output_y);

void finalise_(void);
