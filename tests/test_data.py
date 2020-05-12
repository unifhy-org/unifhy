import cm4twc


def get_dummy_dataset():
    return cm4twc.DataSet.from_file(
        ['dummy_data/dummy_driving_data.nc',
         'dummy_data/dummy_ancillary_data.nc'],
        name_mapping={'rainfall_flux': 'rainfall',
                      'snowfall_flux': 'snowfall',
                      'air_temperature': 'air_temperature',
                      'soil_temperature': 'soil_temperature'}
    )
