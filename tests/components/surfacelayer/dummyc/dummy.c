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
          // interface fluxes in
          double *soil_water_stress,
          // component driving data
          double *driving_a, double *driving_b, double *driving_c,
          // component ancillary data
          double *ancillary_a,
          // component states
          double *state_a_m1, double *state_a_0,
          double *state_b_m1, double *state_b_0,
          // interface fluxes out
          double *throughfall, double *snowmelt, double *transpiration,
          double *evaporation_soil_surface, double *evaporation_ponded_water,
          double *evaporation_openwater)
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
        throughfall[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk];
        snowmelt[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk];
        transpiration[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk];
        evaporation_soil_surface[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk];
        evaporation_ponded_water[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk];
        evaporation_openwater[ijk] = driving_a[ijk] + driving_b[ijk] + driving_c[ijk];
      }
}

void finalise_(void)
{}
