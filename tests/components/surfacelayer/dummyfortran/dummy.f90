subroutine initialise(z, y, x, state_a_m1, state_b_m1)
    implicit none

    ! spaceshape
    integer, intent(in) :: z, y, x
    ! component states
    real(kind=8), intent(inout), dimension(z, y, x) :: state_a_m1, state_b_m1

    state_a_m1 = 0
    state_b_m1 = 0

end subroutine initialise

subroutine run(z, y, x, &
    soil_water_stress, &
    driving_a, driving_b, driving_c, ancillary_a, &
    state_a_m1, state_a_0, state_b_m1, state_b_0, &
    throughfall, snowmelt, transpiration, evaporation_soil_surface, &
    evaporation_ponded_water, evaporation_openwater)

    implicit none

    ! spaceshape
    integer, intent(in) :: z, y, x
    ! interface fluxes in
    real(kind=8), intent(in), dimension(z, y, x) :: soil_water_stress
    ! component driving data
    real(kind=8), intent(in), dimension(z, y, x) :: driving_a, driving_b, driving_c
    ! component ancillary data
    real(kind=8), intent(in), dimension(z, y, x) :: ancillary_a
    ! component states
    real(kind=8), intent(in), dimension(z, y, x) :: state_a_m1, state_b_m1
    real(kind=8), intent(inout), dimension(z, y, x) :: state_a_0, state_b_0
    ! interface fluxes out
    real(kind=8), intent(out), dimension(z, y, x) :: &
        throughfall, snowmelt, transpiration, evaporation_soil_surface, &
        evaporation_ponded_water, evaporation_openwater

    state_a_0 = state_a_m1 + 1
    state_b_0 = state_b_m1 + 2

    throughfall = driving_a + driving_b + driving_c
    snowmelt = driving_a + driving_b + driving_c
    transpiration = driving_a + driving_b + driving_c
    evaporation_soil_surface = driving_a + driving_b + driving_c
    evaporation_ponded_water = driving_a + driving_b + driving_c
    evaporation_openwater = driving_a + driving_b + driving_c

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
