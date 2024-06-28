subroutine initialise(y, x, state_a_m1, state_b_m1)
    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! component states
    real(kind=8), intent(inout), dimension(y, x) :: state_a_m1, state_b_m1

    state_a_m1 = 0
    state_b_m1 = 0

end subroutine initialise

subroutine run(y, x, &
               transfer_c, transfer_d, transfer_f, &
               driving_d, driving_e, driving_f, &
               ancillary_e, &
               state_a_m1, state_a_0, state_b_m1, state_b_0, &
               transfer_a, transfer_b, transfer_h, &
               output_x)

    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! from exchanger
    real(kind=8), intent(in), dimension(y, x) :: &
        transfer_c, transfer_d, transfer_f
    ! component driving data
    real(kind=8), intent(in), dimension(y, x) :: &
        driving_d, driving_e, driving_f
    ! component ancillary data
    real(kind=8), intent(in), dimension(y, x) :: ancillary_e
    ! component states
    real(kind=8), intent(in), dimension(y, x) :: state_a_m1, state_b_m1
    real(kind=8), intent(inout), dimension(y, x) :: state_a_0, state_b_0
    ! to exchanger
    real(kind=8), intent(out), dimension(y, x) :: transfer_a, transfer_b, transfer_h
    ! component outputs
    real(kind=8), intent(out), dimension(y, x) :: output_x

    state_a_0 = state_a_m1 + 1
    state_b_0 = state_b_m1 + 2

    transfer_a = driving_d + driving_e + transfer_d + (ancillary_e * state_a_0)
    transfer_b = driving_d + driving_e + driving_f + transfer_c + state_b_0
    transfer_h = state_a_0 * ancillary_e

    output_x = driving_d + driving_e + driving_f + transfer_f - state_a_0

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
