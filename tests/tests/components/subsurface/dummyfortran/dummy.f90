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
               transfer_i, transfer_n, &
               driving_a, &
               parameter_a, &
               state_a_m1, state_a_0, state_b_m1, state_b_0, &
               transfer_k, transfer_m, &
               output_x)

    implicit none

    ! spaceshape
    integer, intent(in) :: y, x
    ! from exchanger
    real(kind=8), intent(in), dimension(y, x) :: transfer_i, transfer_n
    ! component driving data
    real(kind=8), intent(in), dimension(y, x) :: driving_a
    ! component parameters
    real(kind=8), intent(in), dimension(y, x) :: parameter_a
    ! component states
    real(kind=8), intent(in), dimension(y, x) :: state_a_m1, state_b_m1
    real(kind=8), intent(inout), dimension(y, x) :: state_a_0, state_b_0
    ! to exchanger
    real(kind=8), intent(out), dimension(y, x) :: transfer_k, transfer_m
    ! component outputs
    real(kind=8), intent(out), dimension(y, x) :: output_x

    state_a_0 = state_a_m1 + 1
    state_b_0 = state_b_m1 + 2

    transfer_k = (driving_a * parameter_a) + transfer_n + state_a_0
    transfer_m = (driving_a * parameter_a) + transfer_i + state_b_0

    output_x = (driving_a * parameter_a) + transfer_n - state_a_0

end subroutine run

subroutine finalise()
    implicit none

end subroutine finalise
