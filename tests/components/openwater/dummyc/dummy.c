void initialise_(int nz, int ny, int nx,
                 // component states
                 double *state_a_m1)
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
      }
}

void run_(int nz, int ny, int nx,
          // to interface
          double *transfer_j, double *transfer_m,
          // component ancillary data
          double *ancillary_b,
          // component parameters
          double parameter_c,
          // component states
          double *state_a_m1, double *state_a_0,
          // component constants,
          double constant_c,
          // from interface
          double *transfer_l, double *transfer_n, double *transfer_o,
          // component outputs
          double *output_x, double *output_y)
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
        // compute transfers to interface
        transfer_l[ijk] = (ancillary_b[ijk] * transfer_m[ijk])
          + state_a_0[ijk];
        transfer_n[ijk] = parameter_c * transfer_j[ijk];
        transfer_o[ijk] = parameter_c + transfer_j[ijk];
        // compute outputs
        output_x[ijk] = (parameter_c * transfer_j[ijk]) + constant_c;
        output_y[ijk] = (ancillary_b[ijk] * transfer_m[ijk])
          - state_a_0[ijk];
      }
}

void finalise_(void)
{}
