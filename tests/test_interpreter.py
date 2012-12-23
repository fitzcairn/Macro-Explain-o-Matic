# -*- coding: latin-1 -*
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

class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.mi = get_test_mi(debug=DEBUG, lookup=False)
        lexer = MacroCommandTokenizer(debug=DEBUG)
        self.parser = MacroParser(lexer_obj=lexer,
                                  debug=DEBUG)
        return
    
    # Helpers to reduce repeated code
    def macro_test(self, macro, correct=()):
        int_obj = self.mi.interpret_macro(macro).get_test_repr()
        if not UPDATE:
            if DEBUG:
                logger.info('')
                logger.info('\n' + macro)
                logger.info(self.mi)
                logger.info(int_obj)
            self.assertEqual(correct, int_obj, "\nMACRO:%s\nEXP: %s\nGOT: %s" %\
                             (macro,
                              correct,
                              int_obj)
                             )
        else:
            if DEBUG: logger.info(self.mi)
            print "\n%s\n" % generate_test_function(macro, int_c=int_obj)


    # Testing a nontargeted insecure command using %t
    def test_insecure_say_w_currtarget(self):
        macro = u'''/say %t broke my sheep!'''
        int_correct = [[None, u'Say "(your currently targeted unit) broke my sheep!"']]
        self.macro_test(macro, int_correct)        

    # Testing a targeted insecure command using %t
    def test_insecure_tell_target_w_currtarget(self):
        macro = u'''/tell Fitz my current target is %t'''
        int_correct = [[None, u'Whisper "my current target is (your currently targeted unit)" to Fitz']]
        self.macro_test(macro, int_correct)        

    # Testing replies
    def test_reply(self):
        macro = u'''/r %t Fitz [combat]"'''
        int_correct = [[None, u'Reply to last whisper: "(your currently targeted unit) Fitz [combat]""']]
        self.macro_test(macro, int_correct)        

    # Testing insecure verbs with targets
    def test_insecure_with_target(self):
        macro = u'''/tell Fitz Hello!"'''
        int_correct = [[None, u'Whisper "Hello!"" to Fitz']]
        self.macro_test(macro, int_correct)
        
    # Critical failure.
    def test_critical_failure_equipslot(self):
        macro = u"/equipslot 12 Dragon's Eye"
        int_correct = [[None, u"Equip your Dragon's Eye as your second ring"]]
        self.macro_test(macro, int_correct)
        
    # From my launch blog
    def test_equipset(self):
        macro = u'''/equipset [spec:1]Healing;[spec:2]Boomkin'''
        int_correct = [[u'If you have spec 1 active then:', u"Equip equipment set 'Healing' via the Equipment Manager"], [u'Else, if you have spec 2 active then:', u"Equip equipment set 'Boomkin' via the Equipment Manager"]]
        self.macro_test(macro, int_correct)        
    def test_usetalents(self):
        macro = u'''/usetalents [spec:1]2;[spec:2]1'''
        int_correct = [[u'If you have spec 1 active then:', u'Activate talent set 2'], [u'Else, if you have spec 2 active then:', u'Activate talent set 1']]
        self.macro_test(macro, int_correct)        

    # From the forums
    def test_petattack_target(self):
        macro = u'''/petattack [target=pettarget,noexists]target'''
        int_correct = [["If your pet's currently targeted unit does not exist then:", 'Order your pet to attack the currently targeted unit']]
        self.macro_test(macro, int_correct)

    # Another from the forums
    def test_petautocaston(self):
        macro = u'''/petautocastoff [pet:felguard] Cleave'''
        int_correct = [[u'If you have a pet named or of type felguard out then:', u'Turn off pet skill autocast for Cleave']]
        self.macro_test(macro, int_correct)
    def test_petautocastoff(self):
        macro = u'''/petautocastoff [pet:felguard] Cleave'''
        int_correct = [[u'If you have a pet named or of type felguard out then:', u'Turn off pet skill autocast for Cleave']]
        self.macro_test(macro, int_correct)
    def test_petautocasttoggle(self):
        macro = u'''/petautocasttoggle [pet:felguard] Cleave '''
        int_correct = [[u'If you have a pet named or of type felguard out then:', u'Change pet skill autocast state for Cleave']]
        self.macro_test(macro, int_correct)

    # This was recently fixed.
    def test_assist(self):
        macro = u'''/assist Fitzcairn;'''
        int_correct = [[None, u'Set your target to the target of Fitzcairn']]
        self.macro_test(macro, int_correct)

    def test_bad_else(self):
        macro = u'''/cast [combat] [mounted] Spell; [stealth] [] Spell2; Spell3'''
        int_correct = [['If you are in combat then:', u'Cast Spell on the currently targeted unit'], ['Else, if you are mounted then:', u'Cast Spell on the currently targeted unit'], ['Else, if you are stealthed then:', u'Cast Spell2 on the currently targeted unit'], ['Otherwise:', u'Cast Spell2 on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_broken_targeting(self):
        macro = u'''/petattack [target=Fire Resistance Totem]'''
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro, None)

    def test_cast_multiple(self):
        macro = u'''/cast [equipped:Fishing Pole] Fishing; [equipped:Thrown] Throw; Shoot'''
        int_correct = [[u'If you have equipped item or itemtype Fishing Pole then:', u'Cast Fishing on the currently targeted unit'], [u'Else, if you have equipped item or itemtype Thrown then:', u'Cast Throw on the currently targeted unit'], ['Otherwise:', u'Cast Shoot on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_command(self):
        macro = u'''/cast Spell'''
        int_correct = [[None, u'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_condition(self):
        macro = u'''/equip [combat] Sexy Dagger'''
        int_correct = [['If you are in combat then:', u'Equip your Sexy Dagger in its default slot']]
        self.macro_test(macro, int_correct)

    def test_condition_multi(self):
        macro = u'''/cast [combat, help] Greater Heal'''
        int_correct = [['If you are in combat and the currently targeted unit is a friend then:', u'Cast Greater Heal on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_condition_multi_arg(self):
        macro = u'''/cast [combat, button:1/2/3] Greater Heal'''
        int_correct = [[u'If you are in combat and activated this macro with mouse button 1, mouse button 3, or mouse button 2 then:', u'Cast Greater Heal on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_condition_multi_empty_cond(self):
        macro = u'''/cast [button:1/2/3, help] [ ] [nocombat] Flash of Light'''
        int_correct = [[u'If you activated this macro with mouse button 1, mouse button 3, or mouse button 2 and the currently targeted unit is a friend then:', u'Cast Flash of Light on the currently targeted unit'], ['Otherwise:', u'Cast Flash of Light on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_condition_multi_target(self):
        macro = u'''/cast [target=mouseover, help] [nocombat] Flash of Light'''
        int_correct = [['If the unit your mouse is currently over is a friend then:', u'Cast Flash of Light on the unit your mouse is currently over'], ['Else, if you are not in combat then:', u'Cast Flash of Light on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_equipslot(self):
        macro = u'''/equipslot [target=mouseover,nogroup] 16 Dagger'''
        int_correct = [['If you are not in a group then:', u'Equip your Dagger as your main-hand weapon']]
        self.macro_test(macro, int_correct)

    def test_focus_cond_target(self):
        macro = u'''/focus [target=Fire Resistance Totem]'''
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro, None)

    def test_insecure(self):
        macro = u'''/s This is [] a test of say!'''
        int_correct = [[None, u'Say "This is [] a test of say!"']]
        self.macro_test(macro, int_correct)

    def test_key_unit_not_used(self):
        macro = u'''/target [target=focus, dead] party1'''
        int_correct = [['If the unit saved as your focus target is dead then:', 'Set target to the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_key_unit_used(self):
        macro = u'''/focus [target=focus, dead] [target=party1pet, noharm] Fitzcairn'''
        int_correct = [['If the unit saved as your focus target is dead then:', u'Set your focus target to Fitzcairn'], [u"Else, if party member 1's pet is not an enemy then:", u"Set your focus target to party member 1's pet"]]
        self.macro_test(macro, int_correct)

    # This broke some things.
    def test_ors_with_options(self):
        macro = u'''/castsequence [modifier:alt,nogroup,pet:Voidwalker/pet:Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt'''
        int_correct = [[u'If you were holding the alt key, are not in a group, and have a pet named or of type Voidwalker or Felhunter out then:', u'Cast the next spell in a sequence of [ Searing Pain on the currently targeted unit, Shadow Bolt on the currently targeted unit, Shadow Bolt on the currently targeted unit ] each time the macro is activated']]
        self.macro_test(macro, int_correct)    

    def test_multi_cond_target(self):
        macro = u'''/use [target=targettarget, harm] [target=mouseover, help, button:1/2/3] Item 1; [target=player, combat] Item 2'''
        int_correct = [["If the currently targeted unit's currently targeted unit is an enemy then:", u'Use your Item 1'], [u'Else, if the unit your mouse is currently over is a friend and you activated this macro with mouse button 1, mouse button 3, or mouse button 2 then:', u'Use your Item 1'], ['Else, if you are in combat then:', u'Use your Item 2']]
        self.macro_test(macro, int_correct)

    def test_multi_object(self):
        macro = u'''/use [combat] [mounted] Item 1; [nocombat, nomounted] Item 2; Item 3'''
        int_correct = [['If you are in combat then:', u'Use your Item 1'], ['Else, if you are mounted then:', u'Use your Item 1'], ['Else, if you are not in combat and are not mounted then:', u'Use your Item 2'], ['Otherwise:', u'Use your Item 3']]
        self.macro_test(macro, int_correct)

    def test_multi_target(self):
        macro = u'''/cast [target=party1targettarget] Spell'''
        int_correct = [[None, u"Cast Spell on party member 1's currently targeted unit's currently targeted unit"]]
        self.macro_test(macro, int_correct)

    def test_pettarget_cast(self):
        macro = u'''/cast [combat,modifier:alt,harm,target=pettarget] [] Shadow Bolt'''
        int_correct = [["If you are in combat and were holding the alt key and your pet's currently targeted unit is an enemy then:", u"Cast Shadow Bolt on your pet's currently targeted unit"], ['Otherwise:', u'Cast Shadow Bolt on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_phrase_target_string(self):
        macro = u'''/cast [target=mouseover,help,nodead,exists][help,nodead][]Fluffy spell'''
        int_correct = [['If the unit your mouse is currently over is a friend, is not dead, and exists then:', u'Cast Fluffy spell on the unit your mouse is currently over'], ['Else, if the currently targeted unit is a friend and is not dead then:', u'Cast Fluffy spell on the currently targeted unit'], ['Otherwise:', u'Cast Fluffy spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_real_macro(self):
        macro = u'''/cast [equipped:Shields,stance:1/2] Shield Bash; [equipped:Shields] Defensive Stance; [stance:3] Pummel; Berserker Stance'''
        int_correct = [[u'If you have equipped item or itemtype Shields and are in stance 1 or 2 then:', u'Cast Shield Bash on the currently targeted unit'], [u'Else, if you have equipped item or itemtype Shields then:', u'Cast Defensive Stance on the currently targeted unit'], [u'Else, if you are in stance 3 then:', u'Cast Pummel on the currently targeted unit'], ['Otherwise:', u'Cast Berserker Stance on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_reset(self):
        macro = u'''/castsequence reset=90 Bladefist's Breadth, Blackhand's Breadth'''
        int_correct = [[None, u"Cast the next spell in a sequence of [ Bladefist's Breadth on the currently targeted unit, Blackhand's Breadth on the currently targeted unit ] each time the macro is activated, resetting the sequence after 90 seconds"]]
        self.macro_test(macro, int_correct)

    def test_self_cast(self):
        macro = u'''/cast Anger Management'''
        int_correct = [[None, u'Cast Anger Management on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_serious_break(self):
        macro = u'''#showtooltip Curse of Agony
/use 13
/use 14
/cast Metamorphosis
/cast [pet:Felguard] [pet:imp] Demonic Empowerment
/script UIErrorsFrame:Clear()
/cast Curse of Agony'''
        int_correct = [[None, u'Show tooltip, icon, and cooldown for Curse of Agony for this macro on the action bar'], [None, 'Use your equipped first trinket'], [None, 'Use your equipped second trinket'], [None, u'Cast Metamorphosis on the currently targeted unit'], [u'If you have a pet named or of type Felguard out then:', u'Cast Demonic Empowerment on the currently targeted unit'], [u'Else, if you have a pet named or of type imp out then:', u'Cast Demonic Empowerment on the currently targeted unit'], [None, u'Run Lua: UIErrorsFrame:Clear()'], [None, u'Cast Curse of Agony on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_showtooltip(self):
        macro = u'''#showtooltip [nomodifier:alt] attack; [modifier] Shoot (or Throw)'''
        int_correct = [['If you were not holding the alt key then:', u'Show tooltip, icon, and cooldown for attack for this macro on the action bar'], ['Else, if you holding a modifier key then:', u'Show tooltip, icon, and cooldown for Shoot (or Throw) for this macro on the action bar']]
        self.macro_test(macro, int_correct)

    def test_targeting(self):
        macro = u'''/cast [target=party1,nodead] Heal'''
        int_correct = [[u'If party member 1 is not dead then:', u'Cast Heal on party member 1']]
        self.macro_test(macro, int_correct)

    def test_too_long(self):
        macro = u'''/petfollow [pet:succubus]'''
        int_correct = [[u'If you have a pet named or of type succubus out then:', 'Turn on pet follow mode, canceling other modes']]
        self.macro_test(macro, int_correct)

    def test_use_item_slot(self):
        macro = u'''/use 13 15'''
        int_correct = [[None, u'Use item in bag number 13, bag slot number 15']]
        self.macro_test(macro, int_correct)

    def test_use_item_w_spaces(self):
        macro = u'''/equip 10 Pound Mud Snapper'''
        int_correct = [[None, u'Equip your 10 Pound Mud Snapper in its default slot']]
        self.macro_test(macro, int_correct)

    def test_wowwiki_broken(self):
        macro = u'''#showtooltip
        /castsequence [modifier:alt,nogroup,nopet:Voidwalker/Felhunter] Searing Pain, Shadow Bolt, Shadow Bolt'''
        int_correct = [[None, 'Show tooltip, icon, and cooldown for the first item or spell in this macro on the action bar'], [u'If you were holding the alt key, are not in a group, and do not have a pet named or of type Voidwalker or Felhunter out then:', u'Cast the next spell in a sequence of [ Searing Pain on the currently targeted unit, Shadow Bolt on the currently targeted unit, Shadow Bolt on the currently targeted unit ] each time the macro is activated']]
        self.macro_test(macro, int_correct)

    def test_option_args_w_reset_broken(self):
        macro = u'''/castsequence [] reset=10/20/harm Battlestrider, Swift Green Mechanostrider'''
        self.assertRaises(InterpetErrorInvalidResetOption, self.macro_test, macro, None)

    def test_bad_option_arg(self):
        macro = u'''/cast [pet:combat] Stuff'''
        self.assertRaises(InterpetErrorInvalidConditionArg, self.macro_test, macro, None)
        
    def test_pet_type(self):
        macro = u'''/cast [pet:Felhunter] Devour Magic'''
        int_correct = [[u'If you have a pet named or of type Felhunter out then:', u'Cast Devour Magic on the currently targeted unit']]
        self.macro_test(macro, int_correct)        


    # Broken from the harden test
    def test_broken_reset_castsequence(self):
        macro = u'''/castsequence [target=player]  reset=20/ Inner Fire, Power Word: Fortitude, Shadow Protection'''
        self.assertRaises(ParseErrorUnexpectedToken, self.macro_test, macro, None)


    # Test an emote that doesn't use a target
    def test_helpme1(self):
        macro = u"/helpme"
        int_correct = [[None, 'Emote "You cry out for help!"']]
        self.macro_test(macro, int_correct)

    def test_helpme2(self):
        macro = u"/helpme target"
        int_correct = [[None, 'Emote "You cry out for help!"']]
        self.macro_test(macro, int_correct)

    def test_helpme3(self):
        macro = u"/helpme %t"
        int_correct = [[None, 'Emote "You cry out for help!"']]
        self.macro_test(macro, int_correct)

    def test_helpme4(self):
        macro = u"/helpme unit"
        int_correct = [[None, 'Emote "You cry out for help!"']]
        self.macro_test(macro, int_correct)        

    # Test an emote that uses a target
    def test_glare1(self):
        macro = u"/glare"
        int_correct = [[None, 'Emote "You glare angrily."']]
        self.macro_test(macro, int_correct)

    def test_glare2(self):
        macro = u"/glare target"
        int_correct = [[None, 'Emote "You glare angrily."']]
        self.macro_test(macro, int_correct)

    def test_glare3(self):
        macro = u"/glare %t"
        int_correct = [[None, 'Emote "You glare angrily at (your currently targeted unit)."']]
        self.macro_test(macro, int_correct)

    def test_glare4(self):
        macro = u"/glare unit"
        int_correct = [[None, u'Emote "You glare angrily at unit."']]
        self.macro_test(macro, int_correct)        

        
    # Test new 3.3 conditionals
    def test_vehicleui1(self):
        macro = u'''/cast [vehicleui] Tank Stuff'''
        int_correct = [['If you have a vechicle UI then:', u'Cast Tank Stuff on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_vehicleui2(self):
        macro = u'''/cast [combat,harm,vehicleui,target=focus] Tank Stuff'''
        int_correct = [['If you are in combat and have a vechicle UI and the unit saved as your focus target is an enemy then:', u'Cast Tank Stuff on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_unithasvehicleui1(self):
        macro = u'''/cast [unithasvehicleui] Tank Stuff'''
        int_correct = [['If the currently targeted unit has a vehicle UI then:', u'Cast Tank Stuff on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_unithasvehicleui2(self):
        macro = u'''/cast [combat,harm,unithasvehicleui,target=focus] Tank Stuff'''
        int_correct = [['If you are in combat and the unit saved as your focus target is an enemy and has a vehicle UI then:', u'Cast Tank Stuff on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    # Test out the new lexer rules for @target 3.3 changes.
    def test_target_alias1(self):
        macro = u'''/cast [@focus] Test'''    
        int_correct = [[None, u'Cast Test on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_target_alias2(self):
        macro = u'''/cast [@target] Test'''    
        int_correct = [[None, u'Cast Test on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_target_alias3(self):
        macro = u'''/cast [@player] Test'''    
        int_correct = [[None, u'Cast Test on you']]
        self.macro_test(macro, int_correct)        

    def test_target_alias4(self):
        macro = u'''/cast [@Fitzcairn] Test'''    
        int_correct = [[None, u'Cast Test on Fitzcairn']]
        self.macro_test(macro, int_correct)

    def test_target_alias5(self):
        macro = u'''/cast [@focus,harm,exists] Test'''    
        int_correct = [['If the unit saved as your focus target is an enemy and exists then:', u'Cast Test on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_target_alias6(self):
        macro = u'''/cast [@player,harm,exists] Test'''    
        int_correct = [['If you are an enemy and exist then:', u'Cast Test on you']]
        self.macro_test(macro, int_correct)                

    def test_target_alias7(self):
        macro = u'''/cast [@target,combat,harm,exists] Test'''    
        int_correct = [['If you are in combat and the currently targeted unit is an enemy and exists then:', u'Cast Test on the currently targeted unit']]
        self.macro_test(macro, int_correct)                

    # This should render an exception, but right now its failing.
    def test_tell_exception(self):
        macro = u'''/tell Test'''    
        int_correct = [[None, u'Whisper nothing to Test']]
        self.macro_test(macro, int_correct)

    # Test all the parameter combinations of roll.
    def test_roll1(self):
        macro = u'''/roll'''    
        int_correct = [[None, 'Roll a number between 1 and 100']]
        self.macro_test(macro, int_correct)

    def test_roll2(self):
        macro = u'''/roll 1'''    
        int_correct = [[None, 'Roll a number between 1 and 1']]
        self.macro_test(macro, int_correct)

    def test_roll3(self):
        macro = u'''/roll 1 2'''    
        int_correct = [[None, 'Roll a number between 1 and 2']]
        self.macro_test(macro, int_correct)

    def test_roll4(self):
        macro = u'''/roll 0 1'''    
        int_correct = [[None, 'Roll a number between 0 and 1']]
        self.macro_test(macro, int_correct)

    def test_roll5(self):
        macro = u'''/roll -1 -3'''    
        int_correct = [[None, 'Roll a number between 1 and 100']]
        self.macro_test(macro, int_correct)

    def test_roll6(self):
        macro = u'''/roll sadf sadga'''    
        int_correct = [[None, 'Roll a number between 1 and 100']]
        self.macro_test(macro, int_correct)


    def test_follow(self):
        macro = u'''/f'''
        self.assertRaises(ParseErrorInsecureVerbReqTgt, self.macro_test, macro, None)


    # Test all the who command.
    def test_who1(self):
        macro = u'''/who'''    
        int_correct = [[None, 'Get a list of online players']]
        self.macro_test(macro, int_correct)

    def test_who2(self):
        macro = u'''/who Steve'''    
        int_correct = [[None, u'Get a list of online players with attributes matching: Steve']]
        self.macro_test(macro, int_correct)

    def test_who3(self):
        macro = u'''/who Boomstick Saints'''    
        int_correct = [[None, u'Get a list of online players with attributes matching: Boomstick Saints']]
        self.macro_test(macro, int_correct)

    # Test show/showtooltip for all the various parameter
    # types.
    def test_show_param_types1(self):
        macro = u'''#show 17'''    
        int_correct = [[None, 'Show icon and cooldown for item equipped as your off-hand weapon, two-hand weapon, or shield for this macro on the action bar']]
        self.macro_test(macro, int_correct)

    def test_show_param_types2(self):
        macro = u'''#show 1 12'''    
        int_correct = [[None, u'Show icon and cooldown for item in bag 1, bag slot 12 for this macro on the action bar']]
        self.macro_test(macro, int_correct)

    def test_show_param_types3(self):
        macro = u'''#show Item Name'''    
        int_correct = [[None, u'Show icon and cooldown for Item Name for this macro on the action bar']]
        self.macro_test(macro, int_correct)

    # Test to make sure we're rendering the key unit correctly
    def test_key_unit_default1(self):
        macro = u'''/focus [target=focus,noexists]'''
        int_correct = [['If the unit saved as your focus target does not exist then:', 'Set your focus target to the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_key_unit_default2(self):
        macro = u'''/focus [target=player,combat] Fitz'''
        int_correct = [['If you are in combat then:', 'Set your focus target to you']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default3(self):
        macro = u'''/focus [target=focus,combat,exists] partypet1'''
        int_correct = [['If you are in combat and the unit saved as your focus target exists then:', u'Set your focus target to the pet of party member 1']]
        self.macro_test(macro, int_correct)       

        # No longer a valid test since changes to allow
        # clear target commands.
        #macro = u'''/target [target=target,exists]'''
        #self.assertRaises(ParseErrorParamRequired, self.macro_test, macro, None)

    def test_key_unit_default4(self):
        macro = u'''/target [target=target,exists] Fitz'''
        int_correct = [['If the currently targeted unit exists then:', u'Set target to Fitz']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default5(self):
        macro = u'''/target [target=focus,noexists] Fitz'''
        int_correct = [['If the unit saved as your focus target does not exist then:', 'Set target to the unit saved as your focus target']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default6(self):
        macro = u'''/startattack [target=focus,noexists]'''
        int_correct = [['If the unit saved as your focus target does not exist then:', 'Start attacking the unit saved as your focus target']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default7(self):
        macro = u'''/startattack [target=focus,noexists] Fitz'''
        int_correct = [['If the unit saved as your focus target does not exist then:', 'Start attacking the unit saved as your focus target']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default8(self):
        macro = u'''/startattack [target=target,noexists]'''
        int_correct = [['If the currently targeted unit does not exist then:', 'Start attacking the currently targeted unit']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default9(self):
        macro = u'''/startattack [target=target,noexists] Fitz'''
        int_correct = [['If the currently targeted unit does not exist then:', u'Start attacking Fitz']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default10(self):
        macro = u'''/startattack [target=target,noexists] arena1'''
        int_correct = [['If the currently targeted unit does not exist then:', u'Start attacking enemy Arena player 1']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default11(self):
        macro = u'''/petattack [target=pettarget,noexists]'''
        int_correct = [["If your pet's currently targeted unit does not exist then:", 'Order your pet to attack the currently targeted unit']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default12(self):
        macro = u'''/petattack [target=pettarget,noexists] Fitz'''
        int_correct = [["If your pet's currently targeted unit does not exist then:", u'Order your pet to attack Fitz']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default13(self):
        macro = u'''/petattack [target=focus,noexists]'''
        int_correct = [['If the unit saved as your focus target does not exist then:', 'Order your pet to attack the unit saved as your focus target']]
        self.macro_test(macro, int_correct)       

    def test_key_unit_default14(self):
        macro = u'''/petattack [target=focus,noexists] Fitz'''
        int_correct = [['If the unit saved as your focus target does not exist then:', 'Order your pet to attack the unit saved as your focus target']]
        self.macro_test(macro, int_correct)       


    # Broken command from site
    def test_broken_at_target(self):
        macro = u'''/cast [@focus unithasvehicleui]Blizzard'''
        self.assertRaises(LexErrorNoMatchingRules, self.macro_test, macro, None)

    # Another broken test--this one went live! :(
    # Test targeting commands with various parameter combos.
    def test_broken_focus_w_invalid_target(self):
        macro = u'''/focus [exists]'''
        int_correct = [['If the currently targeted unit exists then:', 'Set your focus target to the currently targeted unit']]
        self.macro_test(macro, int_correct)               

    def test_broken_focus_w_invalid_target2(self):
        macro = u'''/focus [exists] Test'''
        int_correct = [['If the currently targeted unit exists then:', u'Set your focus target to Test']]
        self.macro_test(macro, int_correct)               

    def test_broken_focus_w_invalid_target3(self):
        macro = u'''/focus [exists] Test Unit'''
        int_correct = [['If the currently targeted unit exists then:', u'Set your focus target to Test Unit']]
        self.macro_test(macro, int_correct)               

    def test_broken_focus_w_invalid_target4(self):
        macro = u'''/focus [exists] mouseover'''
        int_correct = [['If the currently targeted unit exists then:', 'Set your focus target to the unit your mouse is currently over']]
        self.macro_test(macro, int_correct)

    def test_broken_focus_w_invalid_target5(self):
        macro = u'''/focus [exists] Tremor Totem'''
        self.assertRaises(ParseErrorTargetTotem, self.macro_test, macro, None)

    def test_broken_focus_w_invalid_target6(self):
        macro = u'''/focus [exists] Totem'''
        int_correct = [['If the currently targeted unit exists then:', u'Set your focus target to Totem']]
        self.macro_test(macro, int_correct)               


    def test_targetexact(self):
        macro = u'''/targetexact Fitzcairn'''
        int_correct = [[None, u'Set target to visible unit named exactly Fitzcairn']]
        self.macro_test(macro, int_correct)               

    def test_targetexact_target_keywords(self):
        macro = u'''/targetexact Fitzcairn-target'''
        int_correct = [[None, u'Set target to visible unit named exactly Fitzcairn-target']]
        self.macro_test(macro, int_correct)               

        
    # Tests for the cycle commands
    def test_targetcycling1(self):
        macro = u'''/targetenemy'''
        int_correct = [[None, 'Target next visible enemy unit']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling2(self):
        macro = u'''/targetenemy 1'''
        int_correct = [[None, 'Target next visible enemy unit in reverse order']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling3(self):
        macro = u'''/targetenemy 425'''
        int_correct = [[None, 'Target next visible enemy unit in reverse order']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling4(self):
        macro = u'''/targetenemy sxc'''
        self.assertRaises(ParseErrorWrongParams, self.macro_test, macro, None)

    def test_targetcycling5(self):
        macro = u'''/targetenemyplayer'''
        int_correct = [[None, 'Target next visible enemy player']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling6(self):
        macro = u'''/targetenemyplayer 1'''
        int_correct = [[None, 'Target next visible enemy player in reverse order']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling7(self):
        macro = u'''/targetenemyplayer sdv'''
        self.assertRaises(ParseErrorWrongParams, self.macro_test, macro, None)

    def test_targetcycling8(self):
        macro = u'''/targetfriend'''
        int_correct = [[None, 'Target next visible friendly unit']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling9(self):
        macro = u'''/targetfriend 1'''
        int_correct = [[None, 'Target next visible friendly unit in reverse order']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling10(self):
        macro = u'''/targetfriend adfasdg'''
        self.assertRaises(ParseErrorWrongParams, self.macro_test, macro, None)

    def test_targetcycling11(self):
        macro = u'''/targetparty'''
        int_correct = [[None, 'Target next visible party member']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling12(self):
        macro = u'''/targetparty 1'''
        int_correct = [[None, 'Target next visible party member in reverse order']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling13(self):
        macro = u'''/targetparty asd'''
        self.assertRaises(ParseErrorWrongParams, self.macro_test, macro, None)

    def test_targetcycling14(self):
        macro = u'''/targetraid'''
        int_correct = [[None, 'Target next visible party or raid member']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling15(self):
        macro = u'''/targetraid 1'''
        int_correct = [[None, 'Target next visible party or raid member in reverse order']]
        self.macro_test(macro, int_correct)               

    def test_targetcycling16(self):
        macro = u'''/targetraid asd'''
        self.assertRaises(ParseErrorWrongParams, self.macro_test, macro, None)


    # Test to make sure option default targets are honored.
    def test_def_option_target(self):
        macro = u'''/targetexact [exists] Test Unit'''
        int_correct = [['If the currently targeted unit exists then:', u'Set target to visible unit named exactly Test Unit']]
        self.macro_test(macro, int_correct)                   

    # Test to make sure option default targets are honored.
    def test_empty_sequence(self):
        macro = u'''/castsequence reset=combat ,,Potion of Wild Magic,'''
        int_correct = [[None, u'Cast the next spell in a sequence of [ nothing, nothing, Potion of Wild Magic on the currently targeted unit, nothing ] each time the macro is activated, resetting the sequence if you leave combat']]
        self.macro_test(macro, int_correct)                   


    # Test international chars
    def test_i18n(self):
        macro = u'''/castsequence [stance:2] reset=10 Heurt de bouclier, Dévaster, Dévaster, Dévaster, Coup de tonnerre'''
        int_correct = [[u'If you are in stance 2 then:', u'Cast the next spell in a sequence of [ Heurt de bouclier on the currently targeted unit, D\xe9vaster on the currently targeted unit, D\xe9vaster on the currently targeted unit, D\xe9vaster on the currently targeted unit, Coup de tonnerre on the currently targeted unit ] each time the macro is activated, resetting the sequence after 10 seconds']]
        self.macro_test(macro, int_correct)                   

    # Another broken macro
    def test_afk(self):
        macro = u'''/afk lala'''
        int_correct = [[None, u'Set your status to Away From Keyboard with status message: lala']]
        self.macro_test(macro, int_correct)                   

    # Another broken macro
    def test_empty_after_use(self):
        macro = u'''/use [stance:1]Growl;'''
        int_correct = [[u'If you are in stance 1 then:', u'Use your Growl'], ['Otherwise:', 'Use your nothing']]
        self.macro_test(macro, int_correct)                   

    # Another broken macro
    def test_broken_click(self):
        macro = u'''/click [nomod] ORLOpen OPieRaidSymbols;'''
        int_correct = [['If you were not holding any modifier key down then:', u'Automatically click button: ORLOpen OPieRaidSymbols'], ['Otherwise:', 'Automatically click button: nothing']]
        self.macro_test(macro, int_correct)                   


    #def test_broken_encoding(self):
    #    macro = u'/w \xe2\x80\x9cHealing %t in 3 seconds.\xe2\x80\x9d'
    #    int_correct = []
    #    self.macro_test(macro, int_correct)                   

    def test_broken_equip_macro(self):
        macro = u'''/equip [noequipped: Fishing Pole,nomod:shift] Fishing Pole;'''
        int_correct = [[u'If you have not equipped item or itemtype Fishing Pole and were not holding the shift key then:', u'Equip your Fishing Pole in its default slot'], ['Otherwise:', 'Equip your nothing in its default slot']]
        self.macro_test(macro, int_correct)
        
              
    def test_assist_empty_command_obj(self):
        macro = '''/assist [combat] X;'''
        int_correct = [['If you are in combat then:', u'Set your target to the target of X'], ['Otherwise:', 'Set your target to the target of the currently targeted unit']]
        self.macro_test(macro, int_correct)


    def test_cancelaura_empty_command_obj(self):
        macro = '''/cancelaura [combat] X;'''
        int_correct = [['If you are in combat then:', u'Remove X from yourself'], ['Otherwise:', 'Remove nothing from yourself']]
        self.macro_test(macro, int_correct)


    def test_cancelform_empty_command_obj(self):
        macro = '''/cancelform [combat] X;'''
        int_correct = [['If you are in combat then:', u'Cancel a stance, form, or stealth X'], ['Otherwise:', 'Cancel a stance, form, or stealth']]
        self.macro_test(macro, int_correct)


    def test_cast_empty_command_obj(self):
        macro = '''/cast [combat] X;'''
        int_correct = [['If you are in combat then:', u'Cast X on the currently targeted unit'], ['Otherwise:', 'Cast nothing on the currently targeted unit']]
        self.macro_test(macro, int_correct)


    def test_castrandom_empty_command_obj(self):
        macro = '''/castrandom [combat] X;'''
        int_correct = [['If you are in combat then:', 'Cast a random spell from a set of [ X on the currently targeted unit ] each time the macro is activated'], ['Otherwise:', 'Cast a random spell from a set of [ nothing ] on the currently targeted unit each time the macro is activated']]
        self.macro_test(macro, int_correct)


    def test_castsequence_empty_command_obj(self):
        macro = '''/castsequence [combat] X;'''
        int_correct = [['If you are in combat then:', 'Cast the next spell in a sequence of [ X on the currently targeted unit ] each time the macro is activated'], ['Otherwise:', 'Cast the next spell in a sequence of [ nothing ] on the currently targeted unit each time the macro is activated']]
        self.macro_test(macro, int_correct)


    def test_changeactionbar_empty_command_obj(self):
        macro = '''/changeactionbar [combat] 1;'''
        int_correct = [['If you are in combat then:', u'Change your active action bar to bar 1'], ['Otherwise:', 'Change your active action bar to']]
        self.macro_test(macro, int_correct)


    def test_clearfocus_empty_command_obj(self):
        macro = '''/clearfocus [combat] X;'''
        int_correct = [['If you are in combat then:', u'Clear your focus target X'], ['Otherwise:', 'Clear your focus target']]
        self.macro_test(macro, int_correct)


    def test_cleartarget_empty_command_obj(self):
        macro = '''/cleartarget [combat] X;'''
        int_correct = [['If you are in combat then:', u'Clear your target X'], ['Otherwise:', 'Clear your target']]
        self.macro_test(macro, int_correct)


    def test_click_empty_command_obj(self):
        macro = '''/click [combat] X;'''
        int_correct = [['If you are in combat then:', u'Automatically click button: X'], ['Otherwise:', 'Automatically click button: nothing']]
        self.macro_test(macro, int_correct)


    def test_dismount_empty_command_obj(self):
        macro = '''/dismount [combat] X;'''
        int_correct = [['If you are in combat then:', u'Dismount X'], ['Otherwise:', 'Dismount']]
        self.macro_test(macro, int_correct)


    def test_equip_empty_command_obj(self):
        macro = '''/equip [combat] X;'''
        int_correct = [['If you are in combat then:', u'Equip your X in its default slot'], ['Otherwise:', 'Equip your nothing in its default slot']]
        self.macro_test(macro, int_correct)


    def test_equipset_empty_command_obj(self):
        macro = '''/equipset [combat] X;'''
        int_correct = [['If you are in combat then:', u"Equip equipment set 'X' via the Equipment Manager"], ['Otherwise:', "Equip equipment set 'nothing' via the Equipment Manager"]]
        self.macro_test(macro, int_correct)


    def test_equipslot_empty_command_obj(self):
        macro = '''/equipslot [combat] 12 X;'''
        int_correct = [['If you are in combat then:', u'Equip your X as your second ring'], ['Otherwise:', 'Equip nothing']]
        self.macro_test(macro, int_correct)


    def test_focus_empty_command_obj(self):
        macro = '''/focus [combat] X;'''
        int_correct = [['If you are in combat then:', u'Set your focus target to X'], ['Otherwise:', 'Set your focus target to the currently targeted unit']]
        self.macro_test(macro, int_correct)


    def test_petagressive_empty_command_obj(self):
        macro = '''/petagressive [combat] X;'''
        int_correct = [['If you are in combat then:', 'Turn on pet aggressive mode, canceling other modes'], ['Otherwise:', 'Turn on pet aggressive mode, canceling other modes']]
        self.macro_test(macro, int_correct)


    def test_petattack_empty_command_obj(self):
        macro = '''/petattack [combat] X;'''
        int_correct = [['If you are in combat then:', u'Order your pet to attack X'], ['Otherwise:', 'Order your pet to attack the currently targeted unit']]
        self.macro_test(macro, int_correct)


    def test_petautocastoff_empty_command_obj(self):
        macro = '''/petautocastoff [combat] X;'''
        int_correct = [['If you are in combat then:', u'Turn off pet skill autocast for X'], ['Otherwise:', 'Turn off pet skill autocast for']]
        self.macro_test(macro, int_correct)


    def test_petautocaston_empty_command_obj(self):
        macro = '''/petautocaston [combat] X;'''
        int_correct = [['If you are in combat then:', u'Turn on pet skill autocast for X'], ['Otherwise:', 'Turn on pet skill autocast for']]
        self.macro_test(macro, int_correct)


    def test_petautocasttoggle_empty_command_obj(self):
        macro = '''/petautocasttoggle [combat] X;'''
        int_correct = [['If you are in combat then:', u'Change pet skill autocast state for X'], ['Otherwise:', 'Change pet skill autocast state for']]
        self.macro_test(macro, int_correct)


    def test_petdefensive_empty_command_obj(self):
        macro = '''/petdefensive [combat] X;'''
        int_correct = [['If you are in combat then:', 'Turn on pet defensive mode, canceling other modes'], ['Otherwise:', 'Turn on pet defensive mode, canceling other modes']]
        self.macro_test(macro, int_correct)


    def test_petfollow_empty_command_obj(self):
        macro = '''/petfollow [combat] X;'''
        int_correct = [['If you are in combat then:', 'Turn on pet follow mode, canceling other modes'], ['Otherwise:', 'Turn on pet follow mode, canceling other modes']]
        self.macro_test(macro, int_correct)


    def test_petpassive_empty_command_obj(self):
        macro = '''/petpassive [combat] X;'''
        int_correct = [['If you are in combat then:', 'Turn on pet passive mode, canceling other modes'], ['Otherwise:', 'Turn on pet passive mode, canceling other modes']]
        self.macro_test(macro, int_correct)


    def test_petstay_empty_command_obj(self):
        macro = '''/petstay [combat] X;'''
        int_correct = [['If you are in combat then:', 'Turn on pet stay mode, canceling other modes'], ['Otherwise:', 'Turn on pet stay mode, canceling other modes']]
        self.macro_test(macro, int_correct)


    def test_show_empty_command_obj(self):
        macro = '''#show [combat] X;'''
        int_correct = [['If you are in combat then:', u'Show icon and cooldown for X for this macro on the action bar'], ['Otherwise:', 'Show icon and cooldown for the first item or spell in this macro on the action bar']]
        self.macro_test(macro, int_correct)


    def test_showcooldown_empty_command_obj(self):
        macro = '''#showcooldown [combat] X;'''
        int_correct = [['If you are in combat then:', u'Show cooldown for X for this macro on the action bar'], ['Otherwise:', 'Show cooldown for the first item or spell in this macro on the action bar']]
        self.macro_test(macro, int_correct)


    def test_showtooltip_empty_command_obj(self):
        macro = '''#showtooltip [combat] X;'''
        int_correct = [['If you are in combat then:', u'Show tooltip, icon, and cooldown for X for this macro on the action bar'], ['Otherwise:', 'Show tooltip, icon, and cooldown for the first item or spell in this macro on the action bar']]
        self.macro_test(macro, int_correct)


    def test_startattack_empty_command_obj(self):
        macro = '''/startattack [combat] X;'''
        int_correct = [['If you are in combat then:', u'Start attacking X'], ['Otherwise:', 'Start attacking the currently targeted unit']]
        self.macro_test(macro, int_correct)


    def test_stopattack_empty_command_obj(self):
        macro = '''/stopattack [combat] X;'''
        int_correct = [['If you are in combat then:', u'Stop attacking X'], ['Otherwise:', 'Stop attacking']]
        self.macro_test(macro, int_correct)


    def test_stopcasting_empty_command_obj(self):
        macro = '''/stopcasting [combat] X;'''
        int_correct = [['If you are in combat then:', u'Stop all casting X'], ['Otherwise:', 'Stop all casting']]
        self.macro_test(macro, int_correct)


    def test_stopmacro_empty_command_obj(self):
        macro = '''/stopmacro [combat] X;'''
        int_correct = [['If you are in combat then:', u'Stop this macro X'], ['Otherwise:', 'Stop this macro']]
        self.macro_test(macro, int_correct)


    def test_swapactionbar_empty_command_obj(self):
        macro = '''/swapactionbar [combat] 1 2;'''
        int_correct = [['If you are in combat then:', u'Swap active action bar from bar 1 to bar 2 if bar 1 is active, otherwise switch to bar 1'], ['Otherwise:', 'Swap active action bar to']]
        self.macro_test(macro, int_correct)


    def test_tar_empty_command_obj(self):
        macro = '''/tar [combat] X;'''
        int_correct = [['If you are in combat then:', 'Set target to X'], ['Otherwise:', 'Set target to nothing']]
        self.macro_test(macro, int_correct)


    def test_target_empty_command_obj(self):
        macro = '''/target [combat] X;'''
        int_correct = [['If you are in combat then:', 'Set target to X'], ['Otherwise:', 'Set target to nothing']]
        self.macro_test(macro, int_correct)


    def test_targetenemy_empty_command_obj(self):
        macro = '''/targetenemy [combat] 1;'''
        int_correct = [['If you are in combat then:', 'Target next visible enemy unit in reverse order'], ['Otherwise:', 'Target next visible enemy unit']]
        self.macro_test(macro, int_correct)


    def test_targetenemyplayer_empty_command_obj(self):
        macro = '''/targetenemyplayer [combat] 1;'''
        int_correct = [['If you are in combat then:', 'Target next visible enemy player in reverse order'], ['Otherwise:', 'Target next visible enemy player']]
        self.macro_test(macro, int_correct)


    def test_targetexact_empty_command_obj(self):
        macro = '''/targetexact [combat] X;'''
        int_correct = [['If you are in combat then:', 'Set target to visible unit named exactly X'], ['Otherwise:', 'Set target to nothing']]
        self.macro_test(macro, int_correct)


    def test_targetfriend_empty_command_obj(self):
        macro = '''/targetfriend [combat] 1;'''
        int_correct = [['If you are in combat then:', 'Target next visible friendly unit in reverse order'], ['Otherwise:', 'Target next visible friendly unit']]
        self.macro_test(macro, int_correct)


    def test_targetfriendplayer_empty_command_obj(self):
        macro = '''/targetfriendplayer [combat] 1;'''
        int_correct = [['If you are in combat then:', 'Target next visible friendly player in reverse order'], ['Otherwise:', 'Target next visible friendly player']]
        self.macro_test(macro, int_correct)


    def test_targetlastenemy_empty_command_obj(self):
        macro = '''/targetlastenemy [combat] X;'''
        int_correct = [['If you are in combat then:', u'Target the last enemy unit you had targeted X'], ['Otherwise:', 'Target the last enemy unit you had targeted']]
        self.macro_test(macro, int_correct)


    def test_targetlastfriend_empty_command_obj(self):
        macro = '''/targetlastfriend [combat] X;'''
        int_correct = [['If you are in combat then:', u'Target the last friendly unit you had targeted X'], ['Otherwise:', 'Target the last friendly unit you had targeted']]
        self.macro_test(macro, int_correct)


    def test_targetlasttarget_empty_command_obj(self):
        macro = '''/targetlasttarget [combat] X;'''
        int_correct = [['If you are in combat then:', u'Target your last target X'], ['Otherwise:', 'Target your last target']]
        self.macro_test(macro, int_correct)


    def test_targetparty_empty_command_obj(self):
        macro = '''/targetparty [combat] 1;'''
        int_correct = [['If you are in combat then:', 'Target next visible party member in reverse order'], ['Otherwise:', 'Target next visible party member']]
        self.macro_test(macro, int_correct)


    def test_targetraid_empty_command_obj(self):
        macro = '''/targetraid [combat] 1;'''
        int_correct = [['If you are in combat then:', 'Target next visible party or raid member in reverse order'], ['Otherwise:', 'Target next visible party or raid member']]
        self.macro_test(macro, int_correct)


    def test_use_empty_command_obj(self):
        macro = '''/use [combat] X;'''
        int_correct = [['If you are in combat then:', u'Use your X'], ['Otherwise:', 'Use your nothing']]
        self.macro_test(macro, int_correct)


    def test_userandom_empty_command_obj(self):
        macro = '''/userandom [combat] X;'''
        int_correct = [['If you are in combat then:', 'Use a randomly selected item from [ X ]'], ['Otherwise:', 'Use a randomly selected item from [ nothing ]']]
        self.macro_test(macro, int_correct)


    def test_usetalents_empty_command_obj(self):
        macro = '''/usetalents [combat] 1;'''
        int_correct = [['If you are in combat then:', u'Activate talent set 1'], ['Otherwise:', 'Activate talent set nothing']]
        self.macro_test(macro, int_correct)

    def test_comments(self):
        macro = '''--/startattack;'''
        int_correct = [[None, u'Commented line, will not be evaluated: --/startattack;']]
        self.macro_test(macro, int_correct)


    # Bug found/fixed 4/13/2010
    def test_stopmacro_bug(self):
        macro = '''/targetenemy [mod:shift] 1 ; [] 0
/stopmacro [mod:ctrl][mod:alt][target=focus,noexists][target=focus,harm][target=focus,dead][target=focustarget,noexists][target=focustarget,dead][target=focustarget,help]
/target focustarget'''
        int_correct = [['If you were holding the shift key then:', 'Target next visible enemy unit in reverse order'], ['Otherwise:', 'Target next visible enemy unit'], ['If you were holding the control key then:', 'Stop this macro'], ['Else, if you were holding the alt key then:', 'Stop this macro'], ['Else, if the unit saved as your focus target does not exist then:', 'Stop this macro'], ['Else, if the unit saved as your focus target is an enemy then:', 'Stop this macro'], ['Else, if the unit saved as your focus target is dead then:', 'Stop this macro'], ["Else, if the unit saved as your focus target's currently targeted unit does not exist then:", 'Stop this macro'], ["Else, if the unit saved as your focus target's currently targeted unit is dead then:", 'Stop this macro'], ["Else, if the unit saved as your focus target's currently targeted unit is a friend then:", 'Stop this macro'], [None, "Set target to the unit saved as your focus target's currently targeted unit"]]
        self.macro_test(macro, int_correct)

    def test_complex_targeting1(self):
        macro = "/target raid2-target-pet"
        int_correct = [[None, u"Set target to the raid member 2's currently targeted unit's pet"]]
        self.macro_test(macro, int_correct)

    def test_complex_targeting2(self):
        macro = "/target raid2targetpet"
        int_correct = [[None, u"Set target to the raid member 2's currently targeted unit's pet"]]
        self.macro_test(macro, int_correct)

    def test_complex_targeting3(self):
        macro = "/target Tess-target-pet"
        int_correct = [[None, u"Set target to Tess's currently targeted unit's pet"]]
        self.macro_test(macro, int_correct)

    def test_complex_targeting4(self):
        macro = "/target Néto-target"
        int_correct = [[None, "Set target to Néto's currently targeted unit"]]
        self.macro_test(macro, int_correct)

    # Test parsing for option args that modify targeting
    def test_target_option_args1(self):
        macro = "/cast [mod:FOCUSCAST]Spell"
        int_correct = [['If you were holding the focus-cast key then:', 'Cast Spell on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_target_option_args2(self):
        macro = "/cast [target=player,mod:FOCUSCAST]Spell"
        int_correct = [['If you were holding the focus-cast key then:', 'Cast Spell on you']]
        self.macro_test(macro, int_correct)

    def test_target_option_args3(self):
        macro = "/cast [mod:SELFCAST]Spell"
        int_correct = [['If you were holding the self-cast key (def: alt) then:', 'Cast Spell on you']]
        self.macro_test(macro, int_correct)

    def test_target_option_args4(self):
        macro = "/cast [target=focus,mod:SELFCAST]Spell"
        int_correct = [['If you were holding the self-cast key (def: alt) then:', 'Cast Spell on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_target_option_args5(self):
        macro = "/cast [mod:SELFCAST/FOCUSCAST]Spell"
        int_correct = [['If you were holding the self-cast key (def: alt) or focus-cast key then:', 'Cast Spell on the player or focus, depending on which key was down when the macro was activated.']]
        self.macro_test(macro, int_correct)

    def test_target_option_args6(self):
        macro = "/cast [mod:SELFCAST/FOCUSCAST/SELFCAST/FOCUSCAST]Spell"
        int_correct = [['If you were holding the self-cast key (def: alt) or focus-cast key then:', 'Cast Spell on the player or focus, depending on which key was down when the macro was activated.']]
        self.macro_test(macro, int_correct)

    def test_target_option_args7(self):
        macro = "/cast [mod:SELFCAST, target=focus]Spell"
        int_correct = [['If you were holding the self-cast key (def: alt) then:', 'Cast Spell on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    # Collapsing repeated arguments
    def test_repeated_args1(self):
        macro = "/cast [mod:alt/shift/alt/shift/shift] Spell"
        int_correct = [['If you were holding the shift key or alt key then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    # Better phrasing on chains
    def test_target_chain(self):
        macro = '''/cast [target=playertargettargettarget] Spell 1'''
        int_correct = [[None, "Cast Spell 1 on your currently targeted unit's currently targeted unit's currently targeted unit"]]
        self.macro_test(macro, int_correct)

    # Bug found on site.
    def test_site_tar_bug(self):
        macro = '''/tar [nodead] Val'''
        int_correct = [['If the currently targeted unit is not dead then:', 'Set target to Val']]
        self.macro_test(macro, int_correct)

    # Test removing repeated phrases
    def test_repeated_phrases1(self):
        macro = '''/cast [mod:alt, combat, mod:alt, combat] Spell'''
        int_correct = [['If you were holding the alt key and are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    # Ensure that even with repeated arguments we can remove repeated
    # phrases
    def test_repeated_phrases2(self):
        macro = '''/cast [mod:alt/alt,combat, combat, mod:alt]Spell'''
        int_correct = [['If you were holding the alt key and are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    # Repeated args with strange cases
    def test_repeated_phrases3(self):
        macro = '''/cast [mod:alt/ALT,combat, combat, mod:ALT]Spell'''
        int_correct = [['If you were holding the alt key and are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    # Repeated conditions
    def test_repeated_condition1(self):
        macro = '''/cast [combat] [combat] Spell'''
        int_correct = [['If you are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition2(self):
        macro = '''/cast [combat] [combat] [combat] Spell'''
        int_correct = [['If you are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition3(self):
        macro = '''/cast [] [] Spell'''
        int_correct = [[None, 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition4(self):
        macro = '''/cast [combat] [] [combat] Spell'''
        int_correct = [['If you are in combat then:', 'Cast Spell on the currently targeted unit'], ['Otherwise:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition5(self):
        macro = '''/cast [combat] [harm] [combat] [harm] Spell'''
        int_correct = [['If you are in combat then:', 'Cast Spell on the currently targeted unit'], ['Else, if the currently targeted unit is an enemy then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition6(self):
        macro = '''/cast [combat] [@focus, harm] [combat] [target=focus, harm] Spell'''
        int_correct = [['If you are in combat then:', 'Cast Spell on the currently targeted unit'], ['Else, if the unit saved as your focus target is an enemy then:', 'Cast Spell on the unit saved as your focus target']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition7(self):
        macro = '''/cast [mod:alt/alt/alt] [mod:alt] Spell'''
        int_correct = [['If you were holding the alt key then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition8(self):
        macro = '''/cast [mod:alt/alt/alt] [combat] [mod:alt] Spell'''
        int_correct = [['If you were holding the alt key then:', 'Cast Spell on the currently targeted unit'], ['Else, if you are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition9(self):
        macro = '''/cast [mod:alt] [combat] [mod:alt/alt/alt] Spell'''
        int_correct = [['If you were holding the alt key then:', 'Cast Spell on the currently targeted unit'], ['Else, if you are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition_reordered(self):
        macro = '''/cast [mod:alt,combat][combat,mod:alt]Spell'''
        int_correct = [['If you were holding the alt key and are in combat then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    def test_repeated_condition_ultimate(self):
        macro = '''/cast [target=focus, stealth][mod:alt,combat,mod:alt/shift/alt][stealth, @focus][mod:alt/alt/shift, combat,mod:alt]Spell'''
        int_correct = [['If you are stealthed then:', 'Cast Spell on the unit saved as your focus target'], ['Else, if you were holding the alt key, are in combat, and were holding the shift key or alt key then:', 'Cast Spell on the currently targeted unit']]
        self.macro_test(macro, int_correct)

    # broken on live
    def test_repeated_meta_commands(self):
        macro = '''#showtooltip Tricks of the Trade
        #showtooltip Tricks of the Trade
        /cast [help][target=focus,help][target=targettarget,help]Tricks of the Trade'''
        self.assertRaises(InterpetErrorSingleUseCommandViolated, self.macro_test, macro, None)

    # Bad spacing found on live with verbs that take a list
    def test_bad_target_spacing(self):
        macro = '''/castrandom [ target = target, harm , exists ] Spell'''
        int_correct = [['If the currently targeted unit is an enemy and exists then:', 'Cast a random spell from a set of [ Spell on the currently targeted unit ] each time the macro is activated']]
        self.macro_test(macro, int_correct)


if __name__ == '__main__':
    # Run all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInterpreter)

    # Run just one test
    if DEBUG:
        suiteOne = unittest.TestSuite()
        suiteOne.addTest(TestInterpreter("test_i18n"))
        unittest.TextTestRunner(verbosity=2).run(suiteOne)
    else:
        unittest.TextTestRunner(verbosity=2).run(suite)


