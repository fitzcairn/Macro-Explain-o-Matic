import sys
import random
import unittest

from macro.exceptions import *
from macro.logger import *
from macro.interpret.interpreter import get_test_mi
from macro.interpret.obj import InterpretedMacro
from macro.util import generate_test_function
from macro.parse.parser import MacroParser
from macro.lex.lexer import MacroCommandTokenizer


# Output?
DEBUG = False
UPDATE = False

class TestExceptions(unittest.TestCase):
    def setUp(self):
        self.mi     = get_test_mi(debug=DEBUG, lookup=False)
        self.lexer  = MacroCommandTokenizer(debug=DEBUG)
        self.parser = MacroParser(lexer_obj=self.lexer,
                                  debug=DEBUG)
        return
    
    # Lex/parse to trigger exceptions
    def macro_test(self, macro, correct=()):
        obj     = self.parser.lex_and_parse_macro(macro)
        int_obj = self.mi.interpret_macro(macro)


    def test_UserInputError(self):
        macro = ''''''
        try:
            self.macro_test(macro)
            self.fail("Did not raise UserInputError")
        except UserInputError, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_LexErrorNoMatchingRules(self):
        macro = '''/cast [[] test'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise LexErrorNoMatchingRules")
        except LexErrorNoMatchingRules, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_LexErrorRequiredMatchFailed(self):
        macro = '''bad_macro'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise LexErrorRequiredMatchFailed")
        except LexErrorRequiredMatchFailed, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorUnexpectedToken(self):
        macro = '''/cast [stance:1/]'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorUnexpectedToken")
        except ParseErrorUnexpectedToken, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorMultiTargetCondition(self):
        macro = '''/cast [target=fitz, target=brizzie]'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorMultiTargetCondition")
        except ParseErrorMultiTargetCondition, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorNoResetAllowed(self):
        macro = '''/cast reset=1 Test'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorNoResetAllowed")
        except ParseErrorNoResetAllowed, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorResetBeforeConditions(self):
        macro = '''/castsequence reset=1/2 [combat] Test'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorResetBeforeConditions")
        except ParseErrorResetBeforeConditions, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorNoTogglesAllowed(self):
        macro = '''#show !Fitz'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorNoTogglesAllowed")
        except ParseErrorNoTogglesAllowed, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorParamRequired(self):
        macro = '''/cast [combat] [stealth]'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorParamRequired")
        except ParseErrorParamRequired, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorWrongParams(self):
        macro = '''/cast 12 13'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorWrongParams")
        except ParseErrorWrongParams, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorNoArgsForOption(self):
        macro = '''/cast [stealth:1/2] Test'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorNoArgsForOption")
        except ParseErrorNoArgsForOption, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorReqArgsForOption(self):
        macro = '''/cast [button] Test'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorReqArgsForOption")
        except ParseErrorReqArgsForOption, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorMalformedCommand(self):
        macro = '''#show asdg [combat]'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorMalformedCommand")
        except ParseErrorMalformedCommand, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorMultipleVerbs(self):
        macro = '''#show /cast'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorMultipleVerbs")
        except ParseErrorMultipleVerbs, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorInsecureVerbNoCurrentTarget(self):
        macro = '''/tell %t Hello!"'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorInsecureVerbNoCurrentTarget")
        except ParseErrorInsecureVerbNoCurrentTarget, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorInsecureVerbReqTgt(self):
        macro = '''/w'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorInsecureVerbReqTgt")
        except ParseErrorInsecureVerbReqTgt, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorTargetTotem(self):
        macro = '''/petattack [target=Fire Resistance Totem]'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorTargetTotem")
        except LexErrorNoMatchingRules, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_InterpetErrorSingleUseCommandViolated(self):
        macro = '''/targetenemy\r\n/targetenemy'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise InterpetErrorSingleUseCommandViolated")
        except InterpetErrorSingleUseCommandViolated, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_InterpetErrorInvalidResetOption(self):
        macro = '''/castsequence reset=harm test,test'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise InterpetErrorInvalidResetOption")
        except InterpetErrorInvalidResetOption, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    # This seems dodgy. . . You should be able to name your
    # pet whatever you want.  TEST THIS.
    def test_InterpetErrorInvalidConditionArg(self):
        macro = '''/cast [pet:combat] Stuff'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise InterpetErrorInvalidConditionArg")
        except InterpetErrorInvalidConditionArg, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)

    def test_ParseErrorNonMatchingNegs(self):
        macro = u'''/castsequence [modifier:alt,nogroup,pet:Voidwalker/nopet:Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorNonMatchingNegs")
        except ParseErrorNonMatchingNegs, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    def test_ParseErrorNonMatchingOptionWords(self):
        macro = u'''/castsequence [modifier:alt,nogroup,pet:Voidwalker/stance:1] Searing Pain, Shadow Bolt, Shadow Bolt'''
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorNonMatchingOptionWords")
        except ParseErrorNonMatchingOptionWords, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)


    # Test follow-on targeting
    def test_ParseErrorInvalidTargetToken(self):
        macro = "/cast [target=Fitz-target-target-focus]Mark of the Wild"
        try:
            self.macro_test(macro)
            self.fail("Did not raise ParseErrorInvalidTargetToken")
        except ParseErrorInvalidTargetToken, instance:
            out = str(instance)
            if DEBUG: logging.debug(out)



        
if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExceptions)

    # Run just one test
    if DEBUG:
        suiteOne = unittest.TestSuite()
        suiteOne.addTest(TestExceptions("test_InterpetErrorInvalidConditionArg"))
        unittest.TextTestRunner(verbosity=2).run(suiteOne)
    else:
        unittest.TextTestRunner(verbosity=2).run(suite)


