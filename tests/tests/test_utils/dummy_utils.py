def clockgen(comptsteps, totaltsteps):
    """
    Generate the switches for which component should run when
    Inputs:
    comptsteps - Dictionary with keys the component names and
                 values the number of 'super' timesteps that
                 each component spans (super being the timestep
                 of the fastest updating component).
    totaltsteps - Total number of 'super' timestep to run for

    Produces a generator which on each iteration yields a dictionary
    with keys the component names and values either 0 or 1 depending
    on if not or if the component is running on a given 'super' tstep
    """

    compswitches = {}

    for tstep in range(1, totaltsteps + 1):
        for comp in comptsteps.keys():
            if tstep % comptsteps[comp] != 0:
                compswitches[comp] = 0
            else:
                compswitches[comp] = 1

        yield compswitches


def calculate_temporal_weights(src, dst):
    """
    Given the number of 'super' timesteps the source (src)
    component (where the transfer is coming from) spans and
    the number of 'super' timesteps the destination (dst)
    component (where the transfer is going to) spans, work out
    the weights for and the number of previous src timesteps
    used for a given transaction.
    """

    if dst == src:
        # need to keep only one step with full weight
        keep = 1
        weights = (dst,)
    elif dst > src:
        if dst % src == 0:
            # need to keep several steps with equal weights
            keep = dst // src
            weights = (src,) * (dst // src)
        else:
            raise ValueError("src and dst must be integer multiples of each other")
    else:
        if src % dst == 0:
            # need to keep only one step with full weight
            keep = 1
            weights = (dst,)
        else:
            raise ValueError("src and dst must be integer multiples of each other")

    weights = np.array(weights)

    assert keep == weights.shape[-1], "error in exchanger temporal weights"

    return weights


def transfer_calc(transfers, inmap, outmap, component):
    """
    Function to calculate the transfers between components on different timesteps.
    Inputs:
    transfers - the full history of all the transfer variables produced by the components
                before any weighting is applied to them.
    inmap     - a dictionary containing the transfers that need to be calculated for all
                the components
    outmap    - a dictionary containing the transfers that each component produces
    component - the component to calculate the weighted transfers for. One of
                sl, ss, ow, nsl, nss, now
    """

    # which transfers need calculating
    to_calc = inmap[component]

    # for each of them
    wtransfers = {}
    for ttc in to_calc:
        # find out which component does the transfer come from
        for key in outmap.keys():
            if ttc in outmap[key]:
                ttc_from_comp = key
                break
        else:
            raise ValueError(str(ttc) + " does not exist in outmap")

        # calculate the weights that apply to this transfer
        weights = calculate_temporal_weights(
            comptsteps[ttc_from_comp], comptsteps[component]
        )
        nts_reqd = len(weights)
        weights = np.asarray(weights)
        nhist = len(transfers[ttc])  # history available for this transfer
        # what happens next depends on the length of the transfer history
        # relative to the number of timesteps needed of it

        # if there is no transfer history yet, the transfer is zero regardless
        if nhist == 0:
            wtransfer = 0
        # if the length of the history is less than the number of
        # timesteps required, the tsteps not present are zero
        elif nhist < nts_reqd:
            nmissing = nts_reqd - nhist
            missings = np.zeros(nmissing)
            transfer_hist = np.append(missings, np.asarray(transfers[ttc]))
            assert len(transfer_hist) == nts_reqd, "transfer_hist is the wrong length"
            wtransfer = np.sum(weights * transfer_hist) / np.sum(weights)
        # if the length of the history is equal or greater than
        # the timesteps required...
        elif nhist >= nts_reqd:
            transfer_hist = np.asarray(transfers[ttc])[-nts_reqd:]
            wtransfer = np.sum(weights * transfer_hist) / np.sum(weights)
        else:
            raise Error("Something is wrong")

        wtransfers[ttc] = wtransfer

    return wtransfers
