void initialise_(int ny, int nx,
                 // component states
                 double *state_a_m1, double *state_b_m1)
{
  int j, k;
  int jk;

  for (j=0; j < ny; j++)
    for (k=0; k < nx; k++)
    {
      // vectorisation of 2d-array
      jk = k + nx * j;
      // initialise states
      state_a_m1[jk] = 0.0;
      state_b_m1[jk] = 0.0;
    }
}

void run_(int ny, int nx,
          // from exchanger
          double *transfer_c, double *transfer_d, double *transfer_f,
          // component driving data
          double *driving_d, double *driving_e, double *driving_f,
          // component ancillary data
          double *ancillary_e,
          // component states
          double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0,
          // to exchanger
          double *transfer_a, double *transfer_b, double *transfer_h,
          // component outputs
          double *output_x)
{
  int j, k;
  int jk;

  for (j=0; j < ny; j++)
    for (k=0; k < nx; k++)
    {
      // vectorisation of 2d-array
      jk = k + nx * j;
      // update states
      state_a_0[jk] = state_a_m1[jk] + 1;
      state_b_0[jk] = state_b_m1[jk] + 2;
      // compute transfers to exchanger
      transfer_a[jk] = driving_d[jk] + driving_e[jk] + transfer_d[jk]
        + (ancillary_e[jk] * state_a_0[jk]);
      transfer_b[jk] = driving_d[jk] + driving_e[jk] + driving_f[jk]
        + transfer_c[jk] + state_b_0[jk];
      transfer_h[jk] = state_a_0[jk] * ancillary_e[jk];
      // compute outputs
      output_x[jk] = driving_d[jk] + driving_e[jk] + driving_f[jk]
        + transfer_f[jk] - state_a_0[jk];
    }
}

void finalise_(void)
{}
