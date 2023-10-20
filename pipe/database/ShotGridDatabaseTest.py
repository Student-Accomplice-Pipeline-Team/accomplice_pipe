import unittest

from accomplice.sg_config import SG_CONFIG
from .ShotGridDatabase import ShotGridDatabase

# Run test in Studini with
# from database import ShotGridDatabaseTest

id_database = {
    'tree': 5307,
    'bicyclerack': 5108,
    'clipboard': 4721,
    'sign': 5312,
    'shopsign': 5345
}

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
    
    def test_get_asset_list(self):
        assets = self.db.get_asset_list()
        self.assertTrue(len(assets) > 0)
    
    def test_get_asset_id(self):
        # Originally I was going to use letty here, but by default the assets exclude the characters in their filters.
        asset_id = self.db.get_asset_id('clipboard')
        self.assertEqual(asset_id, id_database['clipboard'])
    
    def test_get_asset_id_sign(self):
        # Sign
        asset_id = self.db.get_asset_id('sign')
        self.assertEqual(asset_id, id_database['sign'])
    
    def test_get_asset_id_shopsign(self):
        # Shop Sign
        asset_id = self.db.get_asset_id('shopsign')
        self.assertEqual(asset_id, id_database['shopsign'])

    def test_get_asset_id_for_asset_with_subassets_1(self):
        # Tree
        asset_id = self.db.get_asset_id('tree')
        self.assertEqual(asset_id, id_database['tree'])

    def test_get_asset_id_for_asset_with_subassets_2(self):
        # Bicycle Rack
        asset_id = self.db.get_asset_id('bicyclerack')
        self.assertEqual(asset_id, id_database['bicyclerack'])
    
    def test_get_asset_list(self):
        asset_list = self.db.get_asset_list()
        self.assertTrue(len(asset_list) > 0)
        self.assertEqual(len(asset_list), len(set(asset_list)), "Duplicate values are: " + str([asset for asset in asset_list if asset_list.count(asset) > 1])) # Check for duplicates

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
        self.variant = self.db.create_variant(self.name, parent_name='tree')

    def test_create_test_subasset(self):
        self.assertIsNotNone(self.variant)
        self.assertTrue(type(self.variant) is dict)
        self.assertEquals(self.variant['code'], self.name)
        self.assertEquals(self.variant['sg_path'], '/environment/setdressing/tree')
        self.assertEquals(self.variant['sg_asset_type'], 'Environment')
        self.assertEquals(self.variant['parents'][0]['id'], id_database['tree'])
    
    def tearDown(self) -> None:
        self.db.delete_asset_by_id(self.variant['id'])

def run_tests():
    tests = unittest.TestSuite()
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(ShotGridDatabaseTest))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(AsynchronousShotGridDatabaseTest))
    runner = unittest.TextTestRunner(verbosity=3, failfast=True)
    runner.run(tests)


run_tests()
