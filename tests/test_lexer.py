import sys
import random
import unittest
from macro.logger import *
from macro.util   import *
from macro.lex.rules import *
from macro.lex.lexer import *


# Debug mode?
DEBUG = False
UPDATE = False

class TestLexer(unittest.TestCase):
    def setUp(self):
        return

    # Helpers to reduce repeated code
    def macro_test(self, macro, correct=[]):
        # For profiling, construct lexer every test        
        self.lexer = MacroCommandTokenizer(debug=DEBUG)

        self.lexer.reset(macro)
        if not UPDATE:
            if DEBUG:
                logger.info('')
                logger.info('\n' + macro)
                for i in range(len(self.lexer)):
                    logger.debug(str(self.lexer[i].get_list()))

                logger.debug('[' + ','.join(map(str, [o.get_list() for o in self.lexer])) + ']')

            # Test the token list
            for i in range(len(self.lexer)):
                self.assertEqual(correct[i], self.lexer[i].get_list())        
        else:
            lex_c = "[%s]" % ", ".join([str(self.lexer[i].get_list()) for i in range(len(self.lexer))])
            print "\n%s\n" % generate_test_function(macro, lex_c=lex_c)

    # Use with item id
    def test_use_itemid(self):
        macro = '''/use item:34483'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/use', 0, 4, True],
                       [u'PARAMETER', 1, u'item:34483', 5, 15, False]]
        self.macro_test(macro, lex_correct)
        
    # Equip with item id
    def test_equip_itemid(self):
        macro = '''/equip item:34483'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/equip', 0, 6, True],
                       [u'PARAMETER', 1, u'item:34483', 7, 17, False]]
        self.macro_test(macro, lex_correct)
        
    # Equipslot with item id
    def test_equipslot_itemid(self):    
        macro = '''/equipslot 12 item:34483'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True],
                       [u'PARAMETER', 1, u'12', 11, 13, True],
                       [u'PARAMETER', 2, u'item:34483', 14, 24, False]]
        self.macro_test(macro, lex_correct)

    # Emote with target
    def test_emote_with_target(self):
        macro = '''/spit Fitz'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/spit', 0, 5, True],
                       [u'TARGET_OBJ', 1, u'Fitz', 6, 10, False]]
        self.macro_test(macro, lex_correct)

    # Failure to find target
    def test_broken_insecure_target(self):
        macro = '''/tell "hi"'''
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)        

    # Testing insecure verbs with targets
    def test_insecure_with_target(self):
        macro = '''/tell Fitz Hello!"'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/tell', 0, 5, True],
                       [u'TARGET_OBJ', 1, u'Fitz', 6, 10, True],
                       [u'PARAMETER', 2, u'Hello!"', 11, 18, False]]
        self.macro_test(macro, lex_correct)
    def test_insecure_with_currtarget(self):
        macro = '''/e %t Hello!"'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/e', 0, 2, True],
                       [u'PARAMETER', 1, u'%t Hello!"', 3, 13, False]]
        self.macro_test(macro, lex_correct)
    def test_insecure_with_target_noparam(self):
        macro = '''/smile Fitz testing"'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/smile', 0, 6, True],
                       [u'TARGET_OBJ', 1, u'Fitz', 7, 11, True],
                       [u'PARAMETER', 2, u'testing"', 12, 20, False]]
        self.macro_test(macro, lex_correct)

    # Another broken case, this time with parameters
    def test_broken_equipslot_parameter(self):
        macro = '''/equipslot 11 Thunderfury, Blessed Blade of the Windseeker'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True], [u'PARAMETER', 1, u'11', 11, 13, True], [u'PARAMETER', 2, u'Thunderfury, Blessed Blade of the Windseeker', 14, 58, False]]
        self.macro_test(macro, lex_correct)


    # A broken testcase I found
    def test_group_option_multipet(self):
        macro = '''/castsequence [modifier:alt,nogroup,nopet:Voidwalker/Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/castsequence', 0, 13, True], [u'IF', 1, u'[', 14, 15, False], [u'OPTION_WORD', 2, u'modifier', 15, 23, False], [u'IS', 3, u':', 23, 24, False], [u'OPTION_ARG', 4, u'alt', 24, 27, False], [u'AND', 5, u',', 27, 28, False], [u'NOT', 6, u'no', 28, 30, False], [u'OPTION_WORD', 7, u'group', 30, 35, False], [u'AND', 8, u',', 35, 36, False], [u'NOT', 9, u'no', 36, 38, False], [u'OPTION_WORD', 10, u'pet', 38, 41, False], [u'IS', 11, u':', 41, 42, False], [u'OPTION_ARG', 12, u'Voidwalker', 42, 52, False], [u'OR', 13, u'/', 52, 53, False], [u'OPTION_ARG', 14, u'Felhunter', 53, 62, False], [u'ENDIF', 15, u']', 62, 63, False], [u'PARAMETER', 16, u'Searing Pain', 64, 76, False], [u'AND', 17, u',', 76, 77, False], [u'PARAMETER', 18, u'Shadow Bolt', 78, 89, False], [u'AND', 19, u',', 89, 90, False], [u'PARAMETER', 20, u'Shadow Bolt', 91, 102, False]]
        self.macro_test(macro, lex_correct)
        
    # From forums
    def test_group_option_raid(self):
        macro = '''/cast [group:raid] Test'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True], [u'IF', 1, u'[', 6, 7, False], [u'OPTION_WORD', 2, u'group', 7, 12, False], [u'IS', 3, u':', 12, 13, False], [u'OPTION_ARG', 4, u'raid', 13, 17, False], [u'ENDIF', 5, u']', 17, 18, False], [u'PARAMETER', 6, u'Test', 19, 23, False]]
        self.macro_test(macro, lex_correct)

    # Allowing spells to be empty.
    def test_cast_w_empty_spells(self):
        macro = '''/cast;'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True], [u'ELSE', 1, u';', 5, 6, False]]
        self.macro_test(macro, lex_correct)
    
    def test_castsequence_w_empty_spells(self):
        macro = '''/castsequence reset=combat ,,Potion of Wild Magic'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/castsequence', 0, 13, True], [u'MODIFIER', 1, u'reset', 14, 19, False], [u'GETS', 2, u'=', 19, 20, False], [u'OPTION_ARG', 3, u'combat', 20, 26, True], [u'PARAMETER', 4, u'', 27, 27, False], [u'AND', 5, u',', 27, 28, False], [u'PARAMETER', 6, u'', 28, 28, False], [u'AND', 7, u',', 28, 29, False], [u'PARAMETER', 8, u'Potion of Wild Magic', 29, 49, False]]
        self.macro_test(macro, lex_correct)
        
    # From the forums
    def test_petattack_target(self):
        macro = '''/petattack [target=pettarget,noexists]target'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/petattack', 0, 10, True],
                       [u'IF', 1, u'[', 11, 12, False],
                       [u'TARGET', 2, u'target', 12, 18, False],
                       [u'GETS', 3, u'=', 18, 19, False],
                       [u'TARGET_OBJ', 4, u'pet', 19, 22, False],
                       [u'TARGET_OBJ', 5, u'target', 22, 28, False],
                       [u'AND', 6, u',', 28, 29, False],
                       [u'NOT', 7, u'no', 29, 31, False],
                       [u'OPTION_WORD', 8, u'exists', 31, 37, False],
                       [u'ENDIF', 9, u']', 37, 38, False],
                       [u'PARAMETER', 10, u'target', 38, 44, False]]
        self.macro_test(macro, lex_correct)

    def test_broken_equipslot(self):
        macro = '''/equipslot 16 [combat] Dagger'''
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True], [u'PARAMETER', 1, u'16', 11, 13, True], [u'IF', 2, u'[', 14, 15, False], [u'OPTION_WORD', 3, u'combat', 15, 21, False], [u'ENDIF', 4, u']', 21, 22, False], [u'PARAMETER', 5, u'Dagger', 23, 29, False]]
        self.macro_test(macro, lex_correct)        
        
    def test_empty_multiline(self):
        macro = '''/cast [target=mouseover, harm] Blind; [target=focus] Kidney Shot
   
        
        '''
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'TARGET', 2, u'target', 7, 13, False],
                   [u'GETS', 3, u'=', 13, 14, False],
                   [u'TARGET_OBJ', 4, u'mouseover', 14, 23, False],
                   [u'AND', 5, u',', 23, 24, False],
                   [u'OPTION_WORD', 6, u'harm', 25, 29, False],
                   [u'ENDIF', 7, u']', 29, 30, False],
                   [u'PARAMETER', 8, u'Blind', 31, 36, False],
                   [u'ELSE', 9, u';', 36, 37, False],
                   [u'IF', 10, u'[', 38, 39, False],
                   [u'TARGET', 11, u'target', 39, 45, False],
                   [u'GETS', 12, u'=', 45, 46, False],
                   [u'TARGET_OBJ', 13, u'focus', 46, 51, False],
                   [u'ENDIF', 14, u']', 51, 52, False],
                   [u'PARAMETER', 15, u'Kidney Shot', 53, 64, False]]
        self.macro_test(macro, lex_correct)


    def test_equipslot(self):
        macro = "/equipslot [combat] 14 Phat Dagger; [stealth] 16 Poop Dagger"
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True],
                   [u'IF', 1, u'[', 11, 12, False],
                   [u'OPTION_WORD', 2, u'combat', 12, 18, False],
                   [u'ENDIF', 3, u']', 18, 19, False],
                   [u'PARAMETER', 4, u'14', 20, 22, True],
                   [u'PARAMETER', 5, u'Phat Dagger', 23, 34, False],
                   [u'ELSE', 6, u';', 34, 35, False],
                   [u'IF', 7, u'[', 36, 37, False],
                   [u'OPTION_WORD', 8, u'stealth', 37, 44, False],
                   [u'ENDIF', 9, u']', 44, 45, False],
                   [u'PARAMETER', 10, u'16', 46, 48, True],
                   [u'PARAMETER', 11, u'Poop Dagger', 49, 60, False]]
        self.macro_test(macro, lex_correct)


    def test_insecure_command(self):
        macro = '/say [combat] "Oh crap!"'
        lex_correct = [[u'COMMAND_VERB', 0, u'/say', 0, 4, True],
                   [u'PARAMETER', 1, u'[combat] "Oh crap!"', 5, 24, False]]
        self.macro_test(macro, lex_correct)


    def test_key_units(self):
        macro = "/focus [target=party1, harm]"
        lex_correct = [[u'COMMAND_VERB', 0, u'/focus', 0, 6, True],
                   [u'IF', 1, u'[', 7, 8, False],
                   [u'TARGET', 2, u'target', 8, 14, False],
                   [u'GETS', 3, u'=', 14, 15, False],
                   [u'TARGET_OBJ', 4, u'party', 15, 20, False],
                   [u'OPTION_ARG', 5, u'1', 20, 21, False],
                   [u'AND', 6, u',', 21, 22, False],
                   [u'OPTION_WORD', 7, u'harm', 23, 27, False],
                   [u'ENDIF', 8, u']', 27, 28, False]]
        self.macro_test(macro, lex_correct)


    def test_lexer_normalize(self):
        macro = "/cast   Flash                                Heal"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'PARAMETER', 1, u'Flash Heal', 6, 16, False]]
        self.macro_test(macro, lex_correct)


    def test_lexer_simple(self):
        macro = "/cast Flash Heal"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'PARAMETER', 1, u'Flash Heal', 6, 16, False]]
        self.macro_test(macro, lex_correct)


    def test_numeric_use(self):
        macro = "/equipslot 16 Dagger"
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True],
                   [u'PARAMETER', 1, u'16', 11, 13, True],
                   [u'PARAMETER', 2, u'Dagger', 14, 20, False]]
        self.macro_test(macro, lex_correct)


    def test_option_args(self):
        macro = "/userandom [stance:1/2 ,   nobutton:2/3/4, flyable, nomounted] Ebon Gryphon; [target=focus,nomounted] [] Black Battlestrider, Swift Green Mechanostrider"
        lex_correct = [[u'COMMAND_VERB', 0, u'/userandom', 0, 10, True],
                   [u'IF', 1, u'[', 11, 12, False],
                   [u'OPTION_WORD', 2, u'stance', 12, 18, False],
                   [u'IS', 3, u':', 18, 19, False],
                   [u'OPTION_ARG', 4, u'1', 19, 20, False],
                   [u'OR', 5, u'/', 20, 21, False],
                   [u'OPTION_ARG', 6, u'2', 21, 22, False],
                   [u'AND', 7, u',', 23, 24, False],
                   [u'NOT', 8, u'no', 25, 27, False],
                   [u'OPTION_WORD', 9, u'button', 27, 33, False],
                   [u'IS', 10, u':', 33, 34, False],
                   [u'OPTION_ARG', 11, u'2', 34, 35, False],
                   [u'OR', 12, u'/', 35, 36, False],
                   [u'OPTION_ARG', 13, u'3', 36, 37, False],
                   [u'OR', 14, u'/', 37, 38, False],
                   [u'OPTION_ARG', 15, u'4', 38, 39, False],
                   [u'AND', 16, u',', 39, 40, False],
                   [u'OPTION_WORD', 17, u'flyable', 41, 48, False],
                   [u'AND', 18, u',', 48, 49, False],
                   [u'NOT', 19, u'no', 50, 52, False],
                   [u'OPTION_WORD', 20, u'mounted', 52, 59, False],
                   [u'ENDIF', 21, u']', 59, 60, False],
                   [u'PARAMETER', 22, u'Ebon Gryphon', 61, 73, False],
                   [u'ELSE', 23, u';', 73, 74, False],
                   [u'IF', 24, u'[', 75, 76, False],
                   [u'TARGET', 25, u'target', 76, 82, False],
                   [u'GETS', 26, u'=', 82, 83, False],
                   [u'TARGET_OBJ', 27, u'focus', 83, 88, False],
                   [u'AND', 28, u',', 88, 89, False],
                   [u'NOT', 29, u'no', 89, 91, False],
                   [u'OPTION_WORD', 30, u'mounted', 91, 98, False],
                   [u'ENDIF', 31, u']', 98, 99, False],
                   [u'IF', 32, u'[', 100, 101, False],
                   [u'ENDIF', 33, u']', 101, 102, False],
                   [u'PARAMETER', 34, u'Black Battlestrider', 103, 122, False],
                   [u'AND', 35, u',', 122, 123, False],
                   [u'PARAMETER', 36, u'Swift Green Mechanostrider', 124, 150, False]]
        self.macro_test(macro, lex_correct)


    def test_parameter_list(self):
        macro = "/castsequence [combat] Spell 1, Spell 2, Spell 3"
        lex_correct = [[u'COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                   [u'IF', 1, u'[', 14, 15, False],
                   [u'OPTION_WORD', 2, u'combat', 15, 21, False],
                   [u'ENDIF', 3, u']', 21, 22, False],
                   [u'PARAMETER', 4, u'Spell 1', 23, 30, False],
                   [u'AND', 5, u',', 30, 31, False],
                   [u'PARAMETER', 6, u'Spell 2', 32, 39, False],
                   [u'AND', 7, u',', 39, 40, False],
                   [u'PARAMETER', 8, u'Spell 3', 41, 48, False]]
        self.macro_test(macro, lex_correct)


    def test_parameter_list_toggled(self):
        macro = "/castsequence [combat] Spell 1 (Rank 7), !Spell 2 (), !Spell 3"
        lex_correct = [[u'COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                   [u'IF', 1, u'[', 14, 15, False],
                   [u'OPTION_WORD', 2, u'combat', 15, 21, False],
                   [u'ENDIF', 3, u']', 21, 22, False],
                   [u'PARAMETER', 4, u'Spell 1 (Rank 7)', 23, 39, False],
                   [u'AND', 5, u',', 39, 40, False],
                   [u'TOGGLE', 6, u'!', 41, 42, False],
                   [u'PARAMETER', 7, u'Spell 2 ()', 42, 52, False],
                   [u'AND', 8, u',', 52, 53, False],
                   [u'TOGGLE', 9, u'!', 54, 55, False],
                   [u'PARAMETER', 10, u'Spell 3', 55, 62, False]]
        self.macro_test(macro, lex_correct)


    def test_reset_statement(self):
        macro = "/castsequence reset=10/harm [target=self, harm] [target=mouseover,harm,nomounted,nobutton:1/2] Spell 1, Other Spell, Some Item"
        lex_correct = [[u'COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                   [u'MODIFIER', 1, u'reset', 14, 19, False],
                   [u'GETS', 2, u'=', 19, 20, False],
                   [u'OPTION_ARG', 3, u'10', 20, 22, False],
                   [u'OR', 4, u'/', 22, 23, False],
                   [u'OPTION_ARG', 5, u'harm', 23, 27, True],
                   [u'IF', 6, u'[', 28, 29, False],
                   [u'TARGET', 7, u'target', 29, 35, False],
                   [u'GETS', 8, u'=', 35, 36, False],
                   [u'TARGET_OBJ', 9, u'self', 36, 40, False],
                   [u'AND', 10, u',', 40, 41, False],
                   [u'OPTION_WORD', 11, u'harm', 42, 46, False],
                   [u'ENDIF', 12, u']', 46, 47, False],
                   [u'IF', 13, u'[', 48, 49, False],
                   [u'TARGET', 14, u'target', 49, 55, False],
                   [u'GETS', 15, u'=', 55, 56, False],
                   [u'TARGET_OBJ', 16, u'mouseover', 56, 65, False],
                   [u'AND', 17, u',', 65, 66, False],
                   [u'OPTION_WORD', 18, u'harm', 66, 70, False],
                   [u'AND', 19, u',', 70, 71, False],
                   [u'NOT', 20, u'no', 71, 73, False],
                   [u'OPTION_WORD', 21, u'mounted', 73, 80, False],
                   [u'AND', 22, u',', 80, 81, False],
                   [u'NOT', 23, u'no', 81, 83, False],
                   [u'OPTION_WORD', 24, u'button', 83, 89, False],
                   [u'IS', 25, u':', 89, 90, False],
                   [u'OPTION_ARG', 26, u'1', 90, 91, False],
                   [u'OR', 27, u'/', 91, 92, False],
                   [u'OPTION_ARG', 28, u'2', 92, 93, False],
                   [u'ENDIF', 29, u']', 93, 94, False],
                   [u'PARAMETER', 30, u'Spell 1', 95, 102, False],
                   [u'AND', 31, u',', 102, 103, False],
                   [u'PARAMETER', 32, u'Other Spell', 104, 115, False],
                   [u'AND', 33, u',', 115, 116, False],
                   [u'PARAMETER', 34, u'Some Item', 117, 126, False]]
        self.macro_test(macro, lex_correct)


    def test_secure_with_no_conditions(self):
        macro = "/targetlastenemy"
        lex_correct = [[u'COMMAND_VERB', 0, u'/targetlastenemy', 0, 16, False]]
        self.macro_test(macro, lex_correct)


    def test_semicolon(self):
        macro = "/assist;"
        lex_correct = [[u'COMMAND_VERB', 0, u'/assist', 0, 7, True],
                   [u'ELSE', 1, u';', 7, 8, False]]
        self.macro_test(macro, lex_correct)

    def test_assist_empty_obj(self):
        macro = "/assist Fitzcairn;"
        lex_correct = [[u'COMMAND_VERB', 0, u'/assist', 0, 7, True],
                   [u'PARAMETER', 1, u'Fitzcairn', 8, 17, False],
                   [u'ELSE', 2, u';', 17, 18, False]]
        self.macro_test(macro, lex_correct)

    def test_simple_opt_args(self):
        macro = "/cast [stance:1/2/3, modifier:shift] Spell"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'OPTION_WORD', 2, u'stance', 7, 13, False],
                   [u'IS', 3, u':', 13, 14, False],
                   [u'OPTION_ARG', 4, u'1', 14, 15, False],
                   [u'OR', 5, u'/', 15, 16, False],
                   [u'OPTION_ARG', 6, u'2', 16, 17, False],
                   [u'OR', 7, u'/', 17, 18, False],
                   [u'OPTION_ARG', 8, u'3', 18, 19, False],
                   [u'AND', 9, u',', 19, 20, False],
                   [u'OPTION_WORD', 10, u'modifier', 21, 29, False],
                   [u'IS', 11, u':', 29, 30, False],
                   [u'OPTION_ARG', 12, u'shift', 30, 35, False],
                   [u'ENDIF', 13, u']', 35, 36, False],
                   [u'PARAMETER', 14, u'Spell', 37, 42, False]]
        self.macro_test(macro, lex_correct)


    def test_swapactionbar(self):
        macro = "/swapactionbar [combat] 2 3"
        lex_correct = [[u'COMMAND_VERB', 0, u'/swapactionbar', 0, 14, True],
                   [u'IF', 1, u'[', 15, 16, False],
                   [u'OPTION_WORD', 2, u'combat', 16, 22, False],
                   [u'ENDIF', 3, u']', 22, 23, False],
                   [u'PARAMETER', 4, u'2', 24, 25, True],
                   [u'PARAMETER', 5, u'3', 26, 27, False]]
        self.macro_test(macro, lex_correct)


    def test_swapactionbar_num_args(self):
        macro = "/swapactionbar 1 2 3 3"
        lex_correct = [[u'COMMAND_VERB', 0, u'/swapactionbar', 0, 14, True],
                   [u'PARAMETER', 1, u'1', 15, 16, True],
                   [u'PARAMETER', 2, u'2', 17, 18, True],
                   [u'PARAMETER', 3, u'3 3', 19, 22, False]]
        self.macro_test(macro, lex_correct)


    def test_target_args(self):
        macro = "/cast [target=partypet2, harm] Spell 1"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'TARGET', 2, u'target', 7, 13, False],
                   [u'GETS', 3, u'=', 13, 14, False],
                   [u'TARGET_OBJ', 4, u'partypet', 14, 22, False],
                   [u'OPTION_ARG', 5, u'2', 22, 23, False],
                   [u'AND', 6, u',', 23, 24, False],
                   [u'OPTION_WORD', 7, u'harm', 25, 29, False],
                   [u'ENDIF', 8, u']', 29, 30, False],
                   [u'PARAMETER', 9, u'Spell 1', 31, 38, False]]
        self.macro_test(macro, lex_correct)


    def test_target_chain(self):
        macro = "/cast [target=playertargettargettarget, harm] Spell 1"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'TARGET', 2, u'target', 7, 13, False],
                   [u'GETS', 3, u'=', 13, 14, False],
                   [u'TARGET_OBJ', 4, u'player', 14, 20, False],
                   [u'TARGET_OBJ', 5, u'target', 20, 26, False],
                   [u'TARGET_OBJ', 6, u'target', 26, 32, False],
                   [u'TARGET_OBJ', 7, u'target', 32, 38, False],
                   [u'AND', 8, u',', 38, 39, False],
                   [u'OPTION_WORD', 9, u'harm', 40, 44, False],
                   [u'ENDIF', 10, u']', 44, 45, False],
                   [u'PARAMETER', 11, u'Spell 1', 46, 53, False]]
        self.macro_test(macro, lex_correct)


    def test_target_chain_args(self):
        macro = "/cast [target=partypet2targettarget, harm] Spell 1"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'TARGET', 2, u'target', 7, 13, False],
                   [u'GETS', 3, u'=', 13, 14, False],
                   [u'TARGET_OBJ', 4, u'partypet', 14, 22, False],
                   [u'OPTION_ARG', 5, u'2', 22, 23, False],
                   [u'TARGET_OBJ', 6, u'target', 23, 29, False],
                   [u'TARGET_OBJ', 7, u'target', 29, 35, False],
                   [u'AND', 8, u',', 35, 36, False],
                   [u'OPTION_WORD', 9, u'harm', 37, 41, False],
                   [u'ENDIF', 10, u']', 41, 42, False],
                   [u'PARAMETER', 11, u'Spell 1', 43, 50, False]]
        self.macro_test(macro, lex_correct)


    def test_target_chain_unknown(self):
        macro = "/cast [target=Bobtargettarget, harm] Spell 1"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Bobtargettarget', 14, 29, False],['AND', 5, u',', 29, 30, False],['OPTION_WORD', 6, u'harm', 31, 35, False],['ENDIF', 7, u']', 35, 36, False],['PARAMETER', 8, u'Spell 1', 37, 44, False]]
        self.macro_test(macro, lex_correct)

    def test_target_chain_unknown2(self):
        macro = "/cast [target=Bob-target-target, harm] Spell 1"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Bob-', 14, 18, False],['TARGET_OBJ', 5, u'target-', 18, 25, False],['TARGET_OBJ', 6, u'target', 25, 31, False],['AND', 7, u',', 31, 32, False],['OPTION_WORD', 8, u'harm', 33, 37, False],['ENDIF', 9, u']', 37, 38, False],['PARAMETER', 10, u'Spell 1', 39, 46, False]]
        self.macro_test(macro, lex_correct)


    def test_target_party_reverse(self):
        macro = "/targetparty 1"
        lex_correct = [[u'COMMAND_VERB', 0, u'/targetparty', 0, 12, True],
                   [u'PARAMETER', 1, u'1', 13, 14, False]]
        self.macro_test(macro, lex_correct)


    def test_targetparsing(self):
        macro = "/userandom reset=10/20/harm [stance:1/2 ,   nobutton:2/3/4, flyable, nomounted] Ebon Gryphon; [target=focus,nomounted] [] Black Battlestrider, Swift Green Mechanostrider"
        lex_correct = [[u'COMMAND_VERB', 0, u'/userandom', 0, 10, True],
                   [u'MODIFIER', 1, u'reset', 11, 16, False],
                   [u'GETS', 2, u'=', 16, 17, False],
                   [u'OPTION_ARG', 3, u'10', 17, 19, False],
                   [u'OR', 4, u'/', 19, 20, False],
                   [u'OPTION_ARG', 5, u'20', 20, 22, False],
                   [u'OR', 6, u'/', 22, 23, False],
                   [u'OPTION_ARG', 7, u'harm', 23, 27, True],
                   [u'IF', 8, u'[', 28, 29, False],
                   [u'OPTION_WORD', 9, u'stance', 29, 35, False],
                   [u'IS', 10, u':', 35, 36, False],
                   [u'OPTION_ARG', 11, u'1', 36, 37, False],
                   [u'OR', 12, u'/', 37, 38, False],
                   [u'OPTION_ARG', 13, u'2', 38, 39, False],
                   [u'AND', 14, u',', 40, 41, False],
                   [u'NOT', 15, u'no', 42, 44, False],
                   [u'OPTION_WORD', 16, u'button', 44, 50, False],
                   [u'IS', 17, u':', 50, 51, False],
                   [u'OPTION_ARG', 18, u'2', 51, 52, False],
                   [u'OR', 19, u'/', 52, 53, False],
                   [u'OPTION_ARG', 20, u'3', 53, 54, False],
                   [u'OR', 21, u'/', 54, 55, False],
                   [u'OPTION_ARG', 22, u'4', 55, 56, False],
                   [u'AND', 23, u',', 56, 57, False],
                   [u'OPTION_WORD', 24, u'flyable', 58, 65, False],
                   [u'AND', 25, u',', 65, 66, False],
                   [u'NOT', 26, u'no', 67, 69, False],
                   [u'OPTION_WORD', 27, u'mounted', 69, 76, False],
                   [u'ENDIF', 28, u']', 76, 77, False],
                   [u'PARAMETER', 29, u'Ebon Gryphon', 78, 90, False],
                   [u'ELSE', 30, u';', 90, 91, False],
                   [u'IF', 31, u'[', 92, 93, False],
                   [u'TARGET', 32, u'target', 93, 99, False],
                   [u'GETS', 33, u'=', 99, 100, False],
                   [u'TARGET_OBJ', 34, u'focus', 100, 105, False],
                   [u'AND', 35, u',', 105, 106, False],
                   [u'NOT', 36, u'no', 106, 108, False],
                   [u'OPTION_WORD', 37, u'mounted', 108, 115, False],
                   [u'ENDIF', 38, u']', 115, 116, False],
                   [u'IF', 39, u'[', 117, 118, False],
                   [u'ENDIF', 40, u']', 118, 119, False],
                   [u'PARAMETER', 41, u'Black Battlestrider', 120, 139, False],
                   [u'AND', 42, u',', 139, 140, False],
                   [u'PARAMETER', 43, u'Swift Green Mechanostrider', 141, 167, False]]
        self.macro_test(macro, lex_correct)

    def test_toggles(self):
        macro = "/cast [combat] !Sex"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'OPTION_WORD', 2, u'combat', 7, 13, False],
                   [u'ENDIF', 3, u']', 13, 14, False],
                   [u'TOGGLE', 4, u'!', 15, 16, False],
                   [u'PARAMETER', 5, u'Sex', 16, 19, False]]
        self.macro_test(macro, lex_correct)

    # Test that broke the webpage--from wowwiki
    # This should actually NOT work, as pet:Voidwalker/pet:Felhunter ONLY
    # considers the first option as of 3.2
    def test_wowwiki_broken(self):
        macro = "/castsequence [modifier:alt,nogroup,pet:Voidwalker/pet:Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt"
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['IF', 1, u'[', 14, 15, False],
                       ['OPTION_WORD', 2, u'modifier', 15, 23, False],
                       ['IS', 3, u':', 23, 24, False],
                       ['OPTION_ARG', 4, u'alt', 24, 27, False],
                       ['AND', 5, u',', 27, 28, False],
                       ['NOT', 6, u'no', 28, 30, False],
                       ['OPTION_WORD', 7, u'group', 30, 35, False],
                       ['AND', 8, u',', 35, 36, False],
                       ['OPTION_WORD', 9, u'pet', 36, 39, False],
                       ['IS', 10, u':', 39, 40, False],
                       ['OPTION_ARG', 11, u'Voidwalker', 40, 50, False],
                       ['OR', 12, u'/', 50, 51, False],
                       ['OPTION_WORD', 13, u'pet', 51, 54, False],
                       ['IS', 14, u':', 54, 55, False],
                       ['OPTION_ARG', 15, u'Felhunter', 55, 64, False],
                       ['ENDIF', 16, u']', 64, 65, False],
                       ['PARAMETER', 17, u'Searing Pain', 66, 78, False],
                       ['AND', 18, u',', 78, 79, False],
                       ['PARAMETER', 19, u'Shadow Bolt', 80, 91, False],
                       ['AND', 20, u',', 91, 92, False],
                       ['PARAMETER', 21, u'Shadow Bolt', 93, 104, False]]
        self.macro_test(macro, lex_correct)

    # Unitid test
    def test_wowwiki_unitid(self):
        macro = "/petattack [target=Tremor Totem]"
        lex_correct = [[u'COMMAND_VERB', 0, u'/petattack', 0, 10, True],
                   [u'IF', 1, u'[', 11, 12, False],
                   [u'TARGET', 2, u'target', 12, 18, False],
                   [u'GETS', 3, u'=', 18, 19, False],
                   [u'TARGET_OBJ', 4, u'Tremor Totem', 19, 31, False],
                   [u'ENDIF', 5, u']', 31, 32, False]]
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)
        #self.macro_test(macro, lex_correct)

    # Another hardening case.
    def test_cast_multiple(self):
        macro = "/cast [equipped:Fishing Pole] Fishing; [equipped:Thrown] Throw; Shoot"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'OPTION_WORD', 2, u'equipped', 7, 15, False],
                   [u'IS', 3, u':', 15, 16, False],
                   [u'OPTION_ARG', 4, u'Fishing Pole', 16, 28, False],
                   [u'ENDIF', 5, u']', 28, 29, False],
                   [u'PARAMETER', 6, u'Fishing', 30, 37, False],
                   [u'ELSE', 7, u';', 37, 38, False],
                   [u'IF', 8, u'[', 39, 40, False],
                   [u'OPTION_WORD', 9, u'equipped', 40, 48, False],
                   [u'IS', 10, u':', 48, 49, False],
                   [u'OPTION_ARG', 11, u'Thrown', 49, 55, False],
                   [u'ENDIF', 12, u']', 55, 56, False],
                   [u'PARAMETER', 13, u'Throw', 57, 62, False],
                   [u'ELSE', 14, u';', 62, 63, False],
                   [u'PARAMETER', 15, u'Shoot', 64, 69, False]]
        self.macro_test(macro, lex_correct)

    # Bagid param test
    def test_bagid(self):
        macro = "/use 15 16"
        lex_correct = [[u'COMMAND_VERB', 0, u'/use', 0, 4, True],
                   [u'PARAMETER', 1, u'15', 5, 7, True],
                   [u'PARAMETER', 2, u'16', 8, 10, False]]
        self.macro_test(macro, lex_correct)


    # Slotid param test
    def test_slotid(self):
        macro = "/use 15"
        lex_correct = [[u'COMMAND_VERB', 0, u'/use', 0, 4, True],
                   [u'PARAMETER', 1, u'15', 5, 7, False]]
        self.macro_test(macro, lex_correct)


    # Bagid test with lots of spaces.
    def test_slotid_spaces(self):
        macro = "/use 15                      17"
        lex_correct = [[u'COMMAND_VERB', 0, u'/use', 0, 4, True],
                   [u'PARAMETER', 1, u'15', 5, 7, True],
                   [u'PARAMETER', 2, u'17', 8, 10, False]]
        self.macro_test(macro, lex_correct)

    def test_use_item_w_spaces(self):
        macro = "/equip 15 Pound Lobster"
        lex_correct = [[u'COMMAND_VERB', 0, u'/equip', 0, 6, True],
                   [u'PARAMETER', 1, u'15 Pound Lobster', 7, 23, False]]
        self.macro_test(macro, lex_correct)

    def test_broken_petfollow(self):
        macro = "/petfollow [pet:succubus]"
        lex_correct = [[u'COMMAND_VERB', 0, u'/petfollow', 0, 10, True],
                   [u'IF', 1, u'[', 11, 12, False],
                   [u'OPTION_WORD', 2, u'pet', 12, 15, False],
                   [u'IS', 3, u':', 15, 16, False],
                   [u'OPTION_ARG', 4, u'succubus', 16, 24, False],
                   [u'ENDIF', 5, u']', 24, 25, False]]
        self.macro_test(macro, lex_correct)

    def test_spaces_in_targets(self):
        macro = "/focus  [ mod : shift , no mod : ctrl ]  none ; [ target = focus , harm , no dead ]  focus ; [ harm , no dead ]  ; none"
        lex_correct = [[u'COMMAND_VERB', 0, u'/focus', 0, 6, True],
                   [u'IF', 1, u'[', 7, 8, False],
                   [u'OPTION_WORD', 2, u'mod', 9, 12, False],
                   [u'IS', 3, u':', 13, 14, False],
                   [u'OPTION_ARG', 4, u'shift', 15, 20, False],
                   [u'AND', 5, u',', 21, 22, False],
                   [u'NOT', 6, u'no', 23, 25, False],
                   [u'OPTION_WORD', 7, u'mod', 26, 29, False],
                   [u'IS', 8, u':', 30, 31, False],
                   [u'OPTION_ARG', 9, u'ctrl', 32, 36, False],
                   [u'ENDIF', 10, u']', 37, 38, False],
                   [u'PARAMETER', 11, u'none', 39, 43, False],
                   [u'ELSE', 12, u';', 44, 45, False],
                   [u'IF', 13, u'[', 46, 47, False],
                   [u'TARGET', 14, u'target', 48, 54, False],
                   [u'GETS', 15, u'=', 55, 56, False],
                   [u'TARGET_OBJ', 16, u'focus', 57, 62, False],
                   [u'AND', 17, u',', 63, 64, False],
                   [u'OPTION_WORD', 18, u'harm', 65, 69, False],
                   [u'AND', 19, u',', 70, 71, False],
                   [u'NOT', 20, u'no', 72, 74, False],
                   [u'OPTION_WORD', 21, u'dead', 75, 79, False],
                   [u'ENDIF', 22, u']', 80, 81, False],
                   [u'PARAMETER', 23, u'focus', 82, 87, False],
                   [u'ELSE', 24, u';', 88, 89, False],
                   [u'IF', 25, u'[', 90, 91, False],
                   [u'OPTION_WORD', 26, u'harm', 92, 96, False],
                   [u'AND', 27, u',', 97, 98, False],
                   [u'NOT', 28, u'no', 99, 101, False],
                   [u'OPTION_WORD', 29, u'dead', 102, 106, False],
                   [u'ENDIF', 30, u']', 107, 108, False],
                   [u'ELSE', 31, u';', 109, 110, False],
                   [u'PARAMETER', 32, u'none', 111, 115, False]]
        self.macro_test(macro, lex_correct)

    # Reset always follows conditions and is before the param
    def test_reset_before_conditions(self):
        macro = "/castsequence [combat] reset=target Curse of Agony, Immolate, Corruption"
        lex_correct = [[u'COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                   [u'IF', 1, u'[', 14, 15, False],
                   [u'OPTION_WORD', 2, u'combat', 15, 21, False],
                   [u'ENDIF', 3, u']', 21, 22, False],
                   [u'MODIFIER', 4, u'reset', 23, 28, False],
                   [u'GETS', 5, u'=', 28, 29, False],
                   [u'OPTION_ARG', 6, u'target', 29, 35, True],
                   [u'PARAMETER', 7, u'Curse of Agony', 36, 50, False],
                   [u'AND', 8, u',', 50, 51, False],
                   [u'PARAMETER', 9, u'Immolate', 52, 60, False],
                   [u'AND', 10, u',', 60, 61, False],
                   [u'PARAMETER', 11, u'Corruption', 62, 72, False]]
        self.macro_test(macro, lex_correct)


    # Another good spelling case
    def test_incorrect_spelling_arg(self):
        macro = "/cast [nomodifer:alt] Spell Lock"
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)
        
    # Currently breaking lexer, found by mdang.
    def test_incorrect_spelling(self):
        macro = "/cast [nomodifer] Spell Lock"
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)

    # Test caps
    def test_caps_normalization(self):
        macro = "/CAST [COMBAT] Sex"
        lex_correct = [[u'COMMAND_VERB', 0, u'/cast', 0, 5, True],
                   [u'IF', 1, u'[', 6, 7, False],
                   [u'OPTION_WORD', 2, u'combat', 7, 13, False],
                   [u'ENDIF', 3, u']', 13, 14, False],
                   [u'PARAMETER', 4, u'Sex', 15, 18, False]]
        self.macro_test(macro, lex_correct)


    # Test equipslot with bags
    def test_bag_equipslot(self):
        macro = "/equipslot 16 0 12"
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True],
                   [u'PARAMETER', 1, u'16', 11, 13, True],
                   [u'PARAMETER', 2, u'0', 14, 15, True],
                   [u'PARAMETER', 3, u'12', 16, 18, False]]
        self.macro_test(macro, lex_correct)


    # Test an unkown verb, say, outfitter
    def test_outfitter(self):
        macro = "/outfitter OUTFIT"
        lex_correct = [[u'COMMAND_VERB', 0, u'/outfitter', 0, 10, True],
                   [u'PARAMETER', 1, u'OUTFIT', 11, 17, False]]
        self.macro_test(macro, lex_correct)


    # Test broken command
    def test_error_broken_cmd(self):
        macro = "/use [pet=Succubus]Channel Souls"
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)
        macro = "/cast sasdf[adf"
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)


    # Test special click commands
    def test_click_cmds(self):
        macro = "/click PetActionButton5 LeftButton"
        lex_correct = [[u'COMMAND_VERB', 0, u'/click', 0, 6, True],
                   [u'PARAMETER', 1, u'PetActionButton', 7, 22, False],
                   [u'PARAMETER', 2, u'5', 22, 23, True],
                   [u'PARAMETER', 3, u'LeftButton', 24, 34, False]]
        self.macro_test(macro, lex_correct)
        macro = "/click PetActionButton5"
        lex_correct = [[u'COMMAND_VERB', 0, u'/click', 0, 6, True],
                   [u'PARAMETER', 1, u'PetActionButton', 7, 22, False],
                   [u'PARAMETER', 2, u'5', 22, 23, False]]
        self.macro_test(macro, lex_correct)


    # Test dialog click command
    def test_click_dialog_cmds(self):
        macro = "/click StaticPopup1Button1"
        lex_correct = [[u'COMMAND_VERB', 0, u'/click', 0, 6, True],
                       [u'PARAMETER', 1, u'StaticPopup1Button1', 7, 26, False]]
        self.macro_test(macro, lex_correct)


    # Test broken click command
    def test_click_broken_cmds(self):
        macro = "/click Garbarage124Button4"
        lex_correct = [[u'COMMAND_VERB', 0, u'/click', 0, 6, True],
                   [u'PARAMETER', 1, u'Garbarage124Button4', 7, 26, False]]
        self.macro_test(macro, lex_correct)


    # Make sure we handle equipslot InvSlot BagId slot correctly.
    def test_equipslot_num(self):
        macro = "/equipslot 12 13 14"
        lex_correct = [[u'COMMAND_VERB', 0, u'/equipslot', 0, 10, True],
                   [u'PARAMETER', 1, u'12', 11, 13, True],
                   [u'PARAMETER', 2, u'13', 14, 16, True],
                   [u'PARAMETER', 3, u'14', 17, 19, False]]
        self.macro_test(macro, lex_correct)


    # Test the new conditionals in 3.3
    def test_vehicleui(self):
        macro = u'''/cast [vehicleui] Tank Stuff'''
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True], ['IF', 1, u'[', 6, 7, False], ['OPTION_WORD', 2, u'vehicleui', 7, 16, False], ['ENDIF', 3, u']', 16, 17, False], ['PARAMETER', 4, u'Tank Stuff', 18, 28, False]]
        self.macro_test(macro, lex_correct)
    def test_unithasvehicleui(self):
        macro = u'''/cast [unithasvehicleui] Tank Stuff'''
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True], ['IF', 1, u'[', 6, 7, False], ['OPTION_WORD', 2, u'unithasvehicleui', 7, 23, False], ['ENDIF', 3, u']', 23, 24, False], ['PARAMETER', 4, u'Tank Stuff', 25, 35, False]]
        self.macro_test(macro, lex_correct)


    # Test out the new lexer rules for @target 3.3 changes.
    def test_target_alias(self):
        macro = u'''/cast [@focus] Test'''    
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True], ['IF', 1, u'[', 6, 7, False], ['TARGET', 2, u'@', 7, 8, False], ['TARGET_OBJ', 3, u'focus', 8, 13, False], ['ENDIF', 4, u']', 13, 14, False], ['PARAMETER', 5, u'Test', 15, 19, False]]
        self.macro_test(macro, lex_correct)

    # Broken command from site
    def test_broken_at_target(self):
        macro = u'''/cast [@focus unithasvehicleui]Blizzard'''
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro)

    # Another broken macro
    def test_broken_click(self):
        macro = u'''/click [nomod] ORLOpen OPieRaidSymbols;'''
        lex_correct = [['COMMAND_VERB', 0, u'/click', 0, 6, True],
                       ['IF', 1, u'[', 7, 8, False],
                       ['NOT', 2, u'no', 8, 10, False],
                       ['OPTION_WORD', 3, u'mod', 10, 13, False],
                       ['ENDIF', 4, u']', 13, 14, False],
                       ['PARAMETER', 5, u'ORLOpen OPieRaidSymbols', 15, 38, False],
                       ['ELSE', 6, u';', 38, 39, False]]
        self.macro_test(macro, lex_correct)

    # Another test that seems to be causing problems
    def test_broken_cast_target_pet(self):
        macro = u'''/cast [combat,modifier:alt,harm,target=pettarget] [] Shadow Bolt'''
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True], ['IF', 1, u'[', 6, 7, False], ['OPTION_WORD', 2, u'combat', 7, 13, False], ['AND', 3, u',', 13, 14, False], ['OPTION_WORD', 4, u'modifier', 14, 22, False], ['IS', 5, u':', 22, 23, False], ['OPTION_ARG', 6, u'alt', 23, 26, False], ['AND', 7, u',', 26, 27, False], ['OPTION_WORD', 8, u'harm', 27, 31, False], ['AND', 9, u',', 31, 32, False], ['TARGET', 10, u'target', 32, 38, False], ['GETS', 11, u'=', 38, 39, False], ['TARGET_OBJ', 12, u'pet', 39, 42, False], ['TARGET_OBJ', 13, u'target', 42, 48, False], ['ENDIF', 14, u']', 48, 49, False], ['IF', 15, u'[', 50, 51, False], ['ENDIF', 16, u']', 51, 52, False], ['PARAMETER', 17, u'Shadow Bolt', 53, 64, False]]
        self.macro_test(macro, lex_correct)

    def test_sequence_w_empties(self):    
        macro = u'''/castsequence reset=combat ,,Potion of Wild Magic,'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'', 27, 27, False],
                       ['AND', 5, u',', 27, 28, False],
                       ['PARAMETER', 6, u'', 28, 28, False],
                       ['AND', 7, u',', 28, 29, False],
                       ['PARAMETER', 8, u'Potion of Wild Magic', 29, 49, False],
                       ['AND', 9, u',', 49, 50, False],
                       ['PARAMETER', 10, u'', 50, 50, False],]
        self.macro_test(macro, lex_correct)

        # completely empty macro.
        macro = u'''/castsequence reset=combat ,,,'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'', 27, 27, False],
                       ['AND', 5, u',', 27, 28, False],
                       ['PARAMETER', 6, u'', 28, 28, False],
                       ['AND', 7, u',', 28, 29, False],
                       ['PARAMETER', 8, u'', 29, 29, False],
                       ['AND', 9, u',', 29, 30, False],
                       ['PARAMETER', 10, u'', 30, 30, False]]
        self.macro_test(macro, lex_correct)

        # Param and then empty
        macro = u'''/castsequence reset=combat Spell 1,'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'Spell 1', 27, 34, False],
                       ['AND', 5, u',', 34, 35, False],
                       ['PARAMETER', 6, u'', 35, 35, False]]
        self.macro_test(macro, lex_correct)

        # 2 params then empty
        macro = u'''/castsequence reset=combat Spell 1,Spell 2,'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'Spell 1', 27, 34, False],
                       ['AND', 5, u',', 34, 35, False],
                       ['PARAMETER', 6, u'Spell 2', 35, 42, False],
                       ['AND', 7, u',', 42, 43, False],
                       ['PARAMETER', 8, u'', 43, 43, False],]
        self.macro_test(macro, lex_correct)

        # Empty and one param then empty
        macro = u'''/castsequence reset=combat ,Spell 1,'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'', 27, 27, False],
                       ['AND', 5, u',', 27, 28, False],
                       ['PARAMETER', 6, u'Spell 1', 28, 35, False],
                       ['AND', 7, u',', 35, 36, False],
                       ['PARAMETER', 8, u'', 36, 36, False]]
        self.macro_test(macro, lex_correct)

        # Empty then one param
        macro = u'''/castsequence reset=combat ,Spell 1'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'', 27, 27, False],
                       ['AND', 5, u',', 27, 28, False],
                       ['PARAMETER', 6, u'Spell 1', 28, 35, False],]
        self.macro_test(macro, lex_correct)

        # three empties then param
        macro = u'''/castsequence reset=combat ,,,Spell 1'''
        lex_correct = [['COMMAND_VERB', 0, u'/castsequence', 0, 13, True],
                       ['MODIFIER', 1, u'reset', 14, 19, False],
                       ['GETS', 2, u'=', 19, 20, False],
                       ['OPTION_ARG', 3, u'combat', 20, 26, True],
                       ['PARAMETER', 4, u'', 27, 27, False],
                       ['AND', 5, u',', 27, 28, False],
                       ['PARAMETER', 6, u'', 28, 28, False],
                       ['AND', 7, u',', 28, 29, False],
                       ['PARAMETER', 8, u'', 29, 29, False],
                       ['AND', 9, u',', 29, 30, False],
                       ['PARAMETER', 10, u'Spell 1', 30, 37, False]]
        self.macro_test(macro, lex_correct)

    # Test commenting
    def test_commenting(self):
        macro = "#show"
        lex_correct = [['META_COMMAND_VERB', 0, u'#show', 0, 5, False]]
        self.macro_test(macro, lex_correct)

        macro = "##show a bus"
        lex_correct = [['COMMENTED_LINE', 0, u'##show a bus', 0, 12, False]]
        self.macro_test(macro, lex_correct)

        macro = "//use"
        lex_correct = [['COMMENTED_LINE', 0, u'//use', 0, 5, False]]
        self.macro_test(macro, lex_correct)

        macro = "//use a bomb"
        lex_correct = [['COMMENTED_LINE', 0, u'//use a bomb', 0, 12, False]]
        self.macro_test(macro, lex_correct)

        macro = "--/use 14"
        lex_correct = [['COMMENTED_LINE', 0, u'--/use 14', 0, 9, False]]
        self.macro_test(macro, lex_correct)        

        macro = "-/use 14"
        lex_correct = [['COMMENTED_LINE', 0, u'-/use 14', 0, 8, False]]
        self.macro_test(macro, lex_correct)        

        macro = "#/use 14"
        lex_correct = [['COMMENTED_LINE', 0, u'#/use 14', 0, 8, False]]
        self.macro_test(macro, lex_correct)

        macro = "//use 14"
        lex_correct = [['COMMENTED_LINE', 0, u'//use 14', 0, 8, False]]
        self.macro_test(macro, lex_correct)

    # Updated targeting option symantics
    def test_option_targeting1(self):
        macro = "/cast [target=Donuts-target-target-target] Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Donuts-', 14, 21, False],['TARGET_OBJ', 5, u'target-', 21, 28, False],['TARGET_OBJ', 6, u'target-', 28, 35, False],['TARGET_OBJ', 7, u'target', 35, 41, False],['ENDIF', 8, u']', 41, 42, False],['PARAMETER', 9, u'Mark of the Wild', 43, 59, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting2(self):
        macro = "/cast [target=Donuts-target-target] Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Donuts-', 14, 21, False],['TARGET_OBJ', 5, u'target-', 21, 28, False],['TARGET_OBJ', 6, u'target', 28, 34, False],['ENDIF', 7, u']', 34, 35, False],['PARAMETER', 8, u'Mark of the Wild', 36, 52, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting3(self):
        macro = "/cast [target=Donuts-targettarget] Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Donuts-', 14, 21, False],['TARGET_OBJ', 5, u'target', 21, 27, False],['TARGET_OBJ', 6, u'target', 27, 33, False],['ENDIF', 7, u']', 33, 34, False],['PARAMETER', 8, u'Mark of the Wild', 35, 51, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting4(self):
        macro = "/cast [target=Donuts-target] Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Donuts-', 14, 21, False],['TARGET_OBJ', 5, u'target', 21, 27, False],['ENDIF', 6, u']', 27, 28, False],['PARAMETER', 7, u'Mark of the Wild', 29, 45, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting5(self):
        macro = "/cast [target=Donuts] Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Donuts', 14, 20, False],['ENDIF', 5, u']', 20, 21, False],['PARAMETER', 6, u'Mark of the Wild', 22, 38, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting6(self):
        macro = u"""/cast [target=mouseover, harm] Blind; [target=targetstarget] Kidney Shot
            




"""
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'mouseover', 14, 23, False],['AND', 5, u',', 23, 24, False],['OPTION_WORD', 6, u'harm', 25, 29, False],['ENDIF', 7, u']', 29, 30, False],['PARAMETER', 8, u'Blind', 31, 36, False],['ELSE', 9, u';', 36, 37, False],['IF', 10, u'[', 38, 39, False],['TARGET', 11, u'target', 39, 45, False],['GETS', 12, u'=', 45, 46, False],['TARGET_OBJ', 13, u'target', 46, 52, False],['TARGET_OBJ', 14, u'starget', 52, 59, False],['ENDIF', 15, u']', 59, 60, False],['PARAMETER', 16, u'Kidney Shot', 61, 72, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting7(self):
        macro = "/cast [target=focus-pet-target-pet-target]Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'focus-', 14, 20, False],['TARGET_OBJ', 5, u'pet-', 20, 24, False],['TARGET_OBJ', 6, u'target-', 24, 31, False],['TARGET_OBJ', 7, u'pet-', 31, 35, False],['TARGET_OBJ', 8, u'target', 35, 41, False],['ENDIF', 9, u']', 41, 42, False],['PARAMETER', 10, u'Mark of the Wild', 42, 58, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting8(self):
        macro = "/cast [target=focuspettargetpettarget]Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'focus', 14, 19, False],['TARGET_OBJ', 5, u'pet', 19, 22, False],['TARGET_OBJ', 6, u'target', 22, 28, False],['TARGET_OBJ', 7, u'pet', 28, 31, False],['TARGET_OBJ', 8, u'target', 31, 37, False],['ENDIF', 9, u']', 37, 38, False],['PARAMETER', 10, u'Mark of the Wild', 38, 54, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting9(self):
        macro = "/cast [target=Fitz-target-target-focus]Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'Fitz-', 14, 19, False],['TARGET_OBJ', 5, u'target-', 19, 26, False],['TARGET_OBJ', 6, u'target-', 26, 33, False],['TARGET_OBJ', 7, u'focus', 33, 38, False],['ENDIF', 8, u']', 38, 39, False],['PARAMETER', 9, u'Mark of the Wild', 39, 55, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting10(self):
        macro = "/cast [target=party1pet-target-target]Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'party', 14, 19, False],['OPTION_ARG', 5, u'1', 19, 20, False],['TARGET_OBJ', 6, u'pet-', 20, 24, False],['TARGET_OBJ', 7, u'target-', 24, 31, False],['TARGET_OBJ', 8, u'target', 31, 37, False],['ENDIF', 9, u']', 37, 38, False],['PARAMETER', 10, u'Mark of the Wild', 38, 54, False]]
        self.macro_test(macro, lex_correct)

        macro = "/cast [target=party1pettargettarget]Mark of the Wild"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'party', 14, 19, False],['OPTION_ARG', 5, u'1', 19, 20, False],['TARGET_OBJ', 6, u'pet', 20, 23, False],['TARGET_OBJ', 7, u'target', 23, 29, False],['TARGET_OBJ', 8, u'target', 29, 35, False],['ENDIF', 9, u']', 35, 36, False],['PARAMETER', 10, u'Mark of the Wild', 36, 52, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting11(self):
        macro = "/cast [target=raidpet2-target] [] Spell 1"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'raidpet', 14, 21, False],['OPTION_ARG', 5, u'2', 21, 22, False],['TARGET_OBJ', 6, u'-target', 22, 29, False],['ENDIF', 7, u']', 29, 30, False],['IF', 8, u'[', 31, 32, False],['ENDIF', 9, u']', 32, 33, False],['PARAMETER', 10, u'Spell 1', 34, 41, False]]
        self.macro_test(macro, lex_correct)

    def test_option_targeting12(self):
        macro = "/cast [target=raid2-target-pet] Spell 1"
        lex_correct = [['COMMAND_VERB', 0, u'/cast', 0, 5, True],['IF', 1, u'[', 6, 7, False],['TARGET', 2, u'target', 7, 13, False],['GETS', 3, u'=', 13, 14, False],['TARGET_OBJ', 4, u'raid', 14, 18, False],['OPTION_ARG', 5, u'2', 18, 19, False],['TARGET_OBJ', 6, u'-target-', 19, 27, False],['TARGET_OBJ', 7, u'pet', 27, 30, False],['ENDIF', 8, u']', 30, 31, False],['PARAMETER', 9, u'Spell 1', 32, 39, False]]
        self.macro_test(macro, lex_correct)

    def test_complex_targeting1(self):
        macro = "/target raid2-target-pet"
        lex_correct = [['COMMAND_VERB', 0, u'/target', 0, 7, True],['PARAMETER', 1, u'raid2-target-pet', 8, 24, False]]
        self.macro_test(macro, lex_correct)

    # Bad spacing found on live with verbs that take a list
    def test_bad_target_spacing(self):
        macro = '''/castrandom [ target = target, harm , exists ] Spell'''
        lex_correct = [['COMMAND_VERB', 0, '/castrandom', 0, 11, True],['IF', 1, '[', 12, 13, False],['TARGET', 2, 'target', 14, 20, False],['GETS', 3, '=', 21, 22, False],['TARGET_OBJ', 4, 'target', 23, 29, False],['AND', 5, ',', 29, 30, False],['OPTION_WORD', 6, 'harm', 31, 35, False],['AND', 7, ',', 36, 37, False],['OPTION_WORD', 8, 'exists', 38, 44, False],['ENDIF', 9, ']', 45, 46, False],['PARAMETER', 10, 'Spell', 47, 52, False]]
        self.macro_test(macro, lex_correct)

        
if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLexer)

    # Run just one test
    if DEBUG:
        suiteOne = unittest.TestSuite()
        suiteOne.addTest(TestLexer("test_bad_target_spacing"))
        unittest.TextTestRunner(verbosity=2).run(suiteOne)
    else:
        unittest.TextTestRunner(verbosity=2).run(suite)
