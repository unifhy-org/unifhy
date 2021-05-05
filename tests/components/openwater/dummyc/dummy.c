void initialise_(int nz, int ny, int nx,
                 // component constants,
                 double constant_c,
                 // component states
                 double *state_a_m1)
{
  int i, j, k, l, m;
  int nv, nw;
  int ijklm;

  // dimensions for state division
  nw = 4;
  nv = constant_c;

  for (i=0; i < nz; i++)
    for (j=0; j < ny; j++)
      for (k=0; k < nx; k++)
        for (l=0; l < nw; l++)
          for (m=0; m < nv; m++)
          {
            // vectorisation of 5d-array
            ijklm = m + nv * (l + nw * (k + nx * (j + ny * i)));
            // initialise states
            state_a_m1[ijklm] = 0.0;
          }
}

void run_(int nz, int ny, int nx,
          // to exchanger
          double *transfer_j, double *transfer_m,
          // component ancillary data
          double *ancillary_b,
          // component parameters
          double *parameter_c,
          // component states
          double *state_a_m1, double *state_a_0,
          // component constants,
          double constant_c,
          // from exchanger
          double *transfer_l, double *transfer_n, double *transfer_o,
          // component outputs
          double *output_x, double *output_y)
{
  int h, i, j, k, l, m;
  int nv, nw;
  int ijklm, hijk, ijk;

  // time dimension for monthly ancillary
  h = 11;

  // dimensions for state division
  nw = 4;
  nv = constant_c;

  for (i=0; i < nz; i++)
    for (j=0; j < ny; j++)
      for (k=0; k < nx; k++)
      {
        // vectorisation of 4d-array
        hijk = k + nx * (j + ny * (i + nz * h));
        // vectorisation of 3d-array
        ijk = k + nx * (j + ny * i);
        // update states
        for (l=0; l < nw; l++)
          for (m=0; m < nv; m++)
          {
            // vectorisation of 5d-array
            ijklm = m + nv * (l + nw * (k + nx * (j + ny * i)));
            // initialise states
            state_a_0[ijklm] = state_a_m1[ijklm] + 1;
          }
        // vectorisation of 5d-array
        l = 0;
        m = 0;
        ijklm = m + nv * (l + nw * (k + nx * (j + ny * i)));
        // compute transfers to exchanger
        transfer_l[ijk] = (ancillary_b[ijk] * transfer_m[ijk])
          + state_a_0[ijklm];
        transfer_n[ijk] = parameter_c[ijk] * transfer_j[ijk];
        transfer_o[ijk] = parameter_c[ijk] + transfer_j[ijk];
        // compute outputs
        output_x[ijk] = (parameter_c[ijk] * transfer_j[ijk]) + constant_c;
        output_y[ijk] = (ancillary_b[ijk] * transfer_m[ijk])
          - state_a_0[ijklm];
      }
}

void finalise_(void)
{}
