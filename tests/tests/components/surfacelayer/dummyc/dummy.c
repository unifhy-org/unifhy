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
          double *transfer_k, double *transfer_l, double *transfer_n,
          // component driving data
          double *driving_a, double *driving_b, double *driving_c,
          // component ancillary data
          double *ancillary_c,
          // component states
          double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0,
          // to exchanger
          double *transfer_i, double *transfer_j,
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
      transfer_i[jk] = driving_a[jk] + driving_b[jk] + transfer_l[jk]
        + (ancillary_c[jk] * state_a_0[jk]);
      transfer_j[jk] = driving_a[jk] + driving_b[jk] + driving_c[jk]
        + transfer_k[jk] + state_b_0[jk];
      // compute outputs
      output_x[jk] = driving_a[jk] + driving_b[jk] + driving_c[jk]
        + transfer_n[jk] - state_a_0[jk];
    }
}

void finalise_(void)
{}
