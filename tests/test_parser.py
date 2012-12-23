 # -*- coding: utf-8 -*-


import sys
import random
import unittest
from macro.util import *
from macro.exceptions import *
from macro.logger import logger
from macro.parse.parser import MacroParser
from macro.lex.lexer import MacroCommandTokenizer
from macro.lex.token import MacroToken

# Output?
DEBUG = False

# Update shortcut
UPDATE = False


class TestParser(unittest.TestCase):
    def setUp(self):
        lexer = MacroCommandTokenizer(debug=DEBUG)
        self.parser = MacroParser(lexer_obj=lexer,
                                  debug=DEBUG)

    
    # Helpers to reduce repeated code
    def macro_parse(self, macro):
        if DEBUG: logger.debug(macro)
        macro_debug = []
        for i in range(len(macro)):
            macro_debug.append(str(i) + ": " + macro[i])
        if DEBUG: logger.debug(' '.join(macro_debug))

        # Parse it.
        obj = self.parser.lex_and_parse_macro(macro)

        # If we're updating, output the test code.
        if UPDATE: logger.debug("\n        macro = u\"\"\"" + macro + "\"\"\"\n        " + \
                                "objs = self.macro_parse(macro)\n        " + \
                                "correct = " + str(obj) + "\n        " + \
                                "self.macro_check(correct, objs)\n\n")

        if DEBUG:
            logger.warning("\n\n%s\n\n" % get_tree_str(obj, " "))
        return obj

    def macro_check(self, correct, obj):
        # Quickie debug helper.
        def equal(a, b):
            if a != b:
                if DEBUG:    logger.error("%s not equal to %s" % (a,b))
                elif UPDATE: logger.warning("Need to update test.")
                else:        self.assertEqual(a, b)     

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
        if not UPDATE: traverse(correct, obj)

    # Testing broken %t command--command can't expand it.
    def test_broken_insecure_with_no_curr_target(self):
        macro = '''/tell %t Hello!"'''
        self.assertRaises(ParseErrorInsecureVerbNoCurrentTarget, self.macro_parse, macro)

    # Testing insecure verbs that req targets but dont get them.
    def test_broken_insecure_req_target(self):
        macro = '''/tell "Hello!"'''
        self.assertRaises(LexErrorNoMatchingRules, self.macro_parse, macro)

    # Testing insecure verbs with targets
    def test_insecure_with_target(self):
        macro = '''/tell Fitz Hello!"'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/tell', 0, 5, True], [(None, [((None, None, [['TARGET_OBJ', 1, 'Fitz', 6, 10, True]]), None)], None, [(None, ['PARAMETER', 2, 'Hello!"', 11, 18, False])])])
        self.macro_check(correct, objs)

    # Testing insecure verbs with targets
    def test_insecure_glare(self):
        macro = '''/glare'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/glare', 0, 6, False], [(None, [((None, None, []), None)], None, None)])
        self.macro_check(correct, objs)

    # From a comment--CRITICAL CRASH
    def test_critical_crash(self):
        macro = '''/cast [target=focus,target=target]'''
        self.assertRaises(ParseErrorMultiTargetCondition, self.macro_parse, macro)

    # From forums
    def test_group_option_raid(self):
        macro = '''/cast [group:raid] Test'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'group', 7, 12, False], ['IS', 3, ':', 12, 13, False], [['OPTION_ARG', 4, 'raid', 13, 17, False]])], ['ENDIF', 5, ']', 17, 18, False]))], None, [(None, ['PARAMETER', 6, 'Test', 19, 23, False])])])
        self.macro_check(correct, objs)
        
    def test_assist_empty_obj(self):
        macro ="""/assist Fitzcairn;"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/assist', 0, 7, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Fitzcairn', 8, 17, False])]), (['ELSE', 2, ';', 17, 18, False], None, None, None)])
        self.macro_check(correct, objs)


    def test_assist_unit(self):
        macro ="""/assist Fitzcairn"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/assist', 0, 7, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Fitzcairn', 8, 17, False])])])
        self.macro_check(correct, objs)


    def test_bad_else_command(self):
        macro ="""/cast Spell; [combat] Spell2;"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])]), (['ELSE', 2, ';', 11, 12, False], [(None, (['IF', 3, '[', 13, 14, False], [(None, ['OPTION_WORD', 4, 'combat', 14, 20, False], None, None)], ['ENDIF', 5, ']', 20, 21, False]))], None, [(None, ['PARAMETER', 6, 'Spell2', 22, 28, False])]), (['ELSE', 7, ';', 28, 29, False], None, None, None)])
        self.macro_check(correct, objs)


    # Test new changes for 3.2
    def test_broken_targeting(self):
        macro ="""/petattack [target=Fire Resistance Totem]"""
        self.assertRaises(LexErrorNoMatchingRules, self.macro_parse, macro)


    def test_empty_command_obj(self):
        macro ="""/cast [combat] Spell 1;"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None)], ['ENDIF', 3, ']', 13, 14, False]))], None, [(None, ['PARAMETER', 4, 'Spell 1', 15, 22, False])]), (['ELSE', 5, ';', 22, 23, False], None, None, None)])
        self.macro_check(correct, objs)


    def test_empty_conditions(self):
        macro ="""/cast [target=mouseover, help] [ ] Flash of Light"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'help', 25, 29, False], None, None)], ['ENDIF', 7, ']', 29, 30, False])), (None, (['IF', 8, '[', 31, 32, False], None, ['ENDIF', 9, ']', 33, 34, False]))], None, [(None, ['PARAMETER', 10, 'Flash of Light', 35, 49, False])])])
        self.macro_check(correct, objs)


    def test_empty_multiline(self):
        macro ="""/cast [target=mouseover, harm] Blind; [target=targettarget] Kidney Shot
            




"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'harm', 25, 29, False], None, None)], ['ENDIF', 7, ']', 29, 30, False]))], None, [(None, ['PARAMETER', 8, 'Blind', 31, 36, False])]), (['ELSE', 9, ';', 36, 37, False], [((['TARGET', 11, 'target', 39, 45, False], ['GETS', 12, '=', 45, 46, False], [['TARGET_OBJ', 13, 'target', 46, 52, False], ['TARGET_OBJ', 14, 'target', 52, 58, False]]), (['IF', 10, '[', 38, 39, False], None, ['ENDIF', 15, ']', 58, 59, False]))], None, [(None, ['PARAMETER', 16, 'Kidney Shot', 60, 71, False])])])
        self.macro_check(correct, objs)


    def test_empty_rank(self):
        macro ="""/cast Faerie Fire (Feral)()"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Faerie Fire (Feral)()', 6, 27, False])])])
        self.macro_check(correct, objs)


    def test_equipslot_command(self):
        macro ="""/equipslot [combat] 14 Phat Dagger; [nocombat] 16 Poop Dagger"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'combat', 12, 18, False], None, None)], ['ENDIF', 3, ']', 18, 19, False]))], None, [(None, ['PARAMETER', 4, '14', 20, 22, True]), (None, ['PARAMETER', 5, 'Phat Dagger', 23, 34, False])]), (['ELSE', 6, ';', 34, 35, False], [(None, (['IF', 7, '[', 36, 37, False], [(['NOT', 8, 'no', 37, 39, False], ['OPTION_WORD', 9, 'combat', 39, 45, False], None, None)], ['ENDIF', 10, ']', 45, 46, False]))], None, [(None, ['PARAMETER', 11, '16', 47, 49, True]), (None, ['PARAMETER', 12, 'Poop Dagger', 50, 61, False])])])
        self.macro_check(correct, objs)


    def test_insecure_command(self):
        macro = '/party [combat] !"Oh crap!"'
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/party', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, '[combat] !"Oh crap!"', 7, 27, False])])])
        self.macro_check(correct, objs)


    def test_metacommands(self):
        macro ="""#show Stealth"""
        objs = self.macro_parse(macro)
        correct = (['META_COMMAND_VERB', 0, '#show', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Stealth', 6, 13, False])])])
        self.macro_check(correct, objs)


    def test_multiple_conditions(self):
        macro ="""/cast [help] [target=targettarget, help] [target=player] Flash Heal"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'help', 7, 11, False], None, None)], ['ENDIF', 3, ']', 11, 12, False])), ((['TARGET', 5, 'target', 14, 20, False], ['GETS', 6, '=', 20, 21, False], [['TARGET_OBJ', 7, 'target', 21, 27, False], ['TARGET_OBJ', 8, 'target', 27, 33, False]]), (['IF', 4, '[', 13, 14, False], [(None, ['OPTION_WORD', 10, 'help', 35, 39, False], None, None)], ['ENDIF', 11, ']', 39, 40, False])), ((['TARGET', 13, 'target', 42, 48, False], ['GETS', 14, '=', 48, 49, False], [['TARGET_OBJ', 15, 'player', 49, 55, False]]), (['IF', 12, '[', 41, 42, False], None, ['ENDIF', 16, ']', 55, 56, False]))], None, [(None, ['PARAMETER', 17, 'Flash Heal', 57, 67, False])])])
        self.macro_check(correct, objs)


    def test_non_param_command(self):
        macro ="""/targetfriend [combat] [nocombat]"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/targetfriend', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False])), (None, (['IF', 4, '[', 23, 24, False], [(['NOT', 5, 'no', 24, 26, False], ['OPTION_WORD', 6, 'combat', 26, 32, False], None, None)], ['ENDIF', 7, ']', 32, 33, False]))], None, None)])
        self.macro_check(correct, objs)


    def test_non_param_command_multi_objs(self):
        macro ="""/targetfriend [combat]; [nocombat]"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/targetfriend', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], None, None), (['ELSE', 4, ';', 22, 23, False], [(None, (['IF', 5, '[', 24, 25, False], [(['NOT', 6, 'no', 25, 27, False], ['OPTION_WORD', 7, 'combat', 27, 33, False], None, None)], ['ENDIF', 8, ']', 33, 34, False]))], None, None)])
        self.macro_check(correct, objs)


    def test_reset_after_conditions(self):
        macro ="""/castsequence [combat] reset=target Curse of Agony, Immolate, Corruption"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], (['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], [['OPTION_ARG', 6, 'target', 29, 35, True]]), [(None, ['PARAMETER', 7, 'Curse of Agony', 36, 50, False]), (None, ['PARAMETER', 9, 'Immolate', 52, 60, False]), (None, ['PARAMETER', 11, 'Corruption', 62, 72, False])])])
        self.macro_check(correct, objs)


    def test_secure_with_no_conditions(self):
        macro ="""/targetlastenemy"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/targetlastenemy', 0, 16, False], [(None, None, None, None)])
        self.macro_check(correct, objs)


    def test_simple(self):
        macro ="""/cast Spell"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])])])
        self.macro_check(correct, objs)


    def test_simple_equipslot_command(self):
        macro ="""/equipslot [combat] 14 Phat Dagger"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, [(None, (['IF', 1, '[', 11, 12, False], [(None, ['OPTION_WORD', 2, 'combat', 12, 18, False], None, None)], ['ENDIF', 3, ']', 18, 19, False]))], None, [(None, ['PARAMETER', 4, '14', 20, 22, True]), (None, ['PARAMETER', 5, 'Phat Dagger', 23, 34, False])])])
        self.macro_check(correct, objs)


    def test_swapactionbar_num_args(self):
        macro ="""/swapactionbar 1 2"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/swapactionbar', 0, 14, True], [(None, None, None, [(None, ['PARAMETER', 1, '1', 15, 16, True]), (None, ['PARAMETER', 2, '2', 17, 18, False])])])
        self.macro_check(correct, objs)


    def test_target_args(self):
        macro ="""/cast [target=raidpet2] [] Spell 1"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'raidpet', 14, 21, False], ['OPTION_ARG', 5, '2', 21, 22, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 6, ']', 22, 23, False])), (None, (['IF', 7, '[', 24, 25, False], None, ['ENDIF', 8, ']', 25, 26, False]))], None, [(None, ['PARAMETER', 9, 'Spell 1', 27, 34, False])])])
        self.macro_check(correct, objs)


    def test_target_args_chain(self):
        macro ="""/cast [] [target=party2targettargettarget] Spell 1"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [(None, (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 2, ']', 7, 8, False])), ((['TARGET', 4, 'target', 10, 16, False], ['GETS', 5, '=', 16, 17, False], [['TARGET_OBJ', 6, 'party', 17, 22, False], ['OPTION_ARG', 7, '2', 22, 23, False], ['TARGET_OBJ', 8, 'target', 23, 29, False], ['TARGET_OBJ', 9, 'target', 29, 35, False], ['TARGET_OBJ', 10, 'target', 35, 41, False]]), (['IF', 3, '[', 9, 10, False], None, ['ENDIF', 11, ']', 41, 42, False]))], None, [(None, ['PARAMETER', 12, 'Spell 1', 43, 50, False])])])
        self.macro_check(correct, objs)


    def test_target_chain(self):
        macro ="""/cast [target=playertargettargettarget] Spell 1"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'player', 14, 20, False], ['TARGET_OBJ', 5, 'target', 20, 26, False], ['TARGET_OBJ', 6, 'target', 26, 32, False], ['TARGET_OBJ', 7, 'target', 32, 38, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 8, ']', 38, 39, False]))], None, [(None, ['PARAMETER', 9, 'Spell 1', 40, 47, False])])])
        self.macro_check(correct, objs)


    def test_targetlastenemy(self):
        macro ="""/targetlastenemy [combat]"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/targetlastenemy', 0, 16, True], [(None, [(None, (['IF', 1, '[', 17, 18, False], [(None, ['OPTION_WORD', 2, 'combat', 18, 24, False], None, None)], ['ENDIF', 3, ']', 24, 25, False]))], None, None)])
        self.macro_check(correct, objs)


    def test_three_params(self):
        macro ="""/cast [target=mouseover,harm] Smite; [target=mouseover, help] Greater Heal; [] Greater Heal"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'mouseover', 14, 23, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'harm', 24, 28, False], None, None)], ['ENDIF', 7, ']', 28, 29, False]))], None, [(None, ['PARAMETER', 8, 'Smite', 30, 35, False])]), (['ELSE', 9, ';', 35, 36, False], [((['TARGET', 11, 'target', 38, 44, False], ['GETS', 12, '=', 44, 45, False], [['TARGET_OBJ', 13, 'mouseover', 45, 54, False]]), (['IF', 10, '[', 37, 38, False], [(None, ['OPTION_WORD', 15, 'help', 56, 60, False], None, None)], ['ENDIF', 16, ']', 60, 61, False]))], None, [(None, ['PARAMETER', 17, 'Greater Heal', 62, 74, False])]), (['ELSE', 18, ';', 74, 75, False], [(None, (['IF', 19, '[', 76, 77, False], None, ['ENDIF', 20, ']', 77, 78, False]))], None, [(None, ['PARAMETER', 21, 'Greater Heal', 79, 91, False])])])
        self.macro_check(correct, objs)


    def test_use_with_bag(self):
        macro ="""/use 13 14"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '13', 5, 7, True]), (None, ['PARAMETER', 2, '14', 8, 10, False])])])
        self.macro_check(correct, objs)


    def test_use_with_item(self):
        macro ="""/use Swift Dagger"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Swift Dagger', 5, 17, False])])])
        self.macro_check(correct, objs)


    def test_use_with_slot(self):
        macro ="""/use 13"""
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/use', 0, 4, True], [(None, None, None, [(None, ['PARAMETER', 1, '13', 5, 7, False])])])
        self.macro_check(correct, objs)


    def test_option_args(self): 
        macro = '''/castsequence [] reset=10/20/harm Battlestrider, Swift Green Mechanostrider'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], None, ['ENDIF', 2, ']', 15, 16, False]))], (['MODIFIER', 3, 'reset', 17, 22, False], ['GETS', 4, '=', 22, 23, False], [['OPTION_ARG', 5, '10', 23, 25, False], ['OPTION_ARG', 7, '20', 26, 28, False], ['OPTION_ARG', 9, 'harm', 29, 33, True]]), [(None, ['PARAMETER', 10, 'Battlestrider', 34, 47, False]), (None, ['PARAMETER', 12, 'Swift Green Mechanostrider', 49, 75, False])])])
        self.macro_check(correct, objs)


    def test_reset(self): 
        macro = '''/castsequence reset=10/harm [target=mouseover,harm,nobutton:1/2] Spell 1, Other Spell, Some Item; [] Test, Test2'''
        self.assertRaises(ParseErrorResetBeforeConditions, self.macro_parse, macro)


    def test_toggled_list(self): 
        macro = '''/castsequence [combat] reset=120 Spell 1, !Spell 2, !Spell 3'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], (['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], [['OPTION_ARG', 6, '120', 29, 32, True]]), [(None, ['PARAMETER', 7, 'Spell 1', 33, 40, False]), (['TOGGLE', 9, '!', 42, 43, False], ['PARAMETER', 10, 'Spell 2', 43, 50, False]), (['TOGGLE', 12, '!', 52, 53, False], ['PARAMETER', 13, 'Spell 3', 53, 60, False])])])
        self.macro_check(correct, objs)


    # Testing to make sure a broken command actually breaks.
    def test_broken_equipslot(self):
        macro = '/equipslot [combat] dagger'
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)


    # Test to make sure we break on bad slot/bag commands
    def test_broken_use(self):
        macro = '/use 13 Dagger'
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)
        macro = '/use 13 14 Dagger'
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)
        macro = '/use'
        self.assertRaises(ParseErrorParamRequired, self.macro_parse, macro)

    # Test to make sure we break on bad options.
    def test_broken_options(self):
        macro = '/cast [actionbar] Spell'
        self.assertRaises(ParseErrorReqArgsForOption, self.macro_parse, macro)
        macro = '/cast [equipped] Spell'
        self.assertRaises(ParseErrorReqArgsForOption, self.macro_parse, macro)
        macro = '/cast [button] Spell'
        self.assertRaises(ParseErrorReqArgsForOption, self.macro_parse, macro)

    # Test an else
    def test_bad_else_command(self):
        macro ="/cast Spell; [combat] Spell2;"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])]), (['ELSE', 2, ';', 11, 12, False], [(None, (['IF', 3, '[', 13, 14, False], [(None, ['OPTION_WORD', 4, 'combat', 14, 20, False], None, None)], ['ENDIF', 5, ']', 20, 21, False]))], None, [(None, ['PARAMETER', 6, 'Spell2', 22, 28, False])]), (['ELSE', 7, ';', 28, 29, False], None, None, None)])
        self.macro_check(correct, objs)


    # Test that we can handle extra verbs.
    def test_extra_verb(self):
        macro ="/cast Spell; /cast [combat] Spell2;"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Spell', 6, 11, False])]), (['ELSE', 2, ';', 11, 12, False], [(None, (['IF', 4, '[', 19, 20, False], [(None, ['OPTION_WORD', 5, 'combat', 20, 26, False], None, None)], ['ENDIF', 6, ']', 26, 27, False]))], None, [(None, ['PARAMETER', 7, 'Spell2', 28, 34, False])]), (['ELSE', 8, ';', 34, 35, False], None, None, None)])
        self.macro_check(correct, objs)
        macro = '/cast Spell; /cancelaura [combat] Spell'
        self.assertRaises(ParseErrorMultipleVerbs, self.macro_parse, macro)
        

    def test_fail_empty_commands(self):
        macro ="/castsequence;"
        self.assertRaises(ParseErrorParamRequired, self.macro_parse, macro)

    # Test a command with space issues, as well as default targets
    def test_spaces_in_targets(self):
        macro ="/focus  [ mod : shift , no mod : ctrl ]  none ; [ target = focus , harm , no dead ]  focus ; [ harm , no dead ]  ; none"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/focus', 0, 6, True], [(None, [(None, (['IF', 1, '[', 7, 8, False], [(None, ['OPTION_WORD', 2, 'mod', 9, 12, False], ['IS', 3, ':', 13, 14, False], [['OPTION_ARG', 4, 'shift', 15, 20, False]]), (['NOT', 6, 'no', 23, 25, False], ['OPTION_WORD', 7, 'mod', 26, 29, False], ['IS', 8, ':', 30, 31, False], [['OPTION_ARG', 9, 'ctrl', 32, 36, False]])], ['ENDIF', 10, ']', 37, 38, False]))], None, [(None, ['PARAMETER', 11, 'none', 39, 43, False])]), (['ELSE', 12, ';', 44, 45, False], [((['TARGET', 14, 'target', 48, 54, False], ['GETS', 15, '=', 55, 56, False], [['TARGET_OBJ', 16, 'focus', 57, 62, False]]), (['IF', 13, '[', 46, 47, False], [(None, ['OPTION_WORD', 18, 'harm', 65, 69, False], None, None), (['NOT', 20, 'no', 72, 74, False], ['OPTION_WORD', 21, 'dead', 75, 79, False], None, None)], ['ENDIF', 22, ']', 80, 81, False]))], None, [(None, ['PARAMETER', 23, 'focus', 82, 87, False])]), (['ELSE', 24, ';', 88, 89, False], [(None, (['IF', 25, '[', 90, 91, False], [(None, ['OPTION_WORD', 26, 'harm', 92, 96, False], None, None), (['NOT', 28, 'no', 99, 101, False], ['OPTION_WORD', 29, 'dead', 102, 106, False], None, None)], ['ENDIF', 30, ']', 107, 108, False]))], None, None), (['ELSE', 31, ';', 109, 110, False], None, None, [(None, ['PARAMETER', 32, 'none', 111, 115, False])])])
        self.macro_check(correct, objs)

    # Reset always follows conditions.
    def test_reset_before_conditions(self):
        macro ="/castsequence [combat] reset=target Curse of Agony, Immolate, Corruption"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'combat', 15, 21, False], None, None)], ['ENDIF', 3, ']', 21, 22, False]))], (['MODIFIER', 4, 'reset', 23, 28, False], ['GETS', 5, '=', 28, 29, False], [['OPTION_ARG', 6, 'target', 29, 35, True]]), [(None, ['PARAMETER', 7, 'Curse of Agony', 36, 50, False]), (None, ['PARAMETER', 9, 'Immolate', 52, 60, False]), (None, ['PARAMETER', 11, 'Corruption', 62, 72, False])])])
        self.macro_check(correct, objs)


    # Test equipslot with bags
    def test_bag_equipslot(self):
        macro ="/equipslot 16 0 12"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/equipslot', 0, 10, True], [(None, None, None, [(None, ['PARAMETER', 1, '16', 11, 13, True]), (None, ['PARAMETER', 2, '0', 14, 15, True]), (None, ['PARAMETER', 3, '12', 16, 18, False])])])
        self.macro_check(correct, objs)

    # Test equip with bags
    def test_bag_equip(self):
        macro ="/equip 0 12"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/equip', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, '0', 7, 8, True]), (None, ['PARAMETER', 2, '12', 9, 11, False])])])
        self.macro_check(correct, objs)

     
    # Test special click commands
    def test_click_cmds(self):
        macro ="/click PetActionButton5 LeftButton"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'PetActionButton', 7, 22, False]), (None, ['PARAMETER', 2, '5', 22, 23, True]), (None, ['PARAMETER', 3, 'LeftButton', 24, 34, False])])])
        self.macro_check(correct, objs)
        macro ="/click PetActionButton5"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'PetActionButton', 7, 22, False]), (None, ['PARAMETER', 2, '5', 22, 23, False])])])
        self.macro_check(correct, objs)

    # Test broken click command
    def test_click_broken_cmds(self):
        macro ="/click Garbarage124Button4"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, None, None, [(None, ['PARAMETER', 1, 'Garbarage124Button4', 7, 26, False])])])
        self.macro_check(correct, objs)


    # Test broken actionbar commands
    def test_swapactionbar_fail(self):
        macro ="/swapactionbar [combat] 2 3 4"
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)
        macro ="/swapactionbar [combat] 2"
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)
        macro ="/swapactionbar [combat]"
        self.assertRaises(ParseErrorParamRequired, self.macro_parse, macro)

    def test_changeactionbar_fail(self):
        macro ="/changeactionbar [combat]"
        self.assertRaises(ParseErrorParamRequired, self.macro_parse, macro)
        macro ="/changeactionbar [combat] 2 3"
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)        


    # Test broken harden command
    def test_helpme(self):
        macro ="/helpme"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/helpme', 0, 7, False], [(None, None, None, None)])
        self.macro_check(correct, objs)

    # Another broken harden command.
    def test_equipslot_wrong_params(self):
        macro ="""/equipslot [button:2] Z X Y"""
        self.assertRaises(ParseErrorWrongParams, self.macro_parse, macro)


    # Test out the new lexer rules for @target 3.3 changes.
    def test_target_alias(self):
        macro = '''/cast [@focus] Test'''    
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, '@', 7, 8, False], None, [['TARGET_OBJ', 3, 'focus', 8, 13, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 4, ']', 13, 14, False]))], None, [(None, ['PARAMETER', 5, 'Test', 15, 19, False])])])
        self.macro_check(correct, objs)

    # Test to make sure insecure commands that require params
    # trigger the exception.
    def test_insecure_param_required(self):
        macro ="""/master"""
        self.assertRaises(ParseErrorParamRequired, self.macro_parse, macro)

    # Another test that seems to be causing problems
    def test_broken_cast_target_pet(self):
        macro = '''/cast [combat,modifier:alt,harm,target=pettarget] [] Shadow Bolt'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 10, 'target', 32, 38, False], ['GETS', 11, '=', 38, 39, False], [['TARGET_OBJ', 12, 'pet', 39, 42, False], ['TARGET_OBJ', 13, 'target', 42, 48, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 2, 'combat', 7, 13, False], None, None), (None, ['OPTION_WORD', 4, 'modifier', 14, 22, False], ['IS', 5, ':', 22, 23, False], [['OPTION_ARG', 6, 'alt', 23, 26, False]]), (None, ['OPTION_WORD', 8, 'harm', 27, 31, False], None, None)], ['ENDIF', 14, ']', 48, 49, False])), (None, (['IF', 15, '[', 50, 51, False], None, ['ENDIF', 16, ']', 51, 52, False]))], None, [(None, ['PARAMETER', 17, 'Shadow Bolt', 53, 64, False])])])
        self.macro_check(correct, objs)

    def test_sequence_w_empties(self):    
        macro = '''/castsequence reset=combat ,,Potion of Wild Magic,'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, None, (['MODIFIER', 1, 'reset', 14, 19, False], ['GETS', 2, '=', 19, 20, False], [['OPTION_ARG', 3, 'combat', 20, 26, True]]), [(None, ['PARAMETER', 4, '', 27, 27, False]), (None, ['PARAMETER', 6, '', 28, 28, False]), (None, ['PARAMETER', 8, 'Potion of Wild Magic', 29, 49, False]), (None, ['PARAMETER', 10, '', 50, 50, False])])])
        self.macro_check(correct, objs)

    # This broke some things.
    def test_ors_with_options(self):
        macro = '''/castsequence [modifier:alt,nogroup,pet:Voidwalker/pet:Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/castsequence', 0, 13, True], [(None, [(None, (['IF', 1, '[', 14, 15, False], [(None, ['OPTION_WORD', 2, 'modifier', 15, 23, False], ['IS', 3, ':', 23, 24, False], [['OPTION_ARG', 4, 'alt', 24, 27, False]]), (['NOT', 6, 'no', 28, 30, False], ['OPTION_WORD', 7, 'group', 30, 35, False], None, None), (None, ['OPTION_WORD', 9, 'pet', 36, 39, False], ['IS', 10, ':', 39, 40, False], [['OPTION_ARG', 11, 'Voidwalker', 40, 50, False], ['OPTION_ARG', 15, 'Felhunter', 55, 64, False]])], ['ENDIF', 16, ']', 64, 65, False]))], None, [(None, ['PARAMETER', 17, 'Searing Pain', 66, 78, False]), (None, ['PARAMETER', 19, 'Shadow Bolt', 80, 91, False]), (None, ['PARAMETER', 21, 'Shadow Bolt', 93, 104, False])])])
        self.macro_check(correct, objs)

    # Ensure this breaks.
    def test_ors_with_options_broken(self):
        macro = '''/castsequence [modifier:alt,nogroup,pet:Voidwalker/nopet:Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt'''
        self.assertRaises(ParseErrorNonMatchingNegs, self.macro_parse, macro)
        macro = '''/castsequence [modifier:alt,nogroup,pet:Voidwalker/stance:1] Searing Pain, Shadow Bolt, Shadow Bolt'''
        self.assertRaises(ParseErrorNonMatchingOptionWords, self.macro_parse, macro)

    # Another broken macro
    def test_broken_click(self):
        macro = '''/click [nomod] ORLOpen OPieRaidSymbols;'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/click', 0, 6, True], [(None, [(None, (['IF', 1, '[', 7, 8, False], [(['NOT', 2, 'no', 8, 10, False], ['OPTION_WORD', 3, 'mod', 10, 13, False], None, None)], ['ENDIF', 4, ']', 13, 14, False]))], None, [(None, ['PARAMETER', 5, 'ORLOpen OPieRaidSymbols', 15, 38, False])]), (['ELSE', 6, ';', 38, 39, False], None, None, None)])
        self.macro_check(correct, objs)

    # Another broken macro
    def test_broken_equip_macro(self):
        macro = '''/equip [noequipped: Fishing Pole,nomod:shift] Fishing Pole;'''
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/equip', 0, 6, True], [(None, [(None, (['IF', 1, '[', 7, 8, False], [(['NOT', 2, 'no', 8, 10, False], ['OPTION_WORD', 3, 'equipped', 10, 18, False], ['IS', 4, ':', 18, 19, False], [['OPTION_ARG', 5, 'Fishing Pole', 20, 32, False]]), (['NOT', 7, 'no', 33, 35, False], ['OPTION_WORD', 8, 'mod', 35, 38, False], ['IS', 9, ':', 38, 39, False], [['OPTION_ARG', 10, 'shift', 39, 44, False]])], ['ENDIF', 11, ']', 44, 45, False]))], None, [(None, ['PARAMETER', 12, 'Fishing Pole', 46, 58, False])]), (['ELSE', 13, ';', 58, 59, False], None, None, None)])
        self.macro_check(correct, objs)

    # Test commenting
    def test_commenting(self):
        macro = "--/use 14"
        objs = self.macro_parse(macro)
        correct = (['COMMENTED_LINE', 0, '--/use 14', 0, 9, False], [(None, None, None, None)])
        self.macro_check(correct, objs)

    # Test follow-on targeting
    def test_option_targeting_follow1(self):
        macro = "/cast [target=Fitz-target-target-focus]Mark of the Wild"
        self.assertRaises(ParseErrorInvalidTargetToken, self.macro_parse, macro)

    # Test follow-on targeting
    def test_option_targeting_follow2(self):
        macro = "/cast [target=Fitz-target-target]Mark of the Wild"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'Fitz-', 14, 19, False], ['TARGET_OBJ', 5, 'target-', 19, 26, False], ['TARGET_OBJ', 6, 'target', 26, 32, False]]), (['IF', 1, '[', 6, 7, False], None, ['ENDIF', 7, ']', 32, 33, False]))], None, [(None, ['PARAMETER', 8, 'Mark of the Wild', 33, 49, False])])])
        self.macro_check(correct, objs)


    # Test parsing for option args that modify targeting
    def test_target_option_args(self):
        macro = "/cast [target=player,mod:FOCUSCAST]Spell"
        objs = self.macro_parse(macro)
        correct = (['COMMAND_VERB', 0, '/cast', 0, 5, True], [(None, [((['TARGET', 2, 'target', 7, 13, False], ['GETS', 3, '=', 13, 14, False], [['TARGET_OBJ', 4, 'player', 14, 20, False]]), (['IF', 1, '[', 6, 7, False], [(None, ['OPTION_WORD', 6, 'mod', 21, 24, False], ['IS', 7, ':', 24, 25, False], [['OPTION_ARG', 8, 'FOCUSCAST', 25, 34, False]])], ['ENDIF', 9, ']', 34, 35, False]))], None, [(None, ['PARAMETER', 10, 'Spell', 35, 40, False])])])
        self.macro_check(correct, objs)

        
if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)

    # Run just one test
    if DEBUG:
        suiteOne = unittest.TestSuite()
        suiteOne.addTest(TestParser("test_insecure_glare"))
        unittest.TextTestRunner(verbosity=2).run(suiteOne)
    else:
        unittest.TextTestRunner(verbosity=2).run(suite)


