void initialise_(int ny, int nx,
                 // component constants,
                 double constant_c,
                 // component states
                 double *state_a_m1)
{
  int j, k, l, m;
  int nv, nw;
  int jklm;

  // dimensions for state division
  nw = 4;
  nv = constant_c;

  for (j=0; j < ny; j++)
    for (k=0; k < nx; k++)
      for (l=0; l < nw; l++)
        for (m=0; m < nv; m++)
        {
          // vectorisation of 5d-array
          jklm = m + nv * (l + nw * (k + nx * j));
          // initialise states
          state_a_m1[jklm] = 0.0;
        }
}

void run_(int ny, int nx,
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
  int h, j, k, l, m;
  int nv, nw;
  int jklm, hjk, jk;

  // time dimension for monthly ancillary
  h = 11;

  // dimensions for state division
  nw = 4;
  nv = constant_c;

  for (j=0; j < ny; j++)
    for (k=0; k < nx; k++)
    {
      // vectorisation of 3d-array (space with time)
      hjk = k + nx * (j + ny * h);
      // vectorisation of 2d-array (space without time)
      jk = k + nx * j;
      // update states
      for (l=0; l < nw; l++)
        for (m=0; m < nv; m++)
        {
          // vectorisation of 5d-array
          jklm = m + nv * (l + nw * (k + nx * j));
          // initialise states
          state_a_0[jklm] = state_a_m1[jklm] + 1;
        }
      // vectorisation of 5d-array
      l = 0;
      m = 0;
      jklm = m + nv * (l + nw * (k + nx * j));
      // compute transfers to exchanger
      transfer_l[jk] = (ancillary_b[hjk] * transfer_m[jk])
        + state_a_0[jklm];
      transfer_n[jk] = parameter_c[jk] * transfer_j[jk];
      transfer_o[jk] = parameter_c[jk] + transfer_j[jk];
      // compute outputs
      output_x[jk] = (parameter_c[jk] * transfer_j[jk]) + constant_c;
      output_y[jk] = (ancillary_b[jk] * transfer_m[jk])
        - state_a_0[jklm];
    }
}

void finalise_(void)
{}
