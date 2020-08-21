subroutine initialise(z, y, x, state_a_m1)
    implicit none

    ! spaceshape
    integer, intent(in) :: z, y, x
    ! component states
    real(kind=8), intent(inout), dimension(z, y, x) :: state_a_m1

    state_a_m1 = 0

end subroutine initialise

subroutine run(z, y, x, &
               transfer_j, transfer_m, &
               ancillary_b, &
               parameter_c, &
               state_a_m1, state_a_0, &
               constant_a, &
               transfer_l, transfer_n, transfer_o)

    implicit none

    ! spaceshape
    integer, intent(in) :: z, y, x
    ! from interface
    real(kind=8), intent(in), dimension(z, y, x) :: transfer_j, transfer_m
    ! component ancillary data
    real(kind=8), intent(in), dimension(z, y, x) :: ancillary_b
    ! component parameters
    real(kind=8), intent(inout) :: parameter_c
    ! component states
    real(kind=8), intent(in), dimension(z, y, x) :: state_a_m1
    real(kind=8), intent(inout), dimension(z, y, x) :: state_a_0
    ! component constants
    real(kind=8), intent(inout) :: constant_a
    ! to interface
    real(kind=8), intent(out), dimension(z, y, x) :: &
        transfer_l, transfer_n, transfer_o

    state_a_0 = state_a_m1 + 1

    transfer_l = (ancillary_b * transfer_m) + state_a_0
    transfer_n = parameter_c * transfer_j
    transfer_o = parameter_c + transfer_j

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
