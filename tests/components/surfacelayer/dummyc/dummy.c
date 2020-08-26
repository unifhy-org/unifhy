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
          // from interface
          double *transfer_k, double *transfer_l,
          // component driving data
          double *driving_a, double *driving_b, double *driving_c,
          // component ancillary data
          double *ancillary_c,
          // component states
          double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0,
          // to interface
          double *transfer_i, double *transfer_j)
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
        // compute transfers to interface
        transfer_i[ijk] = driving_a[ijk] + driving_b[ijk] + transfer_l[ijk]
          + (ancillary_c[ijk] * state_a_0[ijk]);
        transfer_j[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk]
          + transfer_k[ijk] + state_b_0[ijk];
      }
}

void finalise_(void)
{}
