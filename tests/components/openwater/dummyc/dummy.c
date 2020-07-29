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
          // interface fluxes in
          double *evaporation_openwater, double *runoff,
          // component ancillary data
          double *ancillary_a,
          // component parameters
          double parameter_a,
          // component states
          double *state_a_m1, double *state_a_0,
          // component constants,
          double constant_a,
          // interface fluxes out
          double *discharge)
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
        // interface fluxes out
        discharge[ijk] = ancillary_a[ijk] * parameter_a * constant_a;
      }
}

void finalise_(void)
{}
