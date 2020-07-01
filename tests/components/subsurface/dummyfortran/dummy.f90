module dummyfortran
    contains

        subroutine initialise(z, y, x, state_a_m1, state_a_0, state_b_m1, state_b_0)
            implicit none

            ! spaceshape
            integer, intent(in) :: z, y, x
            ! component states
            real(kind=8), intent(out), dimension(z, y, x) :: state_a_m1, state_a_0, state_b_m1, state_b_0

            state_a_m1 = 0
            state_a_0 = 0
            state_b_m1 = 0
            state_b_0 = 0

        end subroutine initialise

        subroutine run(z, y, x, &
            evaporation_soil_surface, evaporation_ponded_water, &
            transpiration, throughfall, snowmelt, &
            driving_a, parameter_a, state_a_m1, state_a_0, state_b_m1, &
            state_b_0, runoff, soil_water_stress)

            implicit none

            ! spaceshape
            integer, intent(in) :: z, y, x
            ! interface fluxes in
            real(kind=8), intent(in), dimension(z, y, x) :: &
                evaporation_soil_surface, evaporation_ponded_water, &
                transpiration, throughfall, snowmelt
            ! component driving data
            real(kind=8), intent(in), dimension(z, y, x) :: driving_a
            ! component parameters
            real(kind=8), intent(in) :: parameter_a
            ! component states
            real(kind=8), intent(in), dimension(z, y, x) :: state_a_m1, state_b_m1
            real(kind=8), intent(inout), dimension(z, y, x) :: state_a_0, state_b_0
            ! interface fluxes out
            real(kind=8), intent(out), dimension(z, y, x) :: &
                runoff, soil_water_stress

            state_a_0 = state_a_m1 + 1
            state_b_0 = state_b_m1 + 2

            runoff = driving_a * parameter_a
            soil_water_stress = driving_a * parameter_a

        end subroutine run

        subroutine finalise()
            implicit none

        end subroutine finalise

end module dummyfortran
