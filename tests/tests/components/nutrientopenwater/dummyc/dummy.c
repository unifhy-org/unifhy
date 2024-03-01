void initialise_(int ny, int nx,
                 // component constants,
                 double constant_d,
                 // component states
                 double *state_a_m1)
{
  int j, k, l, m;
  int nv, nw;
  int jklm;

  // dimensions for state division
  nw = 4;
  nv = constant_d;

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
          double *transfer_b, double *transfer_e, double *transfer_p,
          // component ancillary data
          double *ancillary_d,
          // component parameters
          double *parameter_e,
          // component states
          double *state_a_m1, double *state_a_0,
          // component constants,
          double constant_d,
          // from exchanger
          double *transfer_d, double *transfer_f, double *transfer_g,
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
  nv = constant_d;

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
      transfer_d[jk] = (ancillary_d[hjk] * transfer_e[jk])
        + state_a_0[jklm];
      transfer_f[jk] = parameter_e[jk] * transfer_b[jk];
      transfer_g[jk] = constant_d + transfer_b[jk];
      // compute outputs
      output_x[jk] = (parameter_e[jk] * transfer_b[jk]) + constant_d;
      output_y[jk] = (ancillary_d[jk] * transfer_e[jk])
        - state_a_0[jklm] + transfer_p[jk];
    }
}

void finalise_(void)
{}
