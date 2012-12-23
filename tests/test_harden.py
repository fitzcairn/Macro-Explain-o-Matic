''' Test that reads from an input file and just runs the
interpreter on every macro in the file.

Exceptions are logged. '''


import sys
import random
import unittest
import logging
import traceback


from macro.exceptions import *
from macro.logger import *
from macro.interpret.interpreter import get_test_mi
    

# Add a handler to the logger to log to file.
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(module)s] %(levelname)s: %(message)s')
fh = logging.FileHandler("harden_output_log.txt", mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Where the errors should go to
error_file = open("harden_error_log.txt", 'w')


# Turning this on gives waaaaay too much output, be warned!
DEBUG=False


class TestParser(unittest.TestCase):
    def setUp(self):
        return

    # Run the test
    def do_test(self, macro):
        self.mi = get_test_mi(debug=DEBUG, test=False)
        logger.info("\n\n---------------------------------------------\n\n")
        logger.info("\n\n" + macro)
        self.mi.interpret_macro(macro)
        logger.info(self.mi)


    # Test cases for macros, an exception=fail
    def test_external_file(self):
        # Open and parse the file.
        f = open('tests/test_macros.txt', 'r')

        # Macros are seperated by blank lines.
        # Read in macro and test it.
        macro = []
        count = 0
        for line in f.readlines():
            #line = line.rstrip('\n')
            if not line.isspace():
                macro.append(line)
            elif len(macro) > 0:
                # Have a macro: run test.                
                try:
                    logger.error("Running macro %s. . ." % (count))
                    self.do_test(''.join(macro))
                except BaseException, instance:
                    error_file.write("\n\n\n" + ''.join(macro))
                    traceback.print_exc(12, error_file)
                    pass
                macro = []
                count = count + 1
            #if count > 2: break

if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
    unittest.TextTestRunner(verbosity=2).run(suite)


