import cm4twc


def get_dummy_spacedomain():
    return cm4twc.Grid(
        latitude_deg=[2.2, 1.76, 1.32, 0.88, 0.44, 0., -0.44, -0.88, -1.32, -1.76],
        longitude_deg=[-4.7, -4.26, -3.82, -3.38, -2.94, -2.5, -2.06, -1.62, -1.18],
        latitude_bounds_deg=[[2.42, 1.98], [1.98, 1.54], [1.54, 1.1], [1.1,  0.66],
                             [0.66, 0.22], [0.22, -0.22], [-0.22, -0.66],
                             [-0.66, -1.1], [-1.1, -1.54], [-1.54, -1.98]],
        longitude_bounds_deg=[[-4.92, -4.48], [-4.48, -4.04], [-4.04, -3.6],
                              [-3.6,  -3.16], [-3.16, -2.72], [-2.72, -2.28],
                              [-2.28, -1.84], [-1.84, -1.4], [-1.4, -0.96]],
        rotated=True,
        earth_radius_m=6371007., grid_north_pole_latitude_deg=38.0,
        grid_north_pole_longitude_deg=190.0
    )
