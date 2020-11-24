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
               constant_c, &
               transfer_l, transfer_n, transfer_o, &
               output_x, output_y)

    implicit none

    ! spaceshape
    integer, intent(in) :: z, y, x
    ! from interface
    real(kind=8), intent(in), dimension(z, y, x) :: transfer_j, transfer_m
    ! component ancillary data
    real(kind=8), intent(in), dimension(12, z, y, x) :: ancillary_b
    ! component parameters
    real(kind=8), intent(in) :: parameter_c
    ! component states
    real(kind=8), intent(in), dimension(z, y, x) :: state_a_m1
    real(kind=8), intent(inout), dimension(z, y, x) :: state_a_0
    ! component constants
    real(kind=8), intent(in) :: constant_c
    ! to interface
    real(kind=8), intent(out), dimension(z, y, x) :: &
        transfer_l, transfer_n, transfer_o
    ! component outputs
    real(kind=8), intent(out), dimension(z, y, x) :: &
        output_x, output_y

    state_a_0 = state_a_m1 + 1

    transfer_l = (ancillary_b(12,:,:,:) * transfer_m) + state_a_0
    transfer_n = parameter_c * transfer_j
    transfer_o = parameter_c + transfer_j

    output_x = (parameter_c * transfer_j) + constant_c
    output_y = (ancillary_b(12,:,:,:) * transfer_m) - state_a_0

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
