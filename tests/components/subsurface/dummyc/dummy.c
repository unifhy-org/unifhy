void initialise_(int nz, int ny, int nx,
                 // component states
                 double *state_a_m1, double *state_a_0,
                 double *state_b_m1, double *state_b_0)
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
        state_a_0[ijk] = 0.0;
        state_b_m1[ijk] = 0.0;
        state_b_0[ijk] = 0.0;
      }
}

void run_(int nz, int ny, int nx,
          // interface fluxes in
          double *evaporation_soil_surface, double *evaporation_ponded_water,
          double *transpiration, double *throughfall, double *snowmelt,
          // component driving data
          double *driving_a,
          // component parameters
          double parameter_a,
          // component states
          double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0,
          // interface fluxes out
          double *runoff, double *soil_water_stress)
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
        // interface fluxes out
        runoff[ijk] = driving_a[ijk] * parameter_a;
        soil_water_stress[ijk] = driving_a[ijk] * parameter_a;
      }
}

void finalise_(void)
{}
