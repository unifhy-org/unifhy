void initialise_(int nz, int ny, int nx,
                 // component states
                 double *state_a_m1, double *state_b_m1)
{
  int i, j, k;
  int ijk;

  for (i=0; i < nz; i++)
    for (j=0; j < ny; j++)
      for (k=0; k < nx; k++)
      {
        // vectorisation of 3d-array
        ijk = k + nx * (j + ny * i);
        // initialise states
        state_a_m1[ijk] = 0.0;
        state_b_m1[ijk] = 0.0;
      }
}

void run_(int nz, int ny, int nx,
          // from exchanger
          double *transfer_i, double *transfer_n,
          // component driving data
          double *driving_a,
          // component parameters
          double parameter_a,
          // component states
          double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0,
          // to exchanger
          double *transfer_k, double *transfer_m,
          // component outputs
          double *output_x)
{
  int i, j, k;
  int ijk;

  for (i=0; i < nz; i++)
    for (j=0; j < ny; j++)
      for (k=0; k < nx; k++)
      {
        // vectorisation of 3d-array
        ijk = k + nx * (j + ny * i);
        // update states
        state_a_0[ijk] = state_a_m1[ijk] + 1;
        state_b_0[ijk] = state_b_m1[ijk] + 2;
        // compute transfers to exchanger
        transfer_k[ijk] = (driving_a[ijk] * parameter_a) + transfer_n[ijk]
          + state_a_0[ijk];
        transfer_m[ijk] = (driving_a[ijk] * parameter_a) + transfer_i[ijk]
          + state_b_0[ijk];
        // compute outputs
        output_x[ijk] = (driving_a[ijk] * parameter_a) + transfer_n[ijk]
          - state_a_0[ijk];
      }
}

void finalise_(void)
{}
