import unittest

from accomplice.sg_config import SG_CONFIG
from .ShotGridDatabase import ShotGridDatabase



class ShotGridDatabaseTest(unittest.TestCase):
    db = ShotGridDatabase( # If we find that there are errors with test order, we can put this in setUp
        SG_CONFIG['SITE_NAME'],
        SG_CONFIG['SCRIPT_NAME'],
        SG_CONFIG['SCRIPT_KEY'],
        SG_CONFIG['ACCOMPLICE_ID']
    )
    def setUp(self): # Runs before each test
        pass

    def test_get_asset(self):
        asset = self.db.get_asset('tree')
        self.assertEqual(asset.name, 'tree')
        self.assertTrue(asset.path.endswith('tree'))
    
    def test_get_asset_id(self):
        # I'll use Letty for this example because it's unlikely that her id will change
        asset_id = self.db.get_asset_id('letty')
        self.assertEqual(asset_id, 3954)

    def test_get_asset_id_for_asset_with_subassets_1(self):
        # Tree
        asset_id = self.db.get_asset_id('tree')
        self.assertEqual(asset_id, 5307)

    def test_get_asset_id_for_asset_with_subassets_2(self):
        # Bicycle Rack
        asset_id = self.db.get_asset_id('bicyclerack')
        self.assertEqual(asset_id, 5108)
    
    def test_get_asset_list(self):
        asset_list = self.db.get_asset_list()
        self.assertTrue(len(asset_list) > 0)
        self.assertEqual(len(asset_list), len(set(asset_list))) # Check for duplicates

class AsynchronousShotGridDatabaseTest(unittest.TestCase):
    db = ShotGridDatabase( # If we find that there are errors with test order, we can put this in setUp
        SG_CONFIG['SITE_NAME'],
        SG_CONFIG['SCRIPT_NAME'],
        SG_CONFIG['SCRIPT_KEY'],
        SG_CONFIG['ACCOMPLICE_ID']
    )
    variant = None
    def setUp(self):
        self.name = 'AUTOMATED_TEST_SUBASSET'
        self.variant = self.db.create_asset(self.name, 'Environment', '/tmp/' + self.name + '.usd', parent_name='tree')

    def test_create_test_subasset(self):
        self.assertIsNotNone(self.variant)
        self.assertTrue(type(self.variant) is dict)
        self.assertEquals(self.variant['name'], self.name)
        self.assertEquals(self.variant['sg_path'], '/tmp/' + self.name + '.usd')
        self.assertEquals(self.variant['sg_asset_type'], 'Environment')
        self.assertEquals(self.variant['parents'], ['tree'])
    
    def tearDown(self) -> None:
        self.db.delete_asset_by_id(self.variant[id])

def run_tests():
    import time
    print('About to run tests!')
    time.sleep(1)
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__('ShotGridDatabaseTest'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('Done!')
    print('Test results:')
    print(f"Ran {result.testsRun} tests in {result.totalTime:.2f} seconds.")
    if result.wasSuccessful():
        print("All tests passed!")
    else:
        print("Some tests failed or encountered errors.")
    time.sleep(4)
    wait = input('Press enter to continue...')

run_tests()
