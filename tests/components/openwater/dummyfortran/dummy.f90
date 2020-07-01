module dummyfortran
    contains

        subroutine initialise(z, y, x, state_a_m1, state_a_0)
            implicit none

            ! spaceshape
            integer, intent(in) :: z, y, x
            ! component states
            real(kind=8), intent(out), dimension(z, y, x) :: state_a_m1, state_a_0

            state_a_m1 = 0
            state_a_0 = 0

        end subroutine initialise

        subroutine run(z, y, x, &
            evaporation_openwater, runoff, &
            ancillary_a, &
            parameter_a, &
            state_a_m1, state_a_0, &
            constant_a, &
            discharge)

            implicit none

            ! spaceshape
            integer, intent(in) :: z, y, x
            ! interface fluxes in
            real(kind=8), intent(in), dimension(z, y, x) :: &
                evaporation_openwater, runoff
            ! component ancillary data
            real(kind=8), intent(in), dimension(z, y, x) :: ancillary_a
            ! component parameters
            real(kind=8), intent(inout) :: parameter_a
            ! component states
            real(kind=8), intent(in), dimension(z, y, x) :: state_a_m1
            real(kind=8), intent(inout), dimension(z, y, x) :: state_a_0
            ! component constants
            real(kind=8), intent(inout) :: constant_a
            ! interface fluxes out
            real(kind=8), intent(out), dimension(z, y, x) :: discharge

            state_a_0 = state_a_m1 + 1

            discharge = ancillary_a * parameter_a * constant_a

        end subroutine run

        subroutine finalise()
            implicit none

        end subroutine finalise

end module dummyfortran
