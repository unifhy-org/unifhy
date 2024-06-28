subroutine initialise(y, x, constant_d, state_a_m1)
    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! component constants
    integer, intent(in) :: constant_d
    ! component states
    real(kind=8), intent(inout), dimension(y, x, 4, constant_d) :: state_a_m1

    state_a_m1 = 0

end subroutine initialise

subroutine run(y, x, &
               transfer_b, transfer_e, transfer_p, &
               ancillary_d, &
               parameter_e, &
               state_a_m1, state_a_0, &
               constant_d, &
               transfer_d, transfer_f, transfer_g, &
               output_x, output_y)

    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! from exchanger
    real(kind=8), intent(in), dimension(y, x) :: transfer_b, transfer_e, transfer_p
    ! component ancillary data
    real(kind=8), intent(in), dimension(12, y, x) :: ancillary_d
    ! component parameters
    real(kind=8), intent(in), dimension(y, x) :: parameter_e
    ! component constants
    integer, intent(in) :: constant_d
    ! component states
    real(kind=8), intent(in), dimension(y, x, 4, constant_d) :: state_a_m1
    real(kind=8), intent(inout), dimension(y, x, 4, constant_d) :: state_a_0
    ! to exchanger
    real(kind=8), intent(out), dimension(y, x) :: &
        transfer_d, transfer_f, transfer_g
    ! component outputs
    real(kind=8), intent(out), dimension(y, x) :: &
        output_x, output_y

    state_a_0 = state_a_m1 + 1

    transfer_d = (ancillary_d(12,:,:) * transfer_e) + state_a_0(:,:,1,1)
    transfer_f = parameter_e * transfer_b
    transfer_g = constant_d + transfer_b

    output_x = (parameter_e * transfer_b) + constant_d
    output_y = (ancillary_d(12,:,:) * transfer_e) - state_a_0(:,:,1,1) + transfer_p

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
