import unittest

import cm4twc


def get_instance_model_from_components(surfacelayer, subsurface, openwater):

    return cm4twc.Model(
        surfacelayer=surfacelayer,
        subsurface=subsurface,
        openwater=openwater
    )


class TestModelAPI(unittest.TestCase):

    def test_model_init_with_all_possible_component_combi(self):

        # full factorial design of experiment
        # (i.e. all possible combinations of components)
        doe = (
            # tuple(surfacelayer_component, subsurface_component, openwater_component)
            # with 'c' for _Component, 'd' for DataComponent, 'n' for NullComponent
            ('c', 'c', 'c'),
            ('d', 'c', 'c'),
            ('n', 'c', 'c'),
            ('c', 'd', 'c'),
            ('d', 'd', 'c'),
            ('n', 'd', 'c'),
            ('c', 'n', 'c'),
            ('d', 'n', 'c'),
            ('n', 'n', 'c'),
            ('c', 'c', 'd'),
            ('d', 'c', 'd'),
            ('n', 'c', 'd'),
            ('c', 'd', 'd'),
            ('d', 'd', 'd'),
            ('n', 'd', 'd'),
            ('c', 'n', 'd'),
            ('d', 'n', 'd'),
            ('n', 'n', 'd'),
            ('c', 'c', 'n'),
            ('d', 'c', 'n'),
            ('n', 'c', 'n'),
            ('c', 'd', 'n'),
            ('d', 'd', 'n'),
            ('n', 'd', 'n'),
            ('c', 'n', 'n'),
            ('d', 'n', 'n'),
            ('n', 'n', 'n')
        )

        # loop through all the possible combinations of components
        for combination in doe:
            # for surfacelayer component
            if combination[0] == 'c':
                surfacelayer = cm4twc.surfacelayer.Dummy
            elif combination[0] == 'd':
                surfacelayer = cm4twc.DataComponent
            else:  # i.e. 'n'
                surfacelayer = cm4twc.NullComponent

            # for subsurface component
            if combination[1] == 'c':
                subsurface = cm4twc.subsurface.Dummy
            elif combination[1] == 'd':
                subsurface = cm4twc.DataComponent
            else:  # i.e. 'n'
                subsurface = cm4twc.NullComponent

            # for openwater
            if combination[2] == 'c':
                openwater = cm4twc.openwater.Dummy
            elif combination[2] == 'd':
                openwater = cm4twc.DataComponent
            else:  # i.e. 'n'
                openwater = cm4twc.NullComponent

            # try to get an instance of model with the given combination
            get_instance_model_from_components(surfacelayer,
                                               subsurface,
                                               openwater)


if __name__ == '__main__':
    unittest.main()
