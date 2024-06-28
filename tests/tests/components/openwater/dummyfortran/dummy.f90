subroutine initialise(y, x, constant_c, state_a_m1)
    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! component constants
    integer, intent(in) :: constant_c
    ! component states
    real(kind=8), intent(inout), dimension(y, x, 4, constant_c) :: state_a_m1

    state_a_m1 = 0

end subroutine initialise

subroutine run(y, x, &
               transfer_j, transfer_m, &
               ancillary_b, &
               parameter_c, &
               state_a_m1, state_a_0, &
               constant_c, &
               transfer_l, transfer_n, transfer_o, transfer_p, &
               output_x, output_y)

    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! from exchanger
    real(kind=8), intent(in), dimension(y, x) :: transfer_j, transfer_m
    ! component ancillary data
    real(kind=8), intent(in), dimension(12, y, x) :: ancillary_b
    ! component parameters
    real(kind=8), intent(in), dimension(y, x) :: parameter_c
    ! component constants
    integer, intent(in) :: constant_c
    ! component states
    real(kind=8), intent(in), dimension(y, x, 4, constant_c) :: state_a_m1
    real(kind=8), intent(inout), dimension(y, x, 4, constant_c) :: state_a_0
    ! to exchanger
    real(kind=8), intent(out), dimension(y, x) :: &
        transfer_l, transfer_n, transfer_o, transfer_p
    ! component outputs
    real(kind=8), intent(out), dimension(y, x) :: &
        output_x, output_y

    state_a_0 = state_a_m1 + 1

    transfer_l = (ancillary_b(12,:,:) * transfer_m) + state_a_0(:,:,1,1)
    transfer_n = parameter_c * transfer_j
    transfer_o = parameter_c + transfer_j
    transfer_p = state_a_0(:,:,1,1)

    output_x = (parameter_c * transfer_j) + constant_c
    output_y = (ancillary_b(12,:,:) * transfer_m) - state_a_0(:,:,1,1)

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
