import numpy as np

import cm4twc


def compare_states(some_states, some_other_states):
    rtol, atol = cm4twc.rtol(), cm4twc.atol()

    comparison = []
    if some_states is not None:
        for state in some_states:
            comparison.append(
                np.allclose(
                    some_states[state].get_timestep(slice(None)),
                    some_other_states[state].get_timestep(slice(None)),
                    rtol, atol
                )
            )
    else:
        if some_other_states is None:
            comparison.append(True)
        else:
            comparison.append(False)

    if False in comparison:
        return False
    else:
        return True
