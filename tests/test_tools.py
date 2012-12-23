''' Test the tools modules.  Requires network connection. '''

import sys
import random
import unittest


from tools.metadata.gcd import NO_GCD_SPELLS
from tools.wowdb.spells import *
from tools.wowhead.api import WowheadAPI
from tools.wowhead.spell_util import keep_or_toss


# Set up the logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(message)s')
logger = logging.getLogger()

# Output?
DEBUG = False
UPDATE = False

class TestInterpreter(unittest.TestCase):
    def setUp(self):\
        return

    # Make sure we can parse a spell.
    def test_parse_spell(self):
        correct = {'self': True, 'taught': True, 'gcd': True, 'spell_id': 34074, 'name': 'Aspect of the Viper'}
        test    = WowheadAPI("EN").getSpell(34074)
        self.assertEqual(correct,test)

    # Make sure we make the right decision amongst several spells.
    def test_keep_trainer(self):
        old = {'self': True, 'taught': True, 'gcd': True, 'spell_id': 34074, 'name': 'Aspect of the Viper'}
        new = {'self': True, 'gcd': True, 'spell_id': 34074, 'name': 'Aspect of the Viper'}
        self.assertEqual(keep_or_toss(new,old),False)

    def test_keep_rank(self):
        old = {'self': True, 'rank':1, 'taught': True, 'gcd': True, 'spell_id': 34074, 'name': 'Aspect of the Viper'}
        new = {'self': True, 'taught': True, 'gcd': True, 'spell_id': 34074, 'name': 'Aspect of the Viper'}
        self.assertEqual(keep_or_toss(new,old),False)

        
if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInterpreter)

    # Run just one test
    if DEBUG:
        suiteOne = unittest.TestSuite()
        suiteOne.addTest(TestInterpreter("test_parse_spell"))
        unittest.TextTestRunner(verbosity=2).run(suiteOne)
    else:
        unittest.TextTestRunner(verbosity=2).run(suite)


