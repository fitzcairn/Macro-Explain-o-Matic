# -*- coding: utf-8 -*-
# Full-engine lex and parse tests.

import sys
import random
import unittest
import inspect

from macro.exceptions import *
from macro.logger import *
from macro.interpret.interpreter import get_test_mi
from macro.interpret.obj import InterpretedMacro
from macro.util import generate_test_function
from macro.parse.parser import MacroParser
from macro.lex.lexer import MacroCommandTokenizer,GLOBAL_MACRO_TOKENIZER
from macro.lex.token import MacroToken


# Output?
DEBUG = False

# Update shortcut
UPDATE = False

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.DEBUG  = DEBUG
        self.parser = MacroParser(debug=DEBUG)
        self.mi = get_test_mi(debug=DEBUG, test=False)
        return

    #
    # --- INTERFACE ---
    #

    # All in one macro update.
    def macro_test_update(self, macro):    
        # Get the lexed version of the macro.
        self.parser.lex_macro(macro, 0)
        lex_c = "[%s]" % ", ".join([str(GLOBAL_MACRO_TOKENIZER[i].get_list()) for i in range(len(GLOBAL_MACRO_TOKENIZER))])

        # Get parse tree
        parse_c = self.parser.parse_macro()

        # Get interpretation
        int_c = self.mi.interpret_macro(macro).get_test_repr()

        # Print new function
        print "\n%s\n" % generate_test_function(macro, lex_c=lex_c, parse_c=parse_c, int_c=int_c, test_name=inspect.stack()[2][3])
        
        
    # All in one macro check
    def macro_test_check(self, macro, lex_correct, parse_correct, int_correct):
        # Save a reference to the global tokenizer
        lexer = GLOBAL_MACRO_TOKENIZER

        # Lex the macro.
        self.parser.lex_macro(macro, 0)
        if DEBUG: logger.debug(lexer.get_command_str())

        # Check the lex tokens
        self.__macro_token_check(macro, lex_correct, lexer)
        
        # Ok, if we're here, we pass the lexer test.  Now, look at
        # the parse tree.  Parse the macro.
        obj = self.parser.parse_macro()
        if DEBUG: logger.warning("\n\n%s\n\n" % str(obj))

        # Test
        self.__macro_parsetree_check(macro, parse_correct, obj)

        # Finally, check the intrepretation
        int_obj = self.mi.interpret_macro(macro).get_test_repr()
        self.__macro_interpretation_check(macro, int_correct, int_obj)
        


    # Abstraction to test/update functionality.
    def macro_test(self, macro, lex_correct=None, parse_correct=None, int_correct=""):
        # If updating, do that
        if UPDATE: return self.macro_test_update(macro)

        # Otherwise, do the test
        return self.macro_test_check(macro, lex_correct, parse_correct, int_correct)


    #
    # --- HELPERS ---
    #

    # Helper functions to do the testing
    def __macro_interpretation_check(self, macro, correct, int_obj):
        if DEBUG:
            logger.info(macro)
            logger.info(int_obj)
        self.assertEqual(correct,
                         int_obj,
                         "INTERPRETATION MISMATCH:\nMACRO:%s\nEXP: %s\nGOT: %s" %\
                         (macro,
                          correct,
                          int_obj))

    def __macro_token_check(self, macro, correct, lexer):
        for i in range(len(lexer)):
            self.assertEqual(correct[i],
                             lexer[i].get_list(),
                             "LEXER MISMATCH:\n  MACRO:%s\n  Correct: %s\n Returned: %s" % \
                             (macro,
                              correct[i],
                              lexer[i].get_list()))
            
    def __macro_parsetree_check(self, macro, correct, obj):
        # Quickie debug helper.
        def equal(a, b):
            if a != b:
                if DEBUG:    logger.error("%s not equal to %s" % (a,b))
                elif UPDATE: logger.warning("Need to update test.")
                else:        self.assertEqual(a,
                                              b,
                                              "PARSER MISMATCH:\n  Correct: %s\n Returned: %s" % (a,b))     

        # Quickie helper traverse comparison
        def traverse(a, b):
            if DEBUG:
                logger.debug(a)
                logger.debug(b)

            # Translate tokens.
            if isinstance(a, MacroToken): a = a.get_list()
            if isinstance(b, MacroToken): b = b.get_list()
                
            equal(type(a), type(b))
            if type(a) is list or type(a) is tuple:
                equal(len(a), len(b))
                for i in range(len(a)):
                    traverse(a[i], b[i])
            else:
                equal(a, b)

        if DEBUG: logger.warning("correct: %s" % str(correct))
        if DEBUG: logger.warning("obj: %s" % str(obj))
        traverse(correct, obj)


    #
    #  --- TESTS ---
    #


    def test_assist_empty_obj(self):
        macro = '''/assist Fitzcairn;'''
        lex_correct = [['COMMAND_VERB', 0, '/assist', 0, 7, True], ['PARAMETER', 1, 'Fitzcairn', 8, 17, False], ['ELSE', 2, ';', 17, 18, False]]
        parse_correct = (['COMMAND_VERB', 0, '/assist', 0, 7, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Fitzcairn', 8, 17, False])]), (['ELSE', 2, ';', 17, 18, False], None, None, None)])
        int_correct = [[None, 'Set your target to the target of Fitzcairn']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_assist_unit(self):
        macro = '''/assist Fitzcairn'''
        lex_correct = [['COMMAND_VERB', 0, '/assist', 0, 7, True], ['PARAMETER', 1, 'Fitzcairn', 8, 17, False]]
        parse_correct = (['COMMAND_VERB', 0, '/assist', 0, 7, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Fitzcairn', 8, 17, False])])])
        int_correct = [[None, 'Set your target to the target of Fitzcairn']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_bad_else(self):
        macro = '''/cast [combat] [mounted] Spell; [stealth] [] Spell2; Spell3'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['ENDIF', 3, ']', 13, 14, False], ['IF', 4, '[', 15, 16, False], ['OPTION_WORD', 5, 'mounted', 16, 23, False], ['ENDIF', 6, ']', 23, 24, False], ['PARAMETER', 7, 'Spell', 25, 30, False], ['ELSE', 8, ';', 30, 31, False], ['IF', 9, '[', 32, 33, False], ['OPTION_WORD', 10, 'stealth', 33, 40, False], ['ENDIF', 11, ']', 40, 41, False], ['IF', 12, '[', 42, 43, False], ['ENDIF', 13, ']', 43, 44, False], ['PARAMETER', 14, 'Spell2', 45, 51, False], ['ELSE', 15, ';', 51, 52, False], ['PARAMETER', 16, 'Spell3', 53, 59, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None)], ['ENDIF', 3, ']', 13, 14, False])), (None, (['IF', 4, '[', 15, 16, False], [(None, ['OPTION_WORD', 5, 'mounted', 16, 23, False], None, None)], ['ENDIF', 6, ']', 23, 24, False]))], None, [(None, ['PARAMETER', 7, 'Spell', 25, 30, False])]), (['ELSE', 8, ';', 30, 31, False], [(None, (['IF', 9, '[', 32, 33, False], [(None, ['OPTION_WORD', 10, 'stealth', 33, 40, False], None, None)], ['ENDIF', 11, ']', 40, 41, False])), (None, (['IF', 12, '[', 42, 43, False], None, ['ENDIF', 13, ']', 43, 44, False]))], None, [(None, ['PARAMETER', 14, 'Spell2', 45, 51, False])]), (['ELSE', 15, ';', 51, 52, False], None, None, [(None, ['PARAMETER', 16, 'Spell3', 53, 59, False])])])
        int_correct = [['If you are in combat then:', 'Cast Spell on the currently targeted unit'], ['Else, if you are mounted then:', 'Cast Spell on the currently targeted unit'], ['Else, if you are stealthed then:', 'Cast Spell2 on the currently targeted unit'], ['Otherwise:', 'Cast Spell2 on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_bad_else_command(self):
        macro = '''/cast Spell; [combat] Spell2;'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Spell', 6, 11, False], ['ELSE', 2, ';', 11, 12, False], ['IF', 3, '[', 13, 14, False], ['OPTION_WORD', 4, 'combat', 14, 20, False], ['ENDIF', 5, ']', 20, 21, False], ['PARAMETER', 6, 'Spell2', 22, 28, False], ['ELSE', 7, ';', 28, 29, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])]), (['ELSE', 2, ';', 11, 12, False], [(None, (['IF', 3, '[', 13, 14, False], [(None, ['OPTION_WORD', 4, 'combat', 14, 20, False], None, None)], ['ENDIF', 5, ']', 20, 21, False]))], None, [(None, ['PARAMETER', 6, 'Spell2', 22, 28, False])]), (['ELSE', 7, ';', 28, 29, False], None, None, None)])
        int_correct = [[None, 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_bag_equip(self):
        macro = '''/equip 0 12'''
        lex_correct = [['COMMAND_VERB', 0, '/equip', 0, 6, True], ['PARAMETER', 1, '0', 7, 8, True], ['PARAMETER', 2, '12', 9, 11, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equip', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, '0', 7, 8, True]), (None, ['PARAMETER', 2, '12', 9, 11, False])])])
        int_correct = [[None, 'Equip item in bag 0, bag slot 12 in its default slot']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_bag_equipslot(self):
        macro = '''/equipslot 16 0 12'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['PARAMETER', 1, '16', 11, 13, True], ['PARAMETER', 2, '0', 14, 15, True], ['PARAMETER', 3, '12', 16, 18, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, None, None, [(None, ['PARAMETER', 1, '16', 11, 13, True]), (None, ['PARAMETER', 2, '0', 14, 15, True]), (None, ['PARAMETER', 3, '12', 16, 18, False])])])
        int_correct = [[None, 'Equip item from bag 0, bag slot 12 as your main-hand weapon']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_bagid(self):
        macro = '''/use 15 16'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, '15', 5, 7, True], ['PARAMETER', 2, '16', 8, 10, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '15', 5, 7, True]), (None, ['PARAMETER', 2, '16', 8, 10, False])])])
        int_correct = [[None, 'Use item in bag number 15, bag slot number 16']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_caps_normalization(self):
        macro = '''/CAST [COMBAT] Sex'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['ENDIF', 3, ']', 13, 14, False], ['PARAMETER', 4, 'Sex', 15, 18, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None)], ['ENDIF', 3, ']', 13, 14, False]))], None, [(None, ['PARAMETER', 4, 'Sex', 15, 18, False])])])
        int_correct = [['If you are in combat then:', 'Cast Sex on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_cast_multiple(self):
        macro = '''/click Garbarage124Button4'''
        lex_correct = [['COMMAND_VERB', 0, '/click', 0, 6, True], ['PARAMETER', 1, 'Garbarage124Button4', 7, 26, False]]
        parse_correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Garbarage124Button4', 7, 26, False])])])
        int_correct = [[None, 'Automatically click button: Garbarage124Button4']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_changeactionbar(self):
        macro = '''/changeactionbar [combat] 2'''
        lex_correct = [['COMMAND_VERB', 0, '/changeactionbar', 0, 16, True], ['IF', 1, '[', 17, 18, False], ['OPTION_WORD', 2, 'combat', 18, 24, False], ['ENDIF', 3, ']', 24, 25, False], ['PARAMETER', 4, '2', 26, 27, False]]
        parse_correct = (['COMMAND_VERB', 0, '/changeactionbar', 0, 16, True], [(None, [(None, (['IF', 1, '[', 17, 18, False], [(None, ['OPTION_WORD', 2, 'combat', 18, 24, False], None, None)], ['ENDIF', 3, ']', 24, 25, False]))], None, [(None, ['PARAMETER', 4, '2', 26, 27, False])])])
        int_correct = [['If you are in combat then:', 'Change your active action bar to bar 2']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_click_cmd_one_button(self):
        macro = '''/click PetActionButton5'''
        lex_correct = [['COMMAND_VERB', 0, '/click', 0, 6, True], ['PARAMETER', 1, 'PetActionButton', 7, 22, False], ['PARAMETER', 2, '5', 22, 23, False]]
        parse_correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'PetActionButton', 7, 22, False]), (None, ['PARAMETER', 2, '5', 22, 23, False])])])
        int_correct = [[None, 'Automatically click button 5 on the pet bar']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_click_cmds(self):
        macro = '''/click PetActionButton5 LeftButton'''
        lex_correct = [['COMMAND_VERB', 0, '/click', 0, 6, True], ['PARAMETER', 1, 'PetActionButton', 7, 22, False], ['PARAMETER', 2, '5', 22, 23, True], ['PARAMETER', 3, 'LeftButton', 24, 34, False]]
        parse_correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'PetActionButton', 7, 22, False]), (None, ['PARAMETER', 2, '5', 22, 23, True]), (None, ['PARAMETER', 3, 'LeftButton', 24, 34, False])])])
        int_correct = [[None, 'Automatically click button 5 on the pet bar with the left mouse button']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_click_dialog_cmds(self):
        macro = '''/click StaticPopup1Button1'''
        lex_correct = [['COMMAND_VERB', 0, '/click', 0, 6, True], ['PARAMETER', 1, 'StaticPopup1Button1', 7, 26, False]]
        parse_correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'StaticPopup1Button1', 7, 26, False])])])
        int_correct = [[None, 'Automatically click button: StaticPopup1Button1']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_command(self):
        macro = '''/cast Spell'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Spell', 6, 11, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])])])
        int_correct = [[None, 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_condition(self):
        macro = '''/equip [combat] Sexy Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/equip', 0, 6, True], ['IF', 1, '[', 7, 8, False], ['OPTION_WORD', 2, 'combat', 8, 14, False], ['ENDIF', 3, ']', 14, 15, False], ['PARAMETER', 4, 'Sexy Dagger', 16, 27, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equip', 0, 6, True], [(None, [(None, (['IF', 1, '[', 7, 8, False], [(None, ['OPTION_WORD', 2, 'combat', 8, 14, False], None, None)], ['ENDIF', 3, ']', 14, 15, False]))], None, [(None, ['PARAMETER', 4, 'Sexy Dagger', 16, 27, False])])])
        int_correct = [['If you are in combat then:', 'Equip your Sexy Dagger in its default slot']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_condition_multi(self):
        macro = '''/cast [combat, help] Greater Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['AND', 3, ',', 13, 14, False], ['OPTION_WORD', 4, 'help', 15, 19, False], ['ENDIF', 5, ']', 19, 20, False], ['PARAMETER', 6, 'Greater Heal', 21, 33, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None), (None, ['OPTION_WORD', 4, 'help', 15, 19, False], None, None)], ['ENDIF', 5, ']', 19, 20, False]))], None, [(None, ['PARAMETER', 6, 'Greater Heal', 21, 33, False])])])
        int_correct = [['If you are in combat and the currently targeted unit is a friend then:', 'Cast Greater Heal on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_condition_multi_arg(self):
        macro = '''/cast [combat, button:1/2/3] Greater Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['AND', 3, ',', 13, 14, False], ['OPTION_WORD', 4, 'button', 15, 21, False], ['IS', 5, ':', 21, 22, False], ['OPTION_ARG', 6, '1', 22, 23, False], ['OR', 7, '/', 23, 24, False], ['OPTION_ARG', 8, '2', 24, 25, False], ['OR', 9, '/', 25, 26, False], ['OPTION_ARG', 10, '3', 26, 27, False], ['ENDIF', 11, ']', 27, 28, False], ['PARAMETER', 12, 'Greater Heal', 29, 41, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None), (None, ['OPTION_WORD', 4, 'button', 15, 21, False], ['IS', 5, ':', 21, 22, False], [['OPTION_ARG', 6, '1', 22, 23, False], ['OPTION_ARG', 8, '2', 24, 25, False], ['OPTION_ARG', 10, '3', 26, 27, False]])], ['ENDIF', 11, ']', 27, 28, False]))], None, [(None, ['PARAMETER', 12, 'Greater Heal', 29, 41, False])])])
        int_correct = [['If you are in combat and activated this macro with mouse button 1, mouse button 3, or mouse button 2 then:', 'Cast Greater Heal on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_condition_multi_empty_cond(self):
        macro = '''/cast [button:1/2/3, help] [ ] [nocombat] Flash of Light'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'button', 7, 13, False], ['IS', 3, ':', 13, 14, False], ['OPTION_ARG', 4, '1', 14, 15, False], ['OR', 5, '/', 15, 16, False], ['OPTION_ARG', 6, '2', 16, 17, False], ['OR', 7, '/', 17, 18, False], ['OPTION_ARG', 8, '3', 18, 19, False], ['AND', 9, ',', 19, 20, False], ['OPTION_WORD', 10, 'help', 21, 25, False], ['ENDIF', 11, ']', 25, 26, False], ['IF', 12, '[', 27, 28, False], ['ENDIF', 13, ']', 29, 30, False], ['IF', 14, '[', 31, 32, False], ['NOT', 15, 'no', 32, 34, False], ['OPTION_WORD', 16, 'combat', 34, 40, False], ['ENDIF', 17, ']', 40, 41, False], ['PARAMETER', 18, 'Flash of Light', 42, 56, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'button', 7, 13, False], ['IS', 3, ':', 13, 14, False], [['OPTION_ARG', 4, '1', 14, 15, False], ['OPTION_ARG', 6, '2', 16, 17, False], ['OPTION_ARG', 8, '3', 18, 19, False]]), (None, ['OPTION_WORD', 10, 'help', 21, 25, False], None, None)], ['ENDIF', 11, ']', 25, 26, False])), (None, (['IF', 12, '[', 27, 28, False], None, ['ENDIF', 13, ']', 29, 30, False])), (None, (['IF', 14, '[', 31, 32, False], [(['NOT', 15, 'no', 32, 34, False], ['OPTION_WORD', 16, 'combat', 34, 40, False], None, None)], ['ENDIF', 17, ']', 40, 41, False]))], None, [(None, ['PARAMETER', 18, 'Flash of Light', 42, 56, False])])])
        int_correct = [['If you activated this macro with mouse button 1, mouse button 3, or mouse button 2 and the currently targeted unit is a friend then:', 'Cast Flash of Light on the currently targeted unit'], ['Otherwise:', 'Cast Flash of Light on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_condition_multi_target(self):
        macro = '''/cast [target=mouseover, help] [nocombat] Flash of Light'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'mouseover', 14, 23, False], ['AND', 5, ',', 23, 24, False], ['OPTION_WORD', 6, 'help', 25, 29, False], ['ENDIF', 7, ']', 29, 30, False], ['IF', 8, '[', 31, 32, False], ['NOT', 9, 'no', 32, 34, False], ['OPTION_WORD', 10, 'combat', 34, 40, False], ['ENDIF', 11, ']', 40, 41, False], ['PARAMETER', 12, 'Flash of Light', 42, 56, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'help', 25, 29, False], None, None)], ['ENDIF', 7, ']', 29, 30, False])), (None, (['IF', 8, '[', 31, 32, False], [(['NOT', 9, 'no', 32, 34, False], ['OPTION_WORD', 10, 'combat', 34, 40, False], None, None)], ['ENDIF', 11, ']', 40, 41, False]))], None, [(None, ['PARAMETER', 12, 'Flash of Light', 42, 56, False])])])
        int_correct = [['If the unit your mouse is currently over is a friend then:', 'Cast Flash of Light on the unit your mouse is currently over'], ['Else, if you are not in combat then:', 'Cast Flash of Light on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_empty_command_obj(self):
        macro = '''/cast [combat] Spell 1;'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['ENDIF', 3, ']', 13, 14, False], ['PARAMETER', 4, 'Spell 1', 15, 22, False], ['ELSE', 5, ';', 22, 23, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None)], ['ENDIF', 3, ']', 13, 14, False]))], None, [(None, ['PARAMETER', 4, 'Spell 1', 15, 22, False])]), (['ELSE', 5, ';', 22, 23, False], None, None, None)])
        int_correct = [['If you are in combat then:', 'Cast Spell 1 on the currently targeted unit'], ['Otherwise:', 'Cast nothing on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_empty_conditions(self):
        macro = '''/cast [target=mouseover, help] [ ] Flash of Light'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'mouseover', 14, 23, False], ['AND', 5, ',', 23, 24, False], ['OPTION_WORD', 6, 'help', 25, 29, False], ['ENDIF', 7, ']', 29, 30, False], ['IF', 8, '[', 31, 32, False], ['ENDIF', 9, ']', 33, 34, False], ['PARAMETER', 10, 'Flash of Light', 35, 49, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'help', 25, 29, False], None, None)], ['ENDIF', 7, ']', 29, 30, False])), (None, (['IF', 8, '[', 31, 32, False], None, ['ENDIF', 9, ']', 33, 34, False]))], None, [(None, ['PARAMETER', 10, 'Flash of Light', 35, 49, False])])])
        int_correct = [['If the unit your mouse is currently over is a friend then:', 'Cast Flash of Light on the unit your mouse is currently over'], ['Otherwise:', 'Cast Flash of Light on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_empty_rank(self):
        macro = '''/cast Faerie Fire (Feral)()'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Faerie Fire (Feral)()', 6, 27, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Faerie Fire (Feral)()', 6, 27, False])])])
        int_correct = [[None, 'Cast Faerie Fire (Feral)() on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_equipset(self):
        macro = '''/equipset [spec:1]Healing;[spec:2]Boomkin'''
        lex_correct = [['COMMAND_VERB', 0, '/equipset', 0, 9, True], ['IF', 1, '[', 10, 11, False], ['OPTION_WORD', 2, 'spec', 11, 15, False], ['IS', 3, ':', 15, 16, False], ['OPTION_ARG', 4, '1', 16, 17, False], ['ENDIF', 5, ']', 17, 18, False], ['PARAMETER', 6, 'Healing', 18, 25, False], ['ELSE', 7, ';', 25, 26, False], ['IF', 8, '[', 26, 27, False], ['OPTION_WORD', 9, 'spec', 27, 31, False], ['IS', 10, ':', 31, 32, False], ['OPTION_ARG', 11, '2', 32, 33, False], ['ENDIF', 12, ']', 33, 34, False], ['PARAMETER', 13, 'Boomkin', 34, 41, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipset', 0, 9, True], [(None, [(None, (['IF', 1, '[', 10, 11, False], [(None, ['OPTION_WORD', 2, 'spec', 11, 15, False], ['IS', 3, ':', 15, 16, False], [['OPTION_ARG', 4, '1', 16, 17, False]])], ['ENDIF', 5, ']', 17, 18, False]))], None, [(None, ['PARAMETER', 6, 'Healing', 18, 25, False])]), (['ELSE', 7, ';', 25, 26, False], [(None, (['IF', 8, '[', 26, 27, False], [(None, ['OPTION_WORD', 9, 'spec', 27, 31, False], ['IS', 10, ':', 31, 32, False], [['OPTION_ARG', 11, '2', 32, 33, False]])], ['ENDIF', 12, ']', 33, 34, False]))], None, [(None, ['PARAMETER', 13, 'Boomkin', 34, 41, False])])])
        int_correct = [['If you have spec 1 active then:', "Equip equipment set 'Healing' via the Equipment Manager"], ['Else, if you have spec 2 active then:', "Equip equipment set 'Boomkin' via the Equipment Manager"]]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_equipslot(self):
        macro = '''/equipslot [combat] 14 Phat Dagger; [stealth] 16 Poop Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['OPTION_WORD', 2, 'combat', 12, 18, False], ['ENDIF', 3, ']', 18, 19, False], ['PARAMETER', 4, '14', 20, 22, True], ['PARAMETER', 5, 'Phat Dagger', 23, 34, False], ['ELSE', 6, ';', 34, 35, False], ['IF', 7, '[', 36, 37, False], ['OPTION_WORD', 8, 'stealth', 37, 44, False], ['ENDIF', 9, ']', 44, 45, False], ['PARAMETER', 10, '16', 46, 48, True], ['PARAMETER', 11, 'Poop Dagger', 49, 60, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'combat', 12, 18, False], None, None)], ['ENDIF', 3, ']', 18, 19, False]))], None, [(None, ['PARAMETER', 4, '14', 20, 22, True]), (None, ['PARAMETER', 5, 'Phat Dagger', 23, 34, False])]), (['ELSE', 6, ';', 34, 35, False], [(None, (['IF', 7, '[', 36, 37, False], [(None, ['OPTION_WORD', 8, 'stealth', 37, 44, False], None, None)], ['ENDIF', 9, ']', 44, 45, False]))], None, [(None, ['PARAMETER', 10, '16', 46, 48, True]), (None, ['PARAMETER', 11, 'Poop Dagger', 49, 60, False])])])
        int_correct = [['If you are in combat then:', 'Equip your Phat Dagger as your second trinket'], ['Else, if you are stealthed then:', 'Equip your Poop Dagger as your main-hand weapon']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_equipslot_command(self):
        macro = '''/equipslot [combat] 14 Phat Dagger; [nocombat] 16 Poop Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['OPTION_WORD', 2, 'combat', 12, 18, False], ['ENDIF', 3, ']', 18, 19, False], ['PARAMETER', 4, '14', 20, 22, True], ['PARAMETER', 5, 'Phat Dagger', 23, 34, False], ['ELSE', 6, ';', 34, 35, False], ['IF', 7, '[', 36, 37, False], ['NOT', 8, 'no', 37, 39, False], ['OPTION_WORD', 9, 'combat', 39, 45, False], ['ENDIF', 10, ']', 45, 46, False], ['PARAMETER', 11, '16', 47, 49, True], ['PARAMETER', 12, 'Poop Dagger', 50, 61, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'combat', 12, 18, False], None, None)], ['ENDIF', 3, ']', 18, 19, False]))], None, [(None, ['PARAMETER', 4, '14', 20, 22, True]), (None, ['PARAMETER', 5, 'Phat Dagger', 23, 34, False])]), (['ELSE', 6, ';', 34, 35, False], [(None, (['IF', 7, '[', 36, 37, False], [(['NOT', 8, 'no', 37, 39, False], ['OPTION_WORD', 9, 'combat', 39, 45, False], None, None)], ['ENDIF', 10, ']', 45, 46, False]))], None, [(None, ['PARAMETER', 11, '16', 47, 49, True]), (None, ['PARAMETER', 12, 'Poop Dagger', 50, 61, False])])])
        int_correct = [['If you are in combat then:', 'Equip your Phat Dagger as your second trinket'], ['Else, if you are not in combat then:', 'Equip your Poop Dagger as your main-hand weapon']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_equipslot_mouseover(self):
        macro = '''/equipslot [target=mouseover,nogroup] 16 Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['TARGET', 2, 'target', 12, 18, False], ['GETS', 3, '=', 18, 19, False], ['TARGET_OBJ', 4, 'mouseover', 19, 28, False], ['AND', 5, ',', 28, 29, False], ['NOT', 6, 'no', 29, 31, False], ['OPTION_WORD', 7, 'group', 31, 36, False], ['ENDIF', 8, ']', 36, 37, False], ['PARAMETER', 9, '16', 38, 40, True], ['PARAMETER', 10, 'Dagger', 41, 47, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, [((['TARGET', 2, 'target', 12, 18, False], ['GETS', 3, '=', 18, 19, False], [['TARGET_OBJ', 4, 'mouseover', 19, 28, False]]), (['IF', 1, '[', 11, 12, False], [(['NOT', 6, 'no', 29, 31, False], ['OPTION_WORD', 7, 'group', 31, 36, False], None, None)], ['ENDIF', 8, ']', 36, 37, False]))], None, [(None, ['PARAMETER', 9, '16', 38, 40, True]), (None, ['PARAMETER', 10, 'Dagger', 41, 47, False])])])
        int_correct = [['If you are not in a group then:', 'Equip your Dagger as your main-hand weapon']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_equipslot_num(self):
        macro = '''/equipslot 12 13 14'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['PARAMETER', 1, '12', 11, 13, True], ['PARAMETER', 2, '13', 14, 16, True], ['PARAMETER', 3, '14', 17, 19, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, None, None, [(None, ['PARAMETER', 1, '12', 11, 13, True]), (None, ['PARAMETER', 2, '13', 14, 16, True]), (None, ['PARAMETER', 3, '14', 17, 19, False])])])
        int_correct = [[None, 'Equip item from bag 13, bag slot 14 as your second ring']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_extra_verb(self):
        macro = '''/cast Spell; /cast [combat] Spell2;'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Spell', 6, 11, False], ['ELSE', 2, ';', 11, 12, False], ['COMMAND_VERB', 3, '/cast', 13, 18, True], ['IF', 4, '[', 19, 20, False], ['OPTION_WORD', 5, 'combat', 20, 26, False], ['ENDIF', 6, ']', 26, 27, False], ['PARAMETER', 7, 'Spell2', 28, 34, False], ['ELSE', 8, ';', 34, 35, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])]), (['ELSE', 2, ';', 11, 12, False], [(None, (['IF', 4, '[', 19, 20, False], [(None, ['OPTION_WORD', 5, 'combat', 20, 26, False], None, None)], ['ENDIF', 6, ']', 26, 27, False]))], None, [(None, ['PARAMETER', 7, 'Spell2', 28, 34, False])]), (['ELSE', 8, ';', 34, 35, False], None, None, None)])
        int_correct = [[None, 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_group_option_raid(self):
        macro = '''/cast [group:raid] Test'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'group', 7, 12, False], ['IS', 3, ':', 12, 13, False], ['OPTION_ARG', 4, 'raid', 13, 17, False], ['ENDIF', 5, ']', 17, 18, False], ['PARAMETER', 6, 'Test', 19, 23, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'group', 7, 12, False], ['IS', 3, ':', 12, 13, False], [['OPTION_ARG', 4, 'raid', 13, 17, False]])], ['ENDIF', 5, ']', 17, 18, False]))], None, [(None, ['PARAMETER', 6, 'Test', 19, 23, False])])])
        int_correct = [['If you are in a raid then:', 'Cast Test on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_insecure(self):
        macro = '''/s This is [] a test of say!'''
        lex_correct = [['COMMAND_VERB', 0, '/s', 0, 2, True], ['PARAMETER', 1, 'This is [] a test of say!', 3, 28, False]]
        parse_correct = (['COMMAND_VERB', 0, '/s', 0, 2, True], [(None, None, None, [(None, ['PARAMETER', 1, 'This is [] a test of say!', 3, 28, False])])])
        int_correct = [[None, 'Say "This is [] a test of say!"']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_insecure_command(self):
        macro = '''/say [combat] "Oh crap!"'''
        lex_correct = [['COMMAND_VERB', 0, '/say', 0, 4, True], ['PARAMETER', 1, '[combat] "Oh crap!"', 5, 24, False]]
        parse_correct = (['COMMAND_VERB', 0, '/say', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '[combat] "Oh crap!"', 5, 24, False])])])
        int_correct = [[None, 'Say "[combat] "Oh crap!""']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_insecure_command_not(self):
        macro = '''/say [combat] !"Oh crap!"'''
        lex_correct = [['COMMAND_VERB', 0, '/say', 0, 4, True], ['PARAMETER', 1, '[combat] !"Oh crap!"', 5, 25, False]]
        parse_correct = (['COMMAND_VERB', 0, '/say', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '[combat] !"Oh crap!"', 5, 25, False])])])
        int_correct = [[None, 'Say "[combat] !"Oh crap!""']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_key_unit_not_used(self):
        macro = '''/target [target=focus, dead] party1'''
        lex_correct = [['COMMAND_VERB', 0, '/target', 0, 7, True], ['IF', 1, '[', 8, 9, False], ['TARGET', 2, 'target', 9, 15, False], ['GETS', 3, '=', 15, 16, False], ['TARGET_OBJ', 4, 'focus', 16, 21, False], ['AND', 5, ',', 21, 22, False], ['OPTION_WORD', 6, 'dead', 23, 27, False], ['ENDIF', 7, ']', 27, 28, False], ['PARAMETER', 8, 'party1', 29, 35, False]]
        parse_correct = (['COMMAND_VERB', 0, '/target', 0, 7, True], [(None, [((['TARGET', 2, 'target', 9, 15, False], ['GETS', 3, '=', 15, 16, False], [['TARGET_OBJ', 4, 'focus', 16, 21, False]]), (['IF', 1, '[', 8, 9, False], [(None, ['OPTION_WORD', 6, 'dead', 23, 27, False], None, None)], ['ENDIF', 7, ']', 27, 28, False]))], None, [(None, ['PARAMETER', 8, 'party1', 29, 35, False])])])
        int_correct = [['If the unit saved as your focus target is dead then:', 'Set target to the unit saved as your focus target']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_key_unit_used(self):
        macro = '''/focus [target=focus, dead] [target=party1pet, noharm] Fitzcairn'''
        lex_correct = [['COMMAND_VERB', 0, '/focus', 0, 6, True], ['IF', 1, '[', 7, 8, False], ['TARGET', 2, 'target', 8, 14, False], ['GETS', 3, '=', 14, 15, False], ['TARGET_OBJ', 4, 'focus', 15, 20, False], ['AND', 5, ',', 20, 21, False], ['OPTION_WORD', 6, 'dead', 22, 26, False], ['ENDIF', 7, ']', 26, 27, False], ['IF', 8, '[', 28, 29, False], ['TARGET', 9, 'target', 29, 35, False], ['GETS', 10, '=', 35, 36, False], ['TARGET_OBJ', 11, 'party', 36, 41, False], ['OPTION_ARG', 12, '1', 41, 42, False], ['TARGET_OBJ', 13, 'pet', 42, 45, False], ['AND', 14, ',', 45, 46, False], ['NOT', 15, 'no', 47, 49, False], ['OPTION_WORD', 16, 'harm', 49, 53, False], ['ENDIF', 17, ']', 53, 54, False], ['PARAMETER', 18, 'Fitzcairn', 55, 64, False]]
        parse_correct = (['COMMAND_VERB', 0, '/focus', 0, 6, True], [(None, [((['TARGET', 2, 'target', 8, 14, False], ['GETS', 3, '=', 14, 15, False], [['TARGET_OBJ', 4, 'focus', 15, 20, False]]), (['IF', 1, '[', 7, 8, False], [(None, ['OPTION_WORD', 6, 'dead', 22, 26, False], None, None)], ['ENDIF', 7, ']', 26, 27, False])), ((['TARGET', 9, 'target', 29, 35, False], ['GETS', 10, '=', 35, 36, False], [['TARGET_OBJ', 11, 'party', 36, 41, False], ['OPTION_ARG', 12, '1', 41, 42, False], ['TARGET_OBJ', 13, 'pet', 42, 45, False]]), (['IF', 8, '[', 28, 29, False], [(['NOT', 15, 'no', 47, 49, False], ['OPTION_WORD', 16, 'harm', 49, 53, False], None, None)], ['ENDIF', 17, ']', 53, 54, False]))], None, [(None, ['PARAMETER', 18, 'Fitzcairn', 55, 64, False])])])
        int_correct = [['If the unit saved as your focus target is dead then:', 'Set your focus target to Fitzcairn'], ["Else, if party member 1's pet is not an enemy then:", "Set your focus target to party member 1's pet"]]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_key_units_focus(self):
        macro = '''/focus [target=party1, harm]'''
        lex_correct = [['COMMAND_VERB', 0, '/focus', 0, 6, True], ['IF', 1, '[', 7, 8, False], ['TARGET', 2, 'target', 8, 14, False], ['GETS', 3, '=', 14, 15, False], ['TARGET_OBJ', 4, 'party', 15, 20, False], ['OPTION_ARG', 5, '1', 20, 21, False], ['AND', 6, ',', 21, 22, False], ['OPTION_WORD', 7, 'harm', 23, 27, False], ['ENDIF', 8, ']', 27, 28, False]]
        parse_correct = (['COMMAND_VERB', 0, '/focus', 0, 6, True], [(None, [((['TARGET', 2, 'target', 8, 14, False], ['GETS', 3, '=', 14, 15, False], [['TARGET_OBJ', 4, 'party', 15, 20, False], ['OPTION_ARG', 5, '1', 20, 21, False]]), (['IF', 1, '[', 7, 8, False], [(None, ['OPTION_WORD', 7, 'harm', 23, 27, False], None, None)], ['ENDIF', 8, ']', 27, 28, False]))], None, None)])
        int_correct = [['If party member 1 is an enemy then:', 'Set your focus target to party member 1']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_lexer_normalize(self):
        macro = '''/cast   Flash                                Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Flash Heal', 6, 16, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Flash Heal', 6, 16, False])])])
        int_correct = [[None, 'Cast Flash Heal on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_lexer_simple(self):
        macro = '''/cast Flash Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Flash Heal', 6, 16, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Flash Heal', 6, 16, False])])])
        int_correct = [[None, 'Cast Flash Heal on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_metacommands(self):
        macro = '''#show Stealth'''
        lex_correct = [['META_COMMAND_VERB', 0, '#show', 0, 5, True], ['PARAMETER', 1, 'Stealth', 6, 13, False]]
        parse_correct = (['META_COMMAND_VERB', 0, '#show', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Stealth', 6, 13, False])])])
        int_correct = [[None, 'Show icon and cooldown for Stealth for this macro on the action bar']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_multi_cond_target(self):
        macro = '''/use [target=targettarget, harm] [target=mouseover, help, button:1/2/3] Item 1; [target=player, combat] Item 2'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['IF', 1, '[', 5, 6, False], ['TARGET', 2, 'target', 6, 12, False], ['GETS', 3, '=', 12, 13, False], ['TARGET_OBJ', 4, 'target', 13, 19, False], ['TARGET_OBJ', 5, 'target', 19, 25, False], ['AND', 6, ',', 25, 26, False], ['OPTION_WORD', 7, 'harm', 27, 31, False], ['ENDIF', 8, ']', 31, 32, False], ['IF', 9, '[', 33, 34, False], ['TARGET', 10, 'target', 34, 40, False], ['GETS', 11, '=', 40, 41, False], ['TARGET_OBJ', 12, 'mouseover', 41, 50, False], ['AND', 13, ',', 50, 51, False], ['OPTION_WORD', 14, 'help', 52, 56, False], ['AND', 15, ',', 56, 57, False], ['OPTION_WORD', 16, 'button', 58, 64, False], ['IS', 17, ':', 64, 65, False], ['OPTION_ARG', 18, '1', 65, 66, False], ['OR', 19, '/', 66, 67, False], ['OPTION_ARG', 20, '2', 67, 68, False], ['OR', 21, '/', 68, 69, False], ['OPTION_ARG', 22, '3', 69, 70, False], ['ENDIF', 23, ']', 70, 71, False], ['PARAMETER', 24, 'Item 1', 72, 78, False], ['ELSE', 25, ';', 78, 79, False], ['IF', 26, '[', 80, 81, False], ['TARGET', 27, 'target', 81, 87, False], ['GETS', 28, '=', 87, 88, False], ['TARGET_OBJ', 29, 'player', 88, 94, False], ['AND', 30, ',', 94, 95, False], ['OPTION_WORD', 31, 'combat', 96, 102, False], ['ENDIF', 32, ']', 102, 103, False], ['PARAMETER', 33, 'Item 2', 104, 110, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, [((['TARGET', 2, 'target', 6, 12, False], ['GETS', 3, '=', 12, 13, False], [['TARGET_OBJ', 4, 'target', 13, 19, False], ['TARGET_OBJ', 5, 'target', 19, 25, False]]), (['IF', 1, '[', 5, 6, False], [(None, ['OPTION_WORD', 7, 'harm', 27, 31, False], None, None)], ['ENDIF', 8, ']', 31, 32, False])), ((['TARGET', 10, 'target', 34, 40, False], ['GETS', 11, '=', 40, 41, False], [['TARGET_OBJ', 12, 'mouseover', 41, 50, False]]), (['IF', 9, '[', 33, 34, False], [(None, ['OPTION_WORD', 14, 'help', 52, 56, False], None, None), (None, ['OPTION_WORD', 16, 'button', 58, 64, False], ['IS', 17, ':', 64, 65, False], [['OPTION_ARG', 18, '1', 65, 66, False], ['OPTION_ARG', 20, '2', 67, 68, False], ['OPTION_ARG', 22, '3', 69, 70, False]])], ['ENDIF', 23, ']', 70, 71, False]))], None, [(None, ['PARAMETER', 24, 'Item 1', 72, 78, False])]), (['ELSE', 25, ';', 78, 79, False], [((['TARGET', 27, 'target', 81, 87, False], ['GETS', 28, '=', 87, 88, False], [['TARGET_OBJ', 29, 'player', 88, 94, False]]), (['IF', 26, '[', 80, 81, False], [(None, ['OPTION_WORD', 31, 'combat', 96, 102, False], None, None)], ['ENDIF', 32, ']', 102, 103, False]))], None, [(None, ['PARAMETER', 33, 'Item 2', 104, 110, False])])])
        int_correct = [["If the currently targeted unit's currently targeted unit is an enemy then:", 'Use your Item 1'], ['Else, if the unit your mouse is currently over is a friend and you activated this macro with mouse button 1, mouse button 3, or mouse button 2 then:', 'Use your Item 1'], ['Else, if you are in combat then:', 'Use your Item 2']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_multi_object(self):
        macro = '''/use [combat] [mounted] Item 1; [nocombat, nomounted] Item 2; Item 3'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['IF', 1, '[', 5, 6, False], ['OPTION_WORD', 2, 'combat', 6, 12, False], ['ENDIF', 3, ']', 12, 13, False], ['IF', 4, '[', 14, 15, False], ['OPTION_WORD', 5, 'mounted', 15, 22, False], ['ENDIF', 6, ']', 22, 23, False], ['PARAMETER', 7, 'Item 1', 24, 30, False], ['ELSE', 8, ';', 30, 31, False], ['IF', 9, '[', 32, 33, False], ['NOT', 10, 'no', 33, 35, False], ['OPTION_WORD', 11, 'combat', 35, 41, False], ['AND', 12, ',', 41, 42, False], ['NOT', 13, 'no', 43, 45, False], ['OPTION_WORD', 14, 'mounted', 45, 52, False], ['ENDIF', 15, ']', 52, 53, False], ['PARAMETER', 16, 'Item 2', 54, 60, False], ['ELSE', 17, ';', 60, 61, False], ['PARAMETER', 18, 'Item 3', 62, 68, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, [(None, (['IF', 1, '[', 5, 6, False], [(None, ['OPTION_WORD', 2, 'combat', 6, 12, False], None, None)], ['ENDIF', 3, ']', 12, 13, False])), (None, (['IF', 4, '[', 14, 15, False], [(None, ['OPTION_WORD', 5, 'mounted', 15, 22, False], None, None)], ['ENDIF', 6, ']', 22, 23, False]))], None, [(None, ['PARAMETER', 7, 'Item 1', 24, 30, False])]), (['ELSE', 8, ';', 30, 31, False], [(None, (['IF', 9, '[', 32, 33, False], [(['NOT', 10, 'no', 33, 35, False], ['OPTION_WORD', 11, 'combat', 35, 41, False], None, None), (['NOT', 13, 'no', 43, 45, False], ['OPTION_WORD', 14, 'mounted', 45, 52, False], None, None)], ['ENDIF', 15, ']', 52, 53, False]))], None, [(None, ['PARAMETER', 16, 'Item 2', 54, 60, False])]), (['ELSE', 17, ';', 60, 61, False], None, None, [(None, ['PARAMETER', 18, 'Item 3', 62, 68, False])])])
        int_correct = [['If you are in combat then:', 'Use your Item 1'], ['Else, if you are mounted then:', 'Use your Item 1'], ['Else, if you are not in combat and are not mounted then:', 'Use your Item 2'], ['Otherwise:', 'Use your Item 3']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_multi_target(self):
        macro = '''/cast [target=party1targettarget] Spell'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'party', 14, 19, False], ['OPTION_ARG', 5, '1', 19, 20, False], ['TARGET_OBJ', 6, 'target', 20, 26, False], ['TARGET_OBJ', 7, 'target', 26, 32, False], ['ENDIF', 8, ']', 32, 33, False], ['PARAMETER', 9, 'Spell', 34, 39, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'party', 14, 19, False], ['OPTION_ARG', 5, '1', 19, 20, False], ['TARGET_OBJ', 6, 'target', 20, 26, False], ['TARGET_OBJ', 7, 'target', 26, 32, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 8, ']', 32, 33, False]))], None, [(None, ['PARAMETER', 9, 'Spell', 34, 39, False])])])
        int_correct = [[None, "Cast Spell on party member 1's currently targeted unit's currently targeted unit"]]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_multiple_conditions(self):
        macro = '''/cast [help] [target=targettarget, help] [target=player] Flash Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'help', 7, 11, False], ['ENDIF', 3, ']', 11, 12, False], ['IF', 4, '[', 13, 14, False], ['TARGET', 5, 'target', 14, 20, False], ['GETS', 6, '=', 20, 21, False], ['TARGET_OBJ', 7, 'target', 21, 27, False], ['TARGET_OBJ', 8, 'target', 27, 33, False], ['AND', 9, ',', 33, 34, False], ['OPTION_WORD', 10, 'help', 35, 39, False], ['ENDIF', 11, ']', 39, 40, False], ['IF', 12, '[', 41, 42, False], ['TARGET', 13, 'target', 42, 48, False], ['GETS', 14, '=', 48, 49, False], ['TARGET_OBJ', 15, 'player', 49, 55, False], ['ENDIF', 16, ']', 55, 56, False], ['PARAMETER', 17, 'Flash Heal', 57, 67, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'help', 7, 11, False], None, None)], ['ENDIF', 3, ']', 11, 12, False])), ((['TARGET', 5, 'target', 14, 20, False], ['GETS', 6, '=', 20, 21, False], [['TARGET_OBJ', 7, 'target', 21, 27, False], ['TARGET_OBJ', 8, 'target', 27, 33, False]]), (['IF', 4, '[', 13, 14, False], [(None, ['OPTION_WORD', 10, 'help', 35, 39, False], None, None)], ['ENDIF', 11, ']', 39, 40, False])), ((['TARGET', 13, 'target', 42, 48, False], ['GETS', 14, '=', 48, 49, False], [['TARGET_OBJ', 15, 'player', 49, 55, False]]), (['IF', 12, '[', 41, 42, False], None, ['ENDIF', 16, ']', 55, 56, False]))], None, [(None, ['PARAMETER', 17, 'Flash Heal', 57, 67, False])])])
        int_correct = [['If the currently targeted unit is a friend then:', 'Cast Flash Heal on the currently targeted unit'], ["Else, if the currently targeted unit's currently targeted unit is a friend then:", "Cast Flash Heal on the currently targeted unit's currently targeted unit"], ['Otherwise:', 'Cast Flash Heal on you']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_no_params_empty_obj(self):
        macro = '''/assist;'''
        lex_correct = [['COMMAND_VERB', 0, '/assist', 0, 7, True], ['ELSE', 1, ';', 7, 8, False]]
        parse_correct = (['COMMAND_VERB', 0, '/assist', 0, 7, True], [(None, None, None, None), (['ELSE', 1, ';', 7, 8, False], None, None, None)])
        int_correct = [[None, 'Set your target to the target of the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_non_param_command(self):
        macro = '''/targetfriend [combat] [nocombat]'''
        lex_correct = [['COMMAND_VERB', 0, '/targetfriend', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['IF', 4, '[', 23, 24, False], ['NOT', 5, 'no', 24, 26, False], ['OPTION_WORD', 6, 'combat', 26, 32, False], ['ENDIF', 7, ']', 32, 33, False]]
        parse_correct = (['COMMAND_VERB', 0, '/targetfriend', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False])), (None, (['IF', 4, '[', 23, 24, False], [(['NOT', 5, 'no', 24, 26, False], ['OPTION_WORD', 6, 'combat', 26, 32, False], None, None)], ['ENDIF', 7, ']', 32, 33, False]))], None, None)])
        int_correct = [['If you are in combat then:', 'Target next visible friendly unit'], ['Else, if you are not in combat then:', 'Target next visible friendly unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_non_param_command_multi_objs(self):
        macro = '''/targetfriend [combat]; [nocombat]'''
        lex_correct = [['COMMAND_VERB', 0, '/targetfriend', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['ELSE', 4, ';', 22, 23, False], ['IF', 5, '[', 24, 25, False], ['NOT', 6, 'no', 25, 27, False], ['OPTION_WORD', 7, 'combat', 27, 33, False], ['ENDIF', 8, ']', 33, 34, False]]
        parse_correct = (['COMMAND_VERB', 0, '/targetfriend', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], None, None), (['ELSE', 4, ';', 22, 23, False], [(None, (['IF', 5, '[', 24, 25, False], [(['NOT', 6, 'no', 25, 27, False], ['OPTION_WORD', 7, 'combat', 27, 33, False], None, None)], ['ENDIF', 8, ']', 33, 34, False]))], None, None)])
        int_correct = [['If you are in combat then:', 'Target next visible friendly unit'], ['Else, if you are not in combat then:', 'Target next visible friendly unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_numeric_use(self):
        macro = '''/equipslot 16 Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['PARAMETER', 1, '16', 11, 13, True], ['PARAMETER', 2, 'Dagger', 14, 20, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, None, None, [(None, ['PARAMETER', 1, '16', 11, 13, True]), (None, ['PARAMETER', 2, 'Dagger', 14, 20, False])])])
        int_correct = [[None, 'Equip your Dagger as your main-hand weapon']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_option_args(self):
        macro = '''/userandom [stance:1/2 ,   nobutton:2/3/4, flyable, nomounted] Ebon Gryphon; [target=focus,nomounted] [] Black Battlestrider, Swift Green Mechanostrider'''
        lex_correct = [['COMMAND_VERB', 0, '/userandom', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['OPTION_WORD', 2, 'stance', 12, 18, False], ['IS', 3, ':', 18, 19, False], ['OPTION_ARG', 4, '1', 19, 20, False], ['OR', 5, '/', 20, 21, False], ['OPTION_ARG', 6, '2', 21, 22, False], ['AND', 7, ',', 23, 24, False], ['NOT', 8, 'no', 25, 27, False], ['OPTION_WORD', 9, 'button', 27, 33, False], ['IS', 10, ':', 33, 34, False], ['OPTION_ARG', 11, '2', 34, 35, False], ['OR', 12, '/', 35, 36, False], ['OPTION_ARG', 13, '3', 36, 37, False], ['OR', 14, '/', 37, 38, False], ['OPTION_ARG', 15, '4', 38, 39, False], ['AND', 16, ',', 39, 40, False], ['OPTION_WORD', 17, 'flyable', 41, 48, False], ['AND', 18, ',', 48, 49, False], ['NOT', 19, 'no', 50, 52, False], ['OPTION_WORD', 20, 'mounted', 52, 59, False], ['ENDIF', 21, ']', 59, 60, False], ['PARAMETER', 22, 'Ebon Gryphon', 61, 73, False], ['ELSE', 23, ';', 73, 74, False], ['IF', 24, '[', 75, 76, False], ['TARGET', 25, 'target', 76, 82, False], ['GETS', 26, '=', 82, 83, False], ['TARGET_OBJ', 27, 'focus', 83, 88, False], ['AND', 28, ',', 88, 89, False], ['NOT', 29, 'no', 89, 91, False], ['OPTION_WORD', 30, 'mounted', 91, 98, False], ['ENDIF', 31, ']', 98, 99, False], ['IF', 32, '[', 100, 101, False], ['ENDIF', 33, ']', 101, 102, False], ['PARAMETER', 34, 'Black Battlestrider', 103, 122, False], ['AND', 35, ',', 122, 123, False], ['PARAMETER', 36, 'Swift Green Mechanostrider', 124, 150, False]]
        parse_correct = (['COMMAND_VERB', 0, '/userandom', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'stance', 12, 18, False], ['IS', 3, ':', 18, 19, False], [['OPTION_ARG', 4, '1', 19, 20, False], ['OPTION_ARG', 6, '2', 21, 22, False]]), (['NOT', 8, 'no', 25, 27, False], ['OPTION_WORD', 9, 'button', 27, 33, False], ['IS', 10, ':', 33, 34, False], [['OPTION_ARG', 11, '2', 34, 35, False], ['OPTION_ARG', 13, '3', 36, 37, False], ['OPTION_ARG', 15, '4', 38, 39, False]]), (None, ['OPTION_WORD', 17, 'flyable', 41, 48, False], None, None), (['NOT', 19, 'no', 50, 52, False], ['OPTION_WORD', 20, 'mounted', 52, 59, False], None, None)], ['ENDIF', 21, ']', 59, 60, False]))], None, [(None, ['PARAMETER', 22, 'Ebon Gryphon', 61, 73, False])]), (['ELSE', 23, ';', 73, 74, False], [((['TARGET', 25, 'target', 76, 82, False], ['GETS', 26, '=', 82, 83, False], [['TARGET_OBJ', 27, 'focus', 83, 88, False]]), (['IF', 24, '[', 75, 76, False], [(['NOT', 29, 'no', 89, 91, False], ['OPTION_WORD', 30, 'mounted', 91, 98, False], None, None)], ['ENDIF', 31, ']', 98, 99, False])), (None, (['IF', 32, '[', 100, 101, False], None, ['ENDIF', 33, ']', 101, 102, False]))], None, [(None, ['PARAMETER', 34, 'Black Battlestrider', 103, 122, False]), (None, ['PARAMETER', 36, 'Swift Green Mechanostrider', 124, 150, False])])])
        int_correct = [['If you are in stance 1 or 2, did not activate this macro with mouse button 3, mouse button 2, or mouse button 4, are in a zone allowing flying, and are not mounted then:', 'Use a randomly selected item from [ Ebon Gryphon ]'], ['Else, if you are not mounted then:', 'Use a randomly selected item from [ Black Battlestrider, Swift Green Mechanostrider ]'], ['Otherwise:', 'Use a randomly selected item from [ Black Battlestrider, Swift Green Mechanostrider ]']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_option_args_w_reset(self):
        macro = '''/castsequence [] reset=10/20/combat Battlestrider, Swift Green Mechanostrider'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['ENDIF', 2, ']', 15, 16, False], ['MODIFIER', 3, 'reset', 17, 22, False], ['GETS', 4, '=', 22, 23, False], ['OPTION_ARG', 5, '10', 23, 25, False], ['OR', 6, '/', 25, 26, False], ['OPTION_ARG', 7, '20', 26, 28, False], ['OR', 8, '/', 28, 29, False], ['OPTION_ARG', 9, 'combat', 29, 35, True], ['PARAMETER', 10, 'Battlestrider', 36, 49, False], ['AND', 11, ',', 49, 50, False], ['PARAMETER', 12, 'Swift Green Mechanostrider', 51, 77, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], None, ['ENDIF', 2, ']', 15, 16, False]))], (['MODIFIER', 3, 'reset', 17, 22, False], ['GETS', 4, '=', 22, 23, False], [['OPTION_ARG', 5, '10', 23, 25, False], ['OPTION_ARG', 7, '20', 26, 28, False], ['OPTION_ARG', 9, 'combat', 29, 35, True]]), [(None, ['PARAMETER', 10, 'Battlestrider', 36, 49, False]), (None, ['PARAMETER', 12, 'Swift Green Mechanostrider', 51, 77, False])])])
        int_correct = [[None, 'Cast the next spell in a sequence of [ Battlestrider on the currently targeted unit, Swift Green Mechanostrider on the currently targeted unit ] each time the macro is activated, resetting the sequence after 10 seconds, after 20 seconds, or if you leave combat']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_option_args_w_reset_broken(self):
        macro = '''/castsequence [] reset=10/20/harm Battlestrider, Swift Green Mechanostrider'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['ENDIF', 2, ']', 15, 16, False], ['MODIFIER', 3, 'reset', 17, 22, False], ['GETS', 4, '=', 22, 23, False], ['OPTION_ARG', 5, '10', 23, 25, False], ['OR', 6, '/', 25, 26, False], ['OPTION_ARG', 7, '20', 26, 28, False], ['OR', 8, '/', 28, 29, False], ['OPTION_ARG', 9, 'harm', 29, 33, True], ['PARAMETER', 10, 'Battlestrider', 34, 47, False], ['AND', 11, ',', 47, 48, False], ['PARAMETER', 12, 'Swift Green Mechanostrider', 49, 75, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], None, ['ENDIF', 2, ']', 15, 16, False]))], (['MODIFIER', 3, 'reset', 17, 22, False], ['GETS', 4, '=', 22, 23, False], [['OPTION_ARG', 5, '10', 23, 25, False], ['OPTION_ARG', 7, '20', 26, 28, False], ['OPTION_ARG', 9, 'harm', 29, 33, True]]), [(None, ['PARAMETER', 10, 'Battlestrider', 34, 47, False]), (None, ['PARAMETER', 12, 'Swift Green Mechanostrider', 49, 75, False])])])
        int_correct = [[None, 'The interpreter did not understand this macro command.  Mouseover\n      the error icons for feedback.']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_outfitter(self):
        macro = '''/outfitter OUTFIT'''
        lex_correct = [['COMMAND_VERB', 0, '/outfitter', 0, 10, True], ['PARAMETER', 1, 'OUTFIT', 11, 17, False]]
        parse_correct = (['COMMAND_VERB', 0, '/outfitter', 0, 10, True], [(None, None, None, [(None, ['PARAMETER', 1, 'OUTFIT', 11, 17, False])])])
        int_correct = [[None, '/outfitter OUTFIT']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_parameter_list(self):
        macro = '''/castsequence [combat] Spell 1, Spell 2, Spell 3'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['PARAMETER', 4, 'Spell 1', 23, 30, False], ['AND', 5, ',', 30, 31, False], ['PARAMETER', 6, 'Spell 2', 32, 39, False], ['AND', 7, ',', 39, 40, False], ['PARAMETER', 8, 'Spell 3', 41, 48, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], None, [(None, ['PARAMETER', 4, 'Spell 1', 23, 30, False]), (None, ['PARAMETER', 6, 'Spell 2', 32, 39, False]), (None, ['PARAMETER', 8, 'Spell 3', 41, 48, False])])])
        int_correct = [['If you are in combat then:', 'Cast the next spell in a sequence of [ Spell 1 on the currently targeted unit, Spell 2 on the currently targeted unit, Spell 3 on the currently targeted unit ] each time the macro is activated']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_parameter_list_toggled(self):
        macro = '''/castsequence [combat] Spell 1 (Rank 7), !Spell 2 (), !Spell 3'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['PARAMETER', 4, 'Spell 1 (Rank 7)', 23, 39, False], ['AND', 5, ',', 39, 40, False], ['TOGGLE', 6, '!', 41, 42, False], ['PARAMETER', 7, 'Spell 2 ()', 42, 52, False], ['AND', 8, ',', 52, 53, False], ['TOGGLE', 9, '!', 54, 55, False], ['PARAMETER', 10, 'Spell 3', 55, 62, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], None, [(None, ['PARAMETER', 4, 'Spell 1 (Rank 7)', 23, 39, False]), (['TOGGLE', 6, '!', 41, 42, False], ['PARAMETER', 7, 'Spell 2 ()', 42, 52, False]), (['TOGGLE', 9, '!', 54, 55, False], ['PARAMETER', 10, 'Spell 3', 55, 62, False])])])
        int_correct = [['If you are in combat then:', 'Cast the next spell in a sequence of [ Spell 1 (Rank 7) on the currently targeted unit, Spell 2 () (if Spell 2 () is not already active) on the currently targeted unit, Spell 3 (if Spell 3 is not already active) on the currently targeted unit ] each time the macro is activated']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_petfollow_target_pet(self):
        macro = '''/petfollow [pet:succubus]'''
        lex_correct = [['COMMAND_VERB', 0, '/petfollow', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['OPTION_WORD', 2, 'pet', 12, 15, False], ['IS', 3, ':', 15, 16, False], ['OPTION_ARG', 4, 'succubus', 16, 24, False], ['ENDIF', 5, ']', 24, 25, False]]
        parse_correct = (['COMMAND_VERB', 0, '/petfollow', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'pet', 12, 15, False], ['IS', 3, ':', 15, 16, False], [['OPTION_ARG', 4, 'succubus', 16, 24, False]])], ['ENDIF', 5, ']', 24, 25, False]))], None, None)])
        int_correct = [['If you have a pet named or of type succubus out then:', 'Turn on pet follow mode, canceling other modes']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_pettarget_cast(self):
        macro = '''/cast [combat,modifier:alt,harm,target=pettarget] [] Shadow Bolt'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['AND', 3, ',', 13, 14, False], ['OPTION_WORD', 4, 'modifier', 14, 22, False], ['IS', 5, ':', 22, 23, False], ['OPTION_ARG', 6, 'alt', 23, 26, False], ['AND', 7, ',', 26, 27, False], ['OPTION_WORD', 8, 'harm', 27, 31, False], ['AND', 9, ',', 31, 32, False], ['TARGET', 10, 'target', 32, 38, False], ['GETS', 11, '=', 38, 39, False], ['TARGET_OBJ', 12, 'pet', 39, 42, False], ['TARGET_OBJ', 13, 'target', 42, 48, False], ['ENDIF', 14, ']', 48, 49, False], ['IF', 15, '[', 50, 51, False], ['ENDIF', 16, ']', 51, 52, False], ['PARAMETER', 17, 'Shadow Bolt', 53, 64, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 10, 'target', 32, 38, False], ['GETS', 11, '=', 38, 39, False], [['TARGET_OBJ', 12, 'pet', 39, 42, False], ['TARGET_OBJ', 13, 'target', 42, 48, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None), (None, ['OPTION_WORD', 4, 'modifier', 14, 22, False], ['IS', 5, ':', 22, 23, False], [['OPTION_ARG', 6, 'alt', 23, 26, False]]), (None, ['OPTION_WORD', 8, 'harm', 27, 31, False], None, None)], ['ENDIF', 14, ']', 48, 49, False])), (None, (['IF', 15, '[', 50, 51, False], None, ['ENDIF', 16, ']', 51, 52, False]))], None, [(None, ['PARAMETER', 17, 'Shadow Bolt', 53, 64, False])])])
        int_correct = [["If you are in combat and were holding the alt key and your pet's currently targeted unit is an enemy then:", "Cast Shadow Bolt on your pet's currently targeted unit"], ['Otherwise:', 'Cast Shadow Bolt on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_phrase_target_string(self):
        macro = '''/cast [target=mouseover,help,nodead,exists][help,nodead][]Fluffy spell'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'mouseover', 14, 23, False], ['AND', 5, ',', 23, 24, False], ['OPTION_WORD', 6, 'help', 24, 28, False], ['AND', 7, ',', 28, 29, False], ['NOT', 8, 'no', 29, 31, False], ['OPTION_WORD', 9, 'dead', 31, 35, False], ['AND', 10, ',', 35, 36, False], ['OPTION_WORD', 11, 'exists', 36, 42, False], ['ENDIF', 12, ']', 42, 43, False], ['IF', 13, '[', 43, 44, False], ['OPTION_WORD', 14, 'help', 44, 48, False], ['AND', 15, ',', 48, 49, False], ['NOT', 16, 'no', 49, 51, False], ['OPTION_WORD', 17, 'dead', 51, 55, False], ['ENDIF', 18, ']', 55, 56, False], ['IF', 19, '[', 56, 57, False], ['ENDIF', 20, ']', 57, 58, False], ['PARAMETER', 21, 'Fluffy spell', 58, 70, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'help', 24, 28, False], None, None), (['NOT', 8, 'no', 29, 31, False], ['OPTION_WORD', 9, 'dead', 31, 35, False], None, None), (None, ['OPTION_WORD', 11, 'exists', 36, 42, False], None, None)], ['ENDIF', 12, ']', 42, 43, False])), (None, (['IF', 13, '[', 43, 44, False], [(None, ['OPTION_WORD', 14, 'help', 44, 48, False], None, None), (['NOT', 16, 'no', 49, 51, False], ['OPTION_WORD', 17, 'dead', 51, 55, False], None, None)], ['ENDIF', 18, ']', 55, 56, False])), (None, (['IF', 19, '[', 56, 57, False], None, ['ENDIF', 20, ']', 57, 58, False]))], None, [(None, ['PARAMETER', 21, 'Fluffy spell', 58, 70, False])])])
        int_correct = [['If the unit your mouse is currently over is a friend, is not dead, and exists then:', 'Cast Fluffy spell on the unit your mouse is currently over'], ['Else, if the currently targeted unit is a friend and is not dead then:', 'Cast Fluffy spell on the currently targeted unit'], ['Otherwise:', 'Cast Fluffy spell on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_real_macro(self):
        macro = '''/cast [equipped:Shields,stance:1/2] Shield Bash; [equipped:Shields] Defensive Stance; [stance:3] Pummel; Berserker Stance'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'equipped', 7, 15, False], ['IS', 3, ':', 15, 16, False], ['OPTION_ARG', 4, 'Shields', 16, 23, False], ['AND', 5, ',', 23, 24, False], ['OPTION_WORD', 6, 'stance', 24, 30, False], ['IS', 7, ':', 30, 31, False], ['OPTION_ARG', 8, '1', 31, 32, False], ['OR', 9, '/', 32, 33, False], ['OPTION_ARG', 10, '2', 33, 34, False], ['ENDIF', 11, ']', 34, 35, False], ['PARAMETER', 12, 'Shield Bash', 36, 47, False], ['ELSE', 13, ';', 47, 48, False], ['IF', 14, '[', 49, 50, False], ['OPTION_WORD', 15, 'equipped', 50, 58, False], ['IS', 16, ':', 58, 59, False], ['OPTION_ARG', 17, 'Shields', 59, 66, False], ['ENDIF', 18, ']', 66, 67, False], ['PARAMETER', 19, 'Defensive Stance', 68, 84, False], ['ELSE', 20, ';', 84, 85, False], ['IF', 21, '[', 86, 87, False], ['OPTION_WORD', 22, 'stance', 87, 93, False], ['IS', 23, ':', 93, 94, False], ['OPTION_ARG', 24, '3', 94, 95, False], ['ENDIF', 25, ']', 95, 96, False], ['PARAMETER', 26, 'Pummel', 97, 103, False], ['ELSE', 27, ';', 103, 104, False], ['PARAMETER', 28, 'Berserker Stance', 105, 121, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'equipped', 7, 15, False], ['IS', 3, ':', 15, 16, False], [['OPTION_ARG', 4, 'Shields', 16, 23, False]]), (None, ['OPTION_WORD', 6, 'stance', 24, 30, False], ['IS', 7, ':', 30, 31, False], [['OPTION_ARG', 8, '1', 31, 32, False], ['OPTION_ARG', 10, '2', 33, 34, False]])], ['ENDIF', 11, ']', 34, 35, False]))], None, [(None, ['PARAMETER', 12, 'Shield Bash', 36, 47, False])]), (['ELSE', 13, ';', 47, 48, False], [(None, (['IF', 14, '[', 49, 50, False], [(None, ['OPTION_WORD', 15, 'equipped', 50, 58, False], ['IS', 16, ':', 58, 59, False], [['OPTION_ARG', 17, 'Shields', 59, 66, False]])], ['ENDIF', 18, ']', 66, 67, False]))], None, [(None, ['PARAMETER', 19, 'Defensive Stance', 68, 84, False])]), (['ELSE', 20, ';', 84, 85, False], [(None, (['IF', 21, '[', 86, 87, False], [(None, ['OPTION_WORD', 22, 'stance', 87, 93, False], ['IS', 23, ':', 93, 94, False], [['OPTION_ARG', 24, '3', 94, 95, False]])], ['ENDIF', 25, ']', 95, 96, False]))], None, [(None, ['PARAMETER', 26, 'Pummel', 97, 103, False])]), (['ELSE', 27, ';', 103, 104, False], None, None, [(None, ['PARAMETER', 28, 'Berserker Stance', 105, 121, False])])])
        int_correct = [['If you have equipped item or itemtype Shields and are in stance 1 or 2 then:', 'Cast Shield Bash on the currently targeted unit'], ['Else, if you have equipped item or itemtype Shields then:', 'Cast Defensive Stance on the currently targeted unit'], ['Else, if you are in stance 3 then:', 'Cast Pummel on the currently targeted unit'], ['Otherwise:', 'Cast Berserker Stance on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_reset_after_conditions(self):
        macro = '''/castsequence [combat] reset=target Curse of Agony, Immolate, Corruption'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], ['OPTION_ARG', 6, 'target', 29, 35, True], ['PARAMETER', 7, 'Curse of Agony', 36, 50, False], ['AND', 8, ',', 50, 51, False], ['PARAMETER', 9, 'Immolate', 52, 60, False], ['AND', 10, ',', 60, 61, False], ['PARAMETER', 11, 'Corruption', 62, 72, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], (['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], [['OPTION_ARG', 6, 'target', 29, 35, True]]), [(None, ['PARAMETER', 7, 'Curse of Agony', 36, 50, False]), (None, ['PARAMETER', 9, 'Immolate', 52, 60, False]), (None, ['PARAMETER', 11, 'Corruption', 62, 72, False])])])
        int_correct = [['If you are in combat then:', 'Cast the next spell in a sequence of [ Curse of Agony on the currently targeted unit, Immolate on the currently targeted unit, Corruption on the currently targeted unit ] each time the macro is activated, resetting the sequence if you change targets']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_reset_before_conditions(self):
        macro = '''/castsequence [combat] reset=target Curse of Agony, Immolate, Corruption'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], ['OPTION_ARG', 6, 'target', 29, 35, True], ['PARAMETER', 7, 'Curse of Agony', 36, 50, False], ['AND', 8, ',', 50, 51, False], ['PARAMETER', 9, 'Immolate', 52, 60, False], ['AND', 10, ',', 60, 61, False], ['PARAMETER', 11, 'Corruption', 62, 72, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], (['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], [['OPTION_ARG', 6, 'target', 29, 35, True]]), [(None, ['PARAMETER', 7, 'Curse of Agony', 36, 50, False]), (None, ['PARAMETER', 9, 'Immolate', 52, 60, False]), (None, ['PARAMETER', 11, 'Corruption', 62, 72, False])])])
        int_correct = [['If you are in combat then:', 'Cast the next spell in a sequence of [ Curse of Agony on the currently targeted unit, Immolate on the currently targeted unit, Corruption on the currently targeted unit ] each time the macro is activated, resetting the sequence if you change targets']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_self_cast(self):
        macro = '''/cast Anger Management'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Anger Management', 6, 22, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Anger Management', 6, 22, False])])])
        int_correct = [[None, 'Cast Anger Management on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_serious_break(self):
        macro = '''#showtooltip Curse of Agony'''
        lex_correct = [['META_COMMAND_VERB', 0, '#showtooltip', 0, 12, True], ['PARAMETER', 1, 'Curse of Agony', 13, 27, False]]
        parse_correct = (['META_COMMAND_VERB', 0, '#showtooltip', 0, 12, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Curse of Agony', 13, 27, False])])])
        int_correct = [[None, 'Show tooltip, icon, and cooldown for Curse of Agony for this macro on the action bar']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_showtooltip(self):
        macro = '''#showtooltip [nomodifier:alt] attack; [modifier] Shoot (or Throw)'''
        lex_correct = [['META_COMMAND_VERB', 0, '#showtooltip', 0, 12, True], ['IF', 1, '[', 13, 14, False], ['NOT', 2, 'no', 14, 16, False], ['OPTION_WORD', 3, 'modifier', 16, 24, False], ['IS', 4, ':', 24, 25, False], ['OPTION_ARG', 5, 'alt', 25, 28, False], ['ENDIF', 6, ']', 28, 29, False], ['PARAMETER', 7, 'attack', 30, 36, False], ['ELSE', 8, ';', 36, 37, False], ['IF', 9, '[', 38, 39, False], ['OPTION_WORD', 10, 'modifier', 39, 47, False], ['ENDIF', 11, ']', 47, 48, False], ['PARAMETER', 12, 'Shoot (or Throw)', 49, 65, False]]
        parse_correct = (['META_COMMAND_VERB', 0, '#showtooltip', 0, 12, True], [(None, [(None, (['IF', 1, '[', 13, 14, False], [(['NOT', 2, 'no', 14, 16, False], ['OPTION_WORD', 3, 'modifier', 16, 24, False], ['IS', 4, ':', 24, 25, False], [['OPTION_ARG', 5, 'alt', 25, 28, False]])], ['ENDIF', 6, ']', 28, 29, False]))], None, [(None, ['PARAMETER', 7, 'attack', 30, 36, False])]), (['ELSE', 8, ';', 36, 37, False], [(None, (['IF', 9, '[', 38, 39, False], [(None, ['OPTION_WORD', 10, 'modifier', 39, 47, False], None, None)], ['ENDIF', 11, ']', 47, 48, False]))], None, [(None, ['PARAMETER', 12, 'Shoot (or Throw)', 49, 65, False])])])
        int_correct = [['If you were not holding the alt key then:', 'Show tooltip, icon, and cooldown for attack for this macro on the action bar'], ['Else, if you holding a modifier key then:', 'Show tooltip, icon, and cooldown for Shoot (or Throw) for this macro on the action bar']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_simple(self):
        macro = '''/cast Spell'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['PARAMETER', 1, 'Spell', 6, 11, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])])])
        int_correct = [[None, 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_simple_equipslot_command(self):
        macro = '''/equipslot [combat] 14 Phat Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/equipslot', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['OPTION_WORD', 2, 'combat', 12, 18, False], ['ENDIF', 3, ']', 18, 19, False], ['PARAMETER', 4, '14', 20, 22, True], ['PARAMETER', 5, 'Phat Dagger', 23, 34, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'combat', 12, 18, False], None, None)], ['ENDIF', 3, ']', 18, 19, False]))], None, [(None, ['PARAMETER', 4, '14', 20, 22, True]), (None, ['PARAMETER', 5, 'Phat Dagger', 23, 34, False])])])
        int_correct = [['If you are in combat then:', 'Equip your Phat Dagger as your second trinket']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_simple_opt_args(self):
        macro = '''/cast [stance:1/2/3, modifier:shift] Spell'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'stance', 7, 13, False], ['IS', 3, ':', 13, 14, False], ['OPTION_ARG', 4, '1', 14, 15, False], ['OR', 5, '/', 15, 16, False], ['OPTION_ARG', 6, '2', 16, 17, False], ['OR', 7, '/', 17, 18, False], ['OPTION_ARG', 8, '3', 18, 19, False], ['AND', 9, ',', 19, 20, False], ['OPTION_WORD', 10, 'modifier', 21, 29, False], ['IS', 11, ':', 29, 30, False], ['OPTION_ARG', 12, 'shift', 30, 35, False], ['ENDIF', 13, ']', 35, 36, False], ['PARAMETER', 14, 'Spell', 37, 42, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'stance', 7, 13, False], ['IS', 3, ':', 13, 14, False], [['OPTION_ARG', 4, '1', 14, 15, False], ['OPTION_ARG', 6, '2', 16, 17, False], ['OPTION_ARG', 8, '3', 18, 19, False]]), (None, ['OPTION_WORD', 10, 'modifier', 21, 29, False], ['IS', 11, ':', 29, 30, False], [['OPTION_ARG', 12, 'shift', 30, 35, False]])], ['ENDIF', 13, ']', 35, 36, False]))], None, [(None, ['PARAMETER', 14, 'Spell', 37, 42, False])])])
        int_correct = [['If you are in stance 1, 3, or 2 and were holding the shift key then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_slotid(self):
        macro = '''/use 15'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, '15', 5, 7, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '15', 5, 7, False])])])
        int_correct = [[None, 'Use your equipped back']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_slotid_spaces(self):
        macro = '''/use 15                      17'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, '15', 5, 7, True], ['PARAMETER', 2, '17', 8, 10, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '15', 5, 7, True]), (None, ['PARAMETER', 2, '17', 8, 10, False])])])
        int_correct = [[None, 'Use item in bag number 15, bag slot number 17']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_spaces_in_targets(self):
        macro = '''/focus  [ mod : shift , no mod : ctrl ]  none ; [ target = focus , harm , no dead ]  focus ; [ harm , no dead ]  ; none'''
        lex_correct = [['COMMAND_VERB', 0, '/focus', 0, 6, True], ['IF', 1, '[', 7, 8, False], ['OPTION_WORD', 2, 'mod', 9, 12, False], ['IS', 3, ':', 13, 14, False], ['OPTION_ARG', 4, 'shift', 15, 20, False], ['AND', 5, ',', 21, 22, False], ['NOT', 6, 'no', 23, 25, False], ['OPTION_WORD', 7, 'mod', 26, 29, False], ['IS', 8, ':', 30, 31, False], ['OPTION_ARG', 9, 'ctrl', 32, 36, False], ['ENDIF', 10, ']', 37, 38, False], ['PARAMETER', 11, 'none', 39, 43, False], ['ELSE', 12, ';', 44, 45, False], ['IF', 13, '[', 46, 47, False], ['TARGET', 14, 'target', 48, 54, False], ['GETS', 15, '=', 55, 56, False], ['TARGET_OBJ', 16, 'focus', 57, 62, False], ['AND', 17, ',', 63, 64, False], ['OPTION_WORD', 18, 'harm', 65, 69, False], ['AND', 19, ',', 70, 71, False], ['NOT', 20, 'no', 72, 74, False], ['OPTION_WORD', 21, 'dead', 75, 79, False], ['ENDIF', 22, ']', 80, 81, False], ['PARAMETER', 23, 'focus', 82, 87, False], ['ELSE', 24, ';', 88, 89, False], ['IF', 25, '[', 90, 91, False], ['OPTION_WORD', 26, 'harm', 92, 96, False], ['AND', 27, ',', 97, 98, False], ['NOT', 28, 'no', 99, 101, False], ['OPTION_WORD', 29, 'dead', 102, 106, False], ['ENDIF', 30, ']', 107, 108, False], ['ELSE', 31, ';', 109, 110, False], ['PARAMETER', 32, 'none', 111, 115, False]]
        parse_correct = (['COMMAND_VERB', 0, '/focus', 0, 6, True], [(None, [(None, (['IF', 1, '[', 7, 8, False], [(None, ['OPTION_WORD', 2, 'mod', 9, 12, False], ['IS', 3, ':', 13, 14, False], [['OPTION_ARG', 4, 'shift', 15, 20, False]]), (['NOT', 6, 'no', 23, 25, False], ['OPTION_WORD', 7, 'mod', 26, 29, False], ['IS', 8, ':', 30, 31, False], [['OPTION_ARG', 9, 'ctrl', 32, 36, False]])], ['ENDIF', 10, ']', 37, 38, False]))], None, [(None, ['PARAMETER', 11, 'none', 39, 43, False])]), (['ELSE', 12, ';', 44, 45, False], [((['TARGET', 14, 'target', 48, 54, False], ['GETS', 15, '=', 55, 56, False], [['TARGET_OBJ', 16, 'focus', 57, 62, False]]), (['IF', 13, '[', 46, 47, False], [(None, ['OPTION_WORD', 18, 'harm', 65, 69, False], None, None), (['NOT', 20, 'no', 72, 74, False], ['OPTION_WORD', 21, 'dead', 75, 79, False], None, None)], ['ENDIF', 22, ']', 80, 81, False]))], None, [(None, ['PARAMETER', 23, 'focus', 82, 87, False])]), (['ELSE', 24, ';', 88, 89, False], [(None, (['IF', 25, '[', 90, 91, False], [(None, ['OPTION_WORD', 26, 'harm', 92, 96, False], None, None), (['NOT', 28, 'no', 99, 101, False], ['OPTION_WORD', 29, 'dead', 102, 106, False], None, None)], ['ENDIF', 30, ']', 107, 108, False]))], None, None), (['ELSE', 31, ';', 109, 110, False], None, None, [(None, ['PARAMETER', 32, 'none', 111, 115, False])])])
        int_correct = [['If you were holding the shift key and were not holding the control key then:', 'Set your focus target to no unit'], ['Else, if the unit saved as your focus target is an enemy and is not dead then:', 'Set your focus target to the unit saved as your focus target'], ['Else, if the currently targeted unit is an enemy and is not dead then:', 'Set your focus target to the currently targeted unit'], ['Otherwise:', 'Set your focus target to no unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_swapactionbar(self):
        macro = '''/swapactionbar [combat] 2 3'''
        lex_correct = [['COMMAND_VERB', 0, '/swapactionbar', 0, 14, True], ['IF', 1, '[', 15, 16, False], ['OPTION_WORD', 2, 'combat', 16, 22, False], ['ENDIF', 3, ']', 22, 23, False], ['PARAMETER', 4, '2', 24, 25, True], ['PARAMETER', 5, '3', 26, 27, False]]
        parse_correct = (['COMMAND_VERB', 0, '/swapactionbar', 0, 14, True], [(None, [(None, (['IF', 1, '[', 15, 16, False], [(None, ['OPTION_WORD', 2, 'combat', 16, 22, False], None, None)], ['ENDIF', 3, ']', 22, 23, False]))], None, [(None, ['PARAMETER', 4, '2', 24, 25, True]), (None, ['PARAMETER', 5, '3', 26, 27, False])])])
        int_correct = [['If you are in combat then:', 'Swap active action bar from bar 2 to bar 3 if bar 2 is active, otherwise switch to bar 2']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_target_args(self):
        macro = '''/cast [target=raidpet2] [] Spell 1'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'raidpet', 14, 21, False], ['OPTION_ARG', 5, '2', 21, 22, False], ['ENDIF', 6, ']', 22, 23, False], ['IF', 7, '[', 24, 25, False], ['ENDIF', 8, ']', 25, 26, False], ['PARAMETER', 9, 'Spell 1', 27, 34, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'raidpet', 14, 21, False], ['OPTION_ARG', 5, '2', 21, 22, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 6, ']', 22, 23, False])), (None, (['IF', 7, '[', 24, 25, False], None, ['ENDIF', 8, ']', 25, 26, False]))], None, [(None, ['PARAMETER', 9, 'Spell 1', 27, 34, False])])])
        int_correct = [[None, 'Cast Spell 1 on the pet of raid member 2']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_target_args_chain(self):
        macro = '''/cast [] [target=party2targettargettarget] Spell 1'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['ENDIF', 2, ']', 7, 8, False], ['IF', 3, '[', 9, 10, False], ['TARGET', 4, 'target', 10, 16, False], ['GETS', 5, '=', 16, 17, False], ['TARGET_OBJ', 6, 'party', 17, 22, False], ['OPTION_ARG', 7, '2', 22, 23, False], ['TARGET_OBJ', 8, 'target', 23, 29, False], ['TARGET_OBJ', 9, 'target', 29, 35, False], ['TARGET_OBJ', 10, 'target', 35, 41, False], ['ENDIF', 11, ']', 41, 42, False], ['PARAMETER', 12, 'Spell 1', 43, 50, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 2, ']', 7, 8, False])), ((['TARGET', 4, 'target', 10, 16, False], ['GETS', 5, '=', 16, 17, False], [['TARGET_OBJ', 6, 'party', 17, 22, False], ['OPTION_ARG', 7, '2', 22, 23, False], ['TARGET_OBJ', 8, 'target', 23, 29, False], ['TARGET_OBJ', 9, 'target', 29, 35, False], ['TARGET_OBJ', 10, 'target', 35, 41, False]]), (['IF', 3, '[', 9, 10, False], None, ['ENDIF', 11, ']', 41, 42, False]))], None, [(None, ['PARAMETER', 12, 'Spell 1', 43, 50, False])])])
        int_correct = [[None, 'Cast Spell 1 on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_target_chain(self):
        macro = '''/cast [target=playertargettargettarget] Spell 1'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'player', 14, 20, False], ['TARGET_OBJ', 5, 'target', 20, 26, False], ['TARGET_OBJ', 6, 'target', 26, 32, False], ['TARGET_OBJ', 7, 'target', 32, 38, False], ['ENDIF', 8, ']', 38, 39, False], ['PARAMETER', 9, 'Spell 1', 40, 47, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'player', 14, 20, False], ['TARGET_OBJ', 5, 'target', 20, 26, False], ['TARGET_OBJ', 6, 'target', 26, 32, False], ['TARGET_OBJ', 7, 'target', 32, 38, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 8, ']', 38, 39, False]))], None, [(None, ['PARAMETER', 9, 'Spell 1', 40, 47, False])])])
        int_correct = [[None, "Cast Spell 1 on your currently targeted unit's currently targeted unit's currently targeted unit"]]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_target_last_enemy(self):
        macro = '''/targetlastenemy'''
        lex_correct = [['COMMAND_VERB', 0, '/targetlastenemy', 0, 16, False]]
        parse_correct = (['COMMAND_VERB', 0, '/targetlastenemy', 0, 16, False], [(None, None, None, None)])
        int_correct = [[None, 'Target the last enemy unit you had targeted']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_target_party_reverse(self):
        macro = '''/targetparty 1'''
        lex_correct = [['COMMAND_VERB', 0, '/targetparty', 0, 12, True], ['PARAMETER', 1, '1', 13, 14, False]]
        parse_correct = (['COMMAND_VERB', 0, '/targetparty', 0, 12, True], [(None, None, None, [(None, ['PARAMETER', 1, '1', 13, 14, False])])])
        int_correct = [[None, 'Target next visible party member in reverse order']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_targeting(self):
        macro = '''/cast [target=party1,nodead] Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'party', 14, 19, False], ['OPTION_ARG', 5, '1', 19, 20, False], ['AND', 6, ',', 20, 21, False], ['NOT', 7, 'no', 21, 23, False], ['OPTION_WORD', 8, 'dead', 23, 27, False], ['ENDIF', 9, ']', 27, 28, False], ['PARAMETER', 10, 'Heal', 29, 33, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'party', 14, 19, False], ['OPTION_ARG', 5, '1', 19, 20, False]]), (['IF', 1, '[', 6, 7, False], [(['NOT', 7, 'no', 21, 23, False], ['OPTION_WORD', 8, 'dead', 23, 27, False], None, None)], ['ENDIF', 9, ']', 27, 28, False]))], None, [(None, ['PARAMETER', 10, 'Heal', 29, 33, False])])])
        int_correct = [['If party member 1 is not dead then:', 'Cast Heal on party member 1']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_targetlastenemy(self):
        macro = '''/targetlastenemy [combat]'''
        lex_correct = [['COMMAND_VERB', 0, '/targetlastenemy', 0, 16, True], ['IF', 1, '[', 17, 18, False], ['OPTION_WORD', 2, 'combat', 18, 24, False], ['ENDIF', 3, ']', 24, 25, False]]
        parse_correct = (['COMMAND_VERB', 0, '/targetlastenemy', 0, 16, True], [(None, [(None, (['IF', 1, '[', 17, 18, False], [(None, ['OPTION_WORD', 2, 'combat', 18, 24, False], None, None)], ['ENDIF', 3, ']', 24, 25, False]))], None, None)])
        int_correct = [['If you are in combat then:', 'Target the last enemy unit you had targeted']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_three_params(self):
        macro = '''/cast [target=mouseover,harm] Smite; [target=mouseover, help] Greater Heal; [] Greater Heal'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], ['TARGET_OBJ', 4, 'mouseover', 14, 23, False], ['AND', 5, ',', 23, 24, False], ['OPTION_WORD', 6, 'harm', 24, 28, False], ['ENDIF', 7, ']', 28, 29, False], ['PARAMETER', 8, 'Smite', 30, 35, False], ['ELSE', 9, ';', 35, 36, False], ['IF', 10, '[', 37, 38, False], ['TARGET', 11, 'target', 38, 44, False], ['GETS', 12, '=', 44, 45, False], ['TARGET_OBJ', 13, 'mouseover', 45, 54, False], ['AND', 14, ',', 54, 55, False], ['OPTION_WORD', 15, 'help', 56, 60, False], ['ENDIF', 16, ']', 60, 61, False], ['PARAMETER', 17, 'Greater Heal', 62, 74, False], ['ELSE', 18, ';', 74, 75, False], ['IF', 19, '[', 76, 77, False], ['ENDIF', 20, ']', 77, 78, False], ['PARAMETER', 21, 'Greater Heal', 79, 91, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'harm', 24, 28, False], None, None)], ['ENDIF', 7, ']', 28, 29, False]))], None, [(None, ['PARAMETER', 8, 'Smite', 30, 35, False])]), (['ELSE', 9, ';', 35, 36, False], [((['TARGET', 11, 'target', 38, 44, False], ['GETS', 12, '=', 44, 45, False], [['TARGET_OBJ', 13, 'mouseover', 45, 54, False]]), (['IF', 10, '[', 37, 38, False], [(None, ['OPTION_WORD', 15, 'help', 56, 60, False], None, None)], ['ENDIF', 16, ']', 60, 61, False]))], None, [(None, ['PARAMETER', 17, 'Greater Heal', 62, 74, False])]), (['ELSE', 18, ';', 74, 75, False], [(None, (['IF', 19, '[', 76, 77, False], None, ['ENDIF', 20, ']', 77, 78, False]))], None, [(None, ['PARAMETER', 21, 'Greater Heal', 79, 91, False])])])
        int_correct = [['If the unit your mouse is currently over is an enemy then:', 'Cast Smite on the unit your mouse is currently over'], ['Else, if the unit your mouse is currently over is a friend then:', 'Cast Greater Heal on the unit your mouse is currently over'], ['Otherwise:', 'Cast Greater Heal on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_toggled_list(self):
        macro = '''/castsequence [combat] reset=120 Spell 1, !Spell 2, !Spell 3'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['IF', 1, '[', 14, 15, False], ['OPTION_WORD', 2, 'combat', 15, 21, False], ['ENDIF', 3, ']', 21, 22, False], ['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], ['OPTION_ARG', 6, '120', 29, 32, True], ['PARAMETER', 7, 'Spell 1', 33, 40, False], ['AND', 8, ',', 40, 41, False], ['TOGGLE', 9, '!', 42, 43, False], ['PARAMETER', 10, 'Spell 2', 43, 50, False], ['AND', 11, ',', 50, 51, False], ['TOGGLE', 12, '!', 52, 53, False], ['PARAMETER', 13, 'Spell 3', 53, 60, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], (['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], [['OPTION_ARG', 6, '120', 29, 32, True]]), [(None, ['PARAMETER', 7, 'Spell 1', 33, 40, False]), (['TOGGLE', 9, '!', 42, 43, False], ['PARAMETER', 10, 'Spell 2', 43, 50, False]), (['TOGGLE', 12, '!', 52, 53, False], ['PARAMETER', 13, 'Spell 3', 53, 60, False])])])
        int_correct = [['If you are in combat then:', 'Cast the next spell in a sequence of [ Spell 1 on the currently targeted unit, Spell 2 (if Spell 2 is not already active) on the currently targeted unit, Spell 3 (if Spell 3 is not already active) on the currently targeted unit ] each time the macro is activated, resetting the sequence after 120 seconds']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_toggles(self):
        macro = '''/cast [combat] !Sex'''
        lex_correct = [['COMMAND_VERB', 0, '/cast', 0, 5, True], ['IF', 1, '[', 6, 7, False], ['OPTION_WORD', 2, 'combat', 7, 13, False], ['ENDIF', 3, ']', 13, 14, False], ['TOGGLE', 4, '!', 15, 16, False], ['PARAMETER', 5, 'Sex', 16, 19, False]]
        parse_correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None)], ['ENDIF', 3, ']', 13, 14, False]))], None, [(['TOGGLE', 4, '!', 15, 16, False], ['PARAMETER', 5, 'Sex', 16, 19, False])])])
        int_correct = [['If you are in combat then:', 'Cast Sex (if Sex is not already active) on the currently targeted unit']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_too_long(self):
        macro = '''/petfollow [pet:succubus]'''
        lex_correct = [['COMMAND_VERB', 0, '/petfollow', 0, 10, True], ['IF', 1, '[', 11, 12, False], ['OPTION_WORD', 2, 'pet', 12, 15, False], ['IS', 3, ':', 15, 16, False], ['OPTION_ARG', 4, 'succubus', 16, 24, False], ['ENDIF', 5, ']', 24, 25, False]]
        parse_correct = (['COMMAND_VERB', 0, '/petfollow', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'pet', 12, 15, False], ['IS', 3, ':', 15, 16, False], [['OPTION_ARG', 4, 'succubus', 16, 24, False]])], ['ENDIF', 5, ']', 24, 25, False]))], None, None)])
        int_correct = [['If you have a pet named or of type succubus out then:', 'Turn on pet follow mode, canceling other modes']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_use_item_slot(self):
        macro = '''/use 13 15'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, '13', 5, 7, True], ['PARAMETER', 2, '15', 8, 10, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '13', 5, 7, True]), (None, ['PARAMETER', 2, '15', 8, 10, False])])])
        int_correct = [[None, 'Use item in bag number 13, bag slot number 15']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_use_item_w_spaces(self):
        macro = '''/equip 10 Pound Mud Snapper'''
        lex_correct = [['COMMAND_VERB', 0, '/equip', 0, 6, True], ['PARAMETER', 1, '10 Pound Mud Snapper', 7, 27, False]]
        parse_correct = (['COMMAND_VERB', 0, '/equip', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, '10 Pound Mud Snapper', 7, 27, False])])])
        int_correct = [[None, 'Equip your 10 Pound Mud Snapper in its default slot']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_use_with_bag(self):
        macro = '''/use 13 14'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, '13', 5, 7, True], ['PARAMETER', 2, '14', 8, 10, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '13', 5, 7, True]), (None, ['PARAMETER', 2, '14', 8, 10, False])])])
        int_correct = [[None, 'Use item in bag number 13, bag slot number 14']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_use_with_item(self):
        macro = '''/use Swift Dagger'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, 'Swift Dagger', 5, 17, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Swift Dagger', 5, 17, False])])])
        int_correct = [[None, 'Use your Swift Dagger']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_use_with_slot(self):
        macro = '''/use 13'''
        lex_correct = [['COMMAND_VERB', 0, '/use', 0, 4, True], ['PARAMETER', 1, '13', 5, 7, False]]
        parse_correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '13', 5, 7, False])])])
        int_correct = [[None, 'Use your equipped first trinket']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_usetalents(self):
        macro = '''/usetalents [spec:1]2;[spec:2]1'''
        lex_correct = [['COMMAND_VERB', 0, '/usetalents', 0, 11, True], ['IF', 1, '[', 12, 13, False], ['OPTION_WORD', 2, 'spec', 13, 17, False], ['IS', 3, ':', 17, 18, False], ['OPTION_ARG', 4, '1', 18, 19, False], ['ENDIF', 5, ']', 19, 20, False], ['PARAMETER', 6, '2', 20, 21, True], ['ELSE', 7, ';', 21, 22, False], ['IF', 8, '[', 22, 23, False], ['OPTION_WORD', 9, 'spec', 23, 27, False], ['IS', 10, ':', 27, 28, False], ['OPTION_ARG', 11, '2', 28, 29, False], ['ENDIF', 12, ']', 29, 30, False], ['PARAMETER', 13, '1', 30, 31, False]]
        parse_correct = (['COMMAND_VERB', 0, '/usetalents', 0, 11, True], [(None, [(None, (['IF', 1, '[', 12, 13, False], [(None, ['OPTION_WORD', 2, 'spec', 13, 17, False], ['IS', 3, ':', 17, 18, False], [['OPTION_ARG', 4, '1', 18, 19, False]])], ['ENDIF', 5, ']', 19, 20, False]))], None, [(None, ['PARAMETER', 6, '2', 20, 21, True])]), (['ELSE', 7, ';', 21, 22, False], [(None, (['IF', 8, '[', 22, 23, False], [(None, ['OPTION_WORD', 9, 'spec', 23, 27, False], ['IS', 10, ':', 27, 28, False], [['OPTION_ARG', 11, '2', 28, 29, False]])], ['ENDIF', 12, ']', 29, 30, False]))], None, [(None, ['PARAMETER', 13, '1', 30, 31, False])])])
        int_correct = [['If you have spec 1 active then:', 'Activate talent set 2'], ['Else, if you have spec 2 active then:', 'Activate talent set 1']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)

    # Test broken harden command
    def test_helpme(self):
        macro = '''/helpme'''
        lex_correct = [['COMMAND_VERB', 0, '/helpme', 0, 7, False]]
        parse_correct = (['COMMAND_VERB', 0, '/helpme', 0, 7, False], [(None, None, None, None)])
        int_correct = [[None, 'Emote "You cry out for help!"']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)

    def test_sequence_w_empties_1(self):
        macro = '''/castsequence reset=combat ,,Potion of Wild Magic,'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], ['OPTION_ARG', 3, 'combat', 20, 26, True], ['PARAMETER', 4, '', 27, 27, False], ['AND', 5, ',', 27, 28, False], ['PARAMETER', 6, '', 28, 28, False], ['AND', 7, ',', 28, 29, False], ['PARAMETER', 8, 'Potion of Wild Magic', 29, 49, False], ['AND', 9, ',', 49, 50, False], ['PARAMETER', 10, '', 50, 50, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, None, (['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], [['OPTION_ARG', 3, 'combat', 20, 26, True]]), [(None, ['PARAMETER', 4, '', 27, 27, False]), (None, ['PARAMETER', 6, '', 28, 28, False]), (None, ['PARAMETER', 8, 'Potion of Wild Magic', 29, 49, False]), (None, ['PARAMETER', 10, '', 50, 50, False])])])
        int_correct = [[None, 'Cast the next spell in a sequence of [ nothing, nothing, Potion of Wild Magic on the currently targeted unit, nothing ] each time the macro is activated, resetting the sequence if you leave combat']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)


    def test_sequence_w_empties_2(self):
        macro = '''/castsequence reset=combat Spell,,'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], ['OPTION_ARG', 3, 'combat', 20, 26, True], ['PARAMETER', 4, 'Spell', 27, 32, False], ['AND', 5, ',', 32, 33, False], ['PARAMETER', 6, '', 33, 33, False], ['AND', 7, ',', 33, 34, False], ['PARAMETER', 8, '', 34, 34, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, None, (['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], [['OPTION_ARG', 3, 'combat', 20, 26, True]]), [(None, ['PARAMETER', 4, 'Spell', 27, 32, False]), (None, ['PARAMETER', 6, '', 33, 33, False]), (None, ['PARAMETER', 8, '', 34, 34, False])])])
        int_correct = [[None, 'Cast the next spell in a sequence of [ Spell on the currently targeted unit, nothing, nothing ] each time the macro is activated, resetting the sequence if you leave combat']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)

    def test_sequence_w_empties_3(self):
        macro = '''/castsequence reset=combat Spell,Spell,,'''
        lex_correct = [['COMMAND_VERB', 0, '/castsequence', 0, 13, True], ['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], ['OPTION_ARG', 3, 'combat', 20, 26, True], ['PARAMETER', 4, 'Spell', 27, 32, False], ['AND', 5, ',', 32, 33, False], ['PARAMETER', 6, 'Spell', 33, 38, False], ['AND', 7, ',', 38, 39, False], ['PARAMETER', 8, '', 39, 39, False], ['AND', 9, ',', 39, 40, False], ['PARAMETER', 10, '', 40, 40, False]]
        parse_correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, None, (['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], [['OPTION_ARG', 3, 'combat', 20, 26, True]]), [(None, ['PARAMETER', 4, 'Spell', 27, 32, False]), (None, ['PARAMETER', 6, 'Spell', 33, 38, False]), (None, ['PARAMETER', 8, '', 39, 39, False]), (None, ['PARAMETER', 10, '', 40, 40, False])])])
        int_correct = [[None, 'Cast the next spell in a sequence of [ Spell on the currently targeted unit, Spell on the currently targeted unit, nothing, nothing ] each time the macro is activated, resetting the sequence if you leave combat']]
        self.macro_test(macro, lex_correct, parse_correct, int_correct)

        
if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEngine)

    # Run just one test
    if DEBUG:
        suiteOne = unittest.TestSuite()
        suiteOne.addTest(TestEngine("test_target_chain"))
        unittest.TextTestRunner(verbosity=2).run(suiteOne)
    else:
        unittest.TextTestRunner(verbosity=2).run(suite)


