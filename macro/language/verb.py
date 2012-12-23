''' Language specification for the WoW Macro language.

Verbs.
'''
from macro.language.base                import LanguagePart
from macro.interpret.assemble_functions import *

# Class describing Verbs
class Verb(LanguagePart):
    ''' Class describing command verb characteristics.  In short:

    INTERPRETATION:

    param_function
      An extra helper function to assemble parameters specific to this
      verb.
      Default get_assembled_parameter from assemble_functions


    VERB:

     comment: (Optional)
      Whether or not this verb is a commented line.
      Default False

     meta: (Optional)
      If this is a metaverb (i.e. does not affect game world)
      Default False

     secure: (Optional)
      Verb is secure (can accept options).  If this is false,
      treat everything after the verb as a parameter.  By default,
      every /command not in the map is handled like this.
      Default False

     only_usable_once: (Optional)
      Some commands can only be used once per macro.  Example is
      /targetenemy.
      Default False
 
     gcd: (Optional)
      Whether or not this command automatically triggers the GCD.
      Data driven.
      Default False

     allow_reset: (Optional)
      Whether or not this command allows use of the reset= statement,
      which comes after the conditions and before the parameters.
      Default False
      
     related: (Optional)
      Some verbs have a set of related verbs where only one command out
      of the set may be used per macro.
      Default []
      

    PARAMETERS:

     allow_toggle: (Optional)
      Some verbs allow for toggle-able parameters.  Example:
         /cast !Stealth
      This means that we will NOT turn off stealth if we are stealthed
      already.
      Default False

     param_req: (Optional)
      Set to true if the interpretation of this verb makes no sense
      without mentioning a parameter.  Shortcut for None not being in
      the param set (see below.
      Default False

     param: (Optional)
      Describe what parameters are taken by a given verb, if any.  A
      list of tuples, or None if the parameter cant take params.  Each
      tuple contains an accepted pattern.  Each tuple element is a
      type of parameter.  Accepted set entries are str, int, None

      For example, /use:

        /use Sword of Truth
        /use 14 (slot number)
        /use 12 13 (bag slot id)

      ...will have the following param_pattern:

        set([(str),(int),(int, int)] )

      Some verbs can take multiple parameters in list form.  Example:

        /castsequence Spell 1
        /castsequence Spell 1, Spell2, Spell 3

      This is described as:

        set([(str,)])

      ...and the "takes_list" attribute is set to True to indicate that
      a list of indeterminate length of these parameters is accepted.

      Some parameters can take specific params, but do not require
      them.  Example:

        /targetfriend
        /targetfriend 1

      This is described as:

        set([(int,), None])

      This is useful because non-int parameters are NOT recognized by
      this macro command.
      Default is None

     takes_units: (Optional)
      Some commands accept units directly as their parameters. Example:
        /target party1
      will target your first party member.
      Default False

     takes_spell: (Optional)
      Whether or not the command casts a spell
      Default False

     takes_item: (Optional)
      Whether or not this command takes an item.
      Default False

     takes_int: (Optional)
      Convienience method indicating one of the parameter patterns is
      comprised entirely of type int.
      Default False.

     takes_list: (Optional)
      Whether or not this command can accept a list of the types given
      in the param attribute where the list is of indeterminate length.
      Default False
      

    TARGETS

     key_unit
      The key unit is a unit you can use in [target=] that will allow
      you to send another unit to the command. The Default Unit is the
      unit that will be sent to the command if you dont provide one.
      Default None

     def_target
      The default target for this command.
      Default is "target"

     req_target
      This command operates on a target.  For example,
         /cast X
      Casts X on a target, whereas
         /equip X
      Does not require a target
      Default False

     takes_ext_target: (Optional)
      The verb accepts external targets, i.e. targets other than player.
      Default False

     interp_target: (Optional)
      When interpolating parameters as targets, ignore references
      to target keywords such as target, pet, etc.
      Default True

     takes_perc_target: (Optional)
      Verb translates %t into current target (some insecure verbs only).
      Default False
    '''

    attr_defaults = {
        # Verb
        'comment'          : False,
        'meta'             : False,
        'secure'           : False,
        'only_usable_once' : False,
        'gcd'              : False,
        'allow_reset'      : False,
        'related'          : [],
        
        # Verb params
        'allow_toggle'     : False,
        'param'            : None,
        'param_req'        : False,
        'takes_units'      : False,
        'takes_spell'      : False,
        'takes_item'       : False,
        'takes_int'        : False,
        'takes_list'       : False,
        
        # Verb targets
        'key_unit'         : None,
        'def_target'       : 'target',
        'req_target'       : False,
        'takes_ext_target' : False,
        'takes_perc_target': False,
        'interp_target'    : True,
        
        # Verb interpretation
        'assemble_function': get_assembled_command,
        'param_function'   : get_assembled_parameter,
        }


''' Map of command verbs.
Note that we handle things outside of this list--these
are just a subset of verbs which have descriptions, etc '''
VERB_MAP = {
    'COMMENT':           Verb(assemble_function=get_commented_command),
    '#show':             Verb(show_gcd=False, only_usable_once=True, related=[u'#showtooltip'], secure=True, meta=True, param=set([None,(str,),(int,),(int, int)]), desc='Show icon and cooldown', takes_item=True, takes_spell=True, param_function=get_assembled_parameter_show, assemble_function=get_show_command),
    '#showcooldown':     Verb(show_gcd=False, only_usable_once=True, related=[u'#showtooltip'], secure=True, meta=True, param=set([None,(str,),(int,),(int, int)]), desc='Show cooldown', takes_item=True, takes_spell=True, param_function=get_assembled_parameter_show, assemble_function=get_show_command),
    '#showtooltip':      Verb(show_gcd=False, only_usable_once=True, related=[u'#show'], secure=True, meta=True, param=set([None,(str,),(int,),(int, int)]), desc='Show tooltip, icon, and cooldown', takes_item=True, takes_spell=True, param_function=get_assembled_parameter_show, assemble_function=get_show_command),
    '/cancelaura':       Verb(param_req=True, secure=True, desc='Remove', param=set([(str,)]), assemble_function=get_cancelaura_command),
    '/cancelform':       Verb(secure=True, desc='Cancel a stance, form, or stealth'),
    '/cast':             Verb(param_req=True, takes_ext_target=True, secure=True, desc='Cast', allow_toggle=True, req_target=True, takes_spell=True, param=set([(str,)]), def_target='target', assemble_function=get_cast_command),
    '/castrandom':       Verb(param_req=True, takes_ext_target=True, secure=True, desc='Cast a random spell from a set', allow_toggle=True, def_target='target', req_target=True, takes_spell=True, param=set([(str,)]), takes_list=True, param_function=get_assembled_list_param, assemble_function=get_castsequence_command),
    '/castsequence':     Verb(param_req=True, takes_ext_target=True, secure=True, desc='Cast the next spell in a sequence', allow_toggle=True, def_target='target', req_target=True, takes_spell=True, param=set([(str,)]), takes_list=True, param_function=get_assembled_list_param, assemble_function=get_castsequence_command, allow_reset=True),
    '/changeactionbar':  Verb(secure=True, desc='Change your active action bar', param=set([(int,)]), assemble_function=get_actionbar_command), 
    '/clearfocus':       Verb(secure=True, desc='Clear your focus target'),
    '/cleartarget':      Verb(secure=True, desc='Clear your target'),
    '/click':            Verb(param_req=True, gcd=False, secure=True, desc='Automatically click', param=set([(str,),(str, int, str),(str, int)]), param_function=get_assembled_parameter_click, error_msg="The /click command takes specific button identifiers.  Check the interpretation frame for more information."),
    '/dismount':         Verb(secure=True, desc='Dismount'),
    '/equip':            Verb(param_req=True, gcd=True, secure=True, desc='Equip', takes_item=True, takes_int=True, param_function=get_assembled_parameter_equip, assemble_function=get_equip_command, param=set([(str,), (int, int)])),
    '/equipslot':        Verb(param_req=True, gcd=True, secure=True, desc='Equip', takes_item=True, takes_int=True, param=set([(int, str), (int, int, int)]), param_function=get_assembled_parameter_equipslot, assemble_function=get_verb_params_command, error_msg="The /equipslot command requires either a slot number an and item, or a slot number, bag id, and bag slot number."),
    '/petattack':        Verb(secure=True, desc='Order your pet to attack', takes_units=True, param=set([(str,)]), key_unit='pettarget', takes_ext_target=True, req_target=True),
    '/petagressive':     Verb(secure=True, desc='Turn on pet aggressive mode, canceling other modes', assemble_function=get_verb_only_command),
    '/petdefensive':     Verb(secure=True, desc='Turn on pet defensive mode, canceling other modes', assemble_function=get_verb_only_command),
    '/petfollow':        Verb(secure=True, desc='Turn on pet follow mode, canceling other modes', assemble_function=get_verb_only_command),
    '/petpassive':       Verb(secure=True, desc='Turn on pet passive mode, canceling other modes', assemble_function=get_verb_only_command),
    '/petstay':          Verb(secure=True, desc='Turn on pet stay mode, canceling other modes', assemble_function=get_verb_only_command),

    # These pet commands take argumetns.
    '/petautocastoff':   Verb(secure=True, desc='Turn off pet skill autocast', param=set([(str,)]), assemble_function=get_pet_autocast_command),
    '/petautocaston':    Verb(secure=True, desc='Turn on pet skill autocast', param=set([(str,)]), assemble_function=get_pet_autocast_command),
    '/petautocasttoggle':Verb(secure=True, desc='Change pet skill autocast state', param=set([(str,)]), assemble_function=get_pet_autocast_command),


    '/startattack':      Verb(takes_ext_target=True, secure=True, desc='Start attacking', takes_units=True, key_unit='target', req_target=True),
    '/stopattack':       Verb(secure=True, desc='Stop attacking'),
    '/stopcasting':      Verb(secure=True, desc='Stop all casting'),
    '/stopmacro':        Verb(secure=True, desc='Stop this macro'),
    '/swapactionbar':    Verb(secure=True, desc='Swap active action bar', takes_int=True, param=set([(int, int)]), error_msg="The /swapactionbar command requires two action bar ids.  See the link in the interpretation frame for details.", assemble_function=get_actionbar_command),

    # Commands for setting target
    '/assist':           Verb(takes_ext_target=True, secure=True, desc='Set your target to the target of', takes_units=True, def_target='target', assemble_function=get_assist_command),
    '/focus':            Verb(takes_ext_target=True, secure=True, desc='Set your focus target to', takes_units=True, key_unit='focus', assemble_function=get_focus_command),
    '/tar':              Verb(def_target=None, param_req=True, takes_ext_target=True, secure=True, desc='Set target to', takes_units=True, key_unit='target', req_target=True, assemble_function=get_target_command, param_function=get_assembled_parameter_targeting),
    '/target':           Verb(def_target=None, param_req=True, takes_ext_target=True, secure=True, desc='Set target to', takes_units=True, key_unit='target', req_target=True, assemble_function=get_target_command, param_function=get_assembled_parameter_targeting),
    '/targetexact':      Verb(def_target=None, param_req=True, takes_ext_target=True, secure=True, desc='Set target to', takes_units=True, key_unit='target', req_target=True, assemble_function=get_targetexact_command, interp_target=False),

    # Commands for cycling through targets amongst a group of units
    '/targetenemy':        Verb(secure=True, desc='Target next visible enemy unit', only_usable_once=True, takes_int=True, assemble_function=get_target_cycle_command, param=set([(int,), None]), error_msg="This command only recognizes single numbers as a parameter.  Use '1' as the parameter to cycle targets in reverse.  To target specific units, use /tar or /targetexact.", param_function=get_assembled_parameter_cycle_target),
    '/targetenemyplayer':  Verb(secure=True, desc='Target next visible enemy player', only_usable_once=True, takes_int=True, assemble_function=get_target_cycle_command, param=set([(int,), None]), error_msg="This command only recognizes single numbers as a parameter.  Use '1' as the parameter to cycle targets in reverse.  To target specific units, use /tar or /targetexact.", param_function=get_assembled_parameter_cycle_target),
    '/targetfriend':       Verb(secure=True, desc='Target next visible friendly unit', only_usable_once=True, takes_int=True, assemble_function=get_target_cycle_command, param=set([(int,), None]), error_msg="This command only recognizes single numbers as a parameter.  Use '1' as the parameter to cycle targets in reverse.  To target specific units, use /tar or /targetexact.", param_function=get_assembled_parameter_cycle_target),
    '/targetfriendplayer': Verb(secure=True, desc='Target next visible friendly player', only_usable_once=True, takes_int=True, assemble_function=get_target_cycle_command, param=set([(int,), None]), error_msg="This command only recognizes single numbers as a parameter.  Use '1' as the parameter to cycle targets in reverse.  To target specific units, use /tar or /targetexact.", param_function=get_assembled_parameter_cycle_target),
    '/targetparty':        Verb(secure=True, desc='Target next visible party member', assemble_function=get_target_cycle_command, takes_int=True, param=set([(int,), None]), error_msg="This command only recognizes single numbers as a parameter.  Use '1' as the parameter to cycle targets in reverse.  To target specific units, use /tar or /targetexact.", param_function=get_assembled_parameter_cycle_target),
    '/targetraid':         Verb(secure=True, desc='Target next visible party or raid member', assemble_function=get_target_cycle_command, takes_int=True, param=set([(int,), None]), error_msg="This command only recognizes single numbers as a parameter.  Use '1' as the parameter to cycle targets in reverse.  To target specific units, use /tar or /targetexact.", param_function=get_assembled_parameter_cycle_target),

    # Commands for cycling through target history
    '/targetlasttarget': Verb(secure=True, desc='Target your last target'),
    '/targetlastenemy':  Verb(secure=True, desc='Target the last enemy unit you had targeted'),
    '/targetlastfriend': Verb(secure=True, desc='Target the last friendly unit you had targeted'),

    '/use':              Verb(param_req=True, gcd=False, secure=True, desc='Use', def_target="player", takes_item=True, takes_int=True, param=set([(str,),(int,),(int, int)]), assemble_function=get_verb_params_command, error_msg="The /use command requires an item name, a bag id and bag slot, or an inventory slot.", param_function=get_assembled_parameter_use),
    '/userandom':        Verb(param_req=True, gcd=False, secure=True, desc='Use a randomly selected item from', param=set([(str,)]), takes_list=True, param_function=get_assembled_list_param, assemble_function=get_verb_params_command),

    # Added with patch 3.1
    '/usetalents':       Verb(param_req=True, secure=True, desc='Activate talent set', takes_int=True, param=set([(int,)]), error_msg="The /usetalents command requires integer arguments."),
    '/equipset':         Verb(param_req=True, secure=True, desc='Equip equipment set', param=set([(str,)]), error_msg="The /equipset command requires a set name as saved in the equipment manager.", assemble_function=get_equipset_command),


    # Insecure slash commands
    '/threshold':        Verb(secure=False, param_req=True, desc='Set loot threshold to'),
    '/master':           Verb(secure=False, param_req=True, desc='Set Master Looter to'),
    '/console':          Verb(secure=False, param_req=True, desc='Run console command:'),

    '/random':           Verb(secure=False, desc='Roll a number', assemble_function=get_roll_command, param_function=get_roll_params),
    '/rand':             Verb(secure=False, desc='Roll a number', assemble_function=get_roll_command, param_function=get_roll_params),
    '/roll':             Verb(secure=False, desc='Roll a number', assemble_function=get_roll_command, param_function=get_roll_params),
    '/rnd':              Verb(secure=False, desc='Roll a number', assemble_function=get_roll_command, param_function=get_roll_params),

    '/follow':           Verb(secure=False, desc='Follow', takes_ext_target=True, req_target=True, takes_units=True, assemble_function=get_follow_command),
    '/f':                Verb(secure=False, desc='Follow', takes_ext_target=True, req_target=True, takes_units=True, assemble_function=get_follow_command),

    '/who':              Verb(secure=False, desc='Get a list of online players', param_function=get_who_params),

    '/afk':              Verb(secure=False, desc='Set your status to Away From Keyboard', assemble_function=get_verb_msg_command),
    '/dnd':              Verb(secure=False, desc='Set your status to Do Not Disturb', assemble_function=get_verb_msg_command),
    '/sit':              Verb(secure=False, desc='Sit down', param_function=get_verb_only_command),
    '/stand':            Verb(secure=False, desc='Stand up', assemble_function=get_verb_only_command),
    '/played':           Verb(secure=False, desc='Output the amount of time played on this character', assemble_function=get_verb_only_command),
    '/exit':             Verb(secure=False, desc='Exit the game', assemble_function=get_verb_only_command),
    '/logout':           Verb(secure=False, desc='Log out', assemble_function=get_verb_only_command),
    '/camp':             Verb(secure=False, desc='Log out', assemble_function=get_verb_only_command),


    # Insecure commands with a targeting component
    '/t':                Verb(secure=False, takes_ext_target=True, req_target=True, takes_units=True, desc='Whisper', assemble_function=get_targeted_chat_command, param_function=get_translated_chat_params),
    '/tell':             Verb(secure=False, takes_ext_target=True, req_target=True, takes_units=True, desc='Whisper', assemble_function=get_targeted_chat_command, param_function=get_translated_chat_params),
    '/w':                Verb(secure=False, takes_ext_target=True, req_target=True, takes_units=True, desc='Whisper', assemble_function=get_targeted_chat_command, param_function=get_translated_chat_params),
    '/whisper':          Verb(secure=False, takes_ext_target=True, req_target=True, takes_units=True, desc='Whisper', assemble_function=get_targeted_chat_command, param_function=get_translated_chat_params),
    
    # Insecure commands dealing with chats
    '/p':                Verb(secure=False, desc='Say in party chat:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/party':            Verb(secure=False, desc='Say in party chat:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/s':                Verb(secure=False, desc='Say', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/say':              Verb(secure=False, desc='Say', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/yell':             Verb(secure=False, desc='Yell', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/y':                Verb(secure=False, desc='Yell', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/r':                Verb(secure=False, desc='Reply to last whisper:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/reply':            Verb(secure=False, desc='Reply to last whisper:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),   
    '/rw':               Verb(secure=False, desc='Raid Warn:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/raidwarning':      Verb(secure=False, desc='Raid Warn:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/run':              Verb(secure=False, desc='Run Lua:'),
    '/script':           Verb(secure=False, desc='Run Lua:'),
    
    '/ra':               Verb(secure=False, desc='Say in raid:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/raid':             Verb(secure=False, desc='Say in raid:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/bg':               Verb(secure=False, desc='Say in bgchat:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/g':                Verb(secure=False, desc='Say in guildchat:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/guild':            Verb(secure=False, desc='Say in guildchat:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/y':                Verb(secure=False, desc='Yell:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/yell':             Verb(secure=False, desc='Yell:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/1':                Verb(secure=False, desc='Say in chat channel 1:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/2':                Verb(secure=False, desc='Say in chat channel 2:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/3':                Verb(secure=False, desc='Say in chat channel 3:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/4':                Verb(secure=False, desc='Say in chat channel 4:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/5':                Verb(secure=False, desc='Say in chat channel 5:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/6':                Verb(secure=False, desc='Say in chat channel 6:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/7':                Verb(secure=False, desc='Say in chat channel 7:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/8':                Verb(secure=False, desc='Say in chat channel 8:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/9':                Verb(secure=False, desc='Say in chat channel 9:', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/join':             Verb(secure=False, desc='Join chat channel: '),
    '/leave':            Verb(secure=False, desc='Leave chat channel: '),

    # Emotes follow.  These all behave differently depending on whether they have a unit.
    # These emotes take parameters
    '/e':                Verb(secure=False, desc='Emote', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/emote':            Verb(secure=False, desc='Emote', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),
    '/em':               Verb(secure=False, desc='Emote', assemble_function=get_verb_params_command, param_function=get_translated_chat_params),

    # These emotes do not take parameters
    '/absent':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You look absent-minded."''', alt_desc='''Emote "You look at %s absently."''', assemble_function=get_emote_command),
    '/agree':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You agree."''', alt_desc='''Emote "You agree with %s."''', assemble_function=get_emote_command),
    '/amaze':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are amazed!"''', alt_desc='''Emote "You are amazed by %s!"''', assemble_function=get_emote_command),
    '/angry':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise your fist in anger."''', alt_desc='''Emote "You raise your fist in anger at %s."''', assemble_function=get_emote_command),
    '/apologize':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You apologize to everyone. Sorry!"''', alt_desc='''Emote "You apologize to %s. Sorry!"''', assemble_function=get_emote_command),
    '/applaud':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You applaud. Bravo!"''', alt_desc='''Emote "You applaud at %s. Bravo!"''', assemble_function=get_emote_command),
    '/applause':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You applaud. Bravo!"''', alt_desc='''Emote "You applaud at %s. Bravo!"''', assemble_function=get_emote_command),
    '/arm':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You stretch your arms out."''', alt_desc='''Emote "You put your arm around %s's shoulder."''', assemble_function=get_emote_command),
    '/attacktarget':     Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You tell everyone to attack something."''', alt_desc='''Emote "You tell everyone to attack %s."''', assemble_function=get_emote_command),
    '/awe':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You look around in awe."''', alt_desc='''Emote "You stare at %s in awe."''', assemble_function=get_emote_command),
    '/backpack':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You dig through your backpack."''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/badfeeling':       Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You have a bad feeling about this..."''', alt_desc='''Emote "You have a bad feeling about %s."''', assemble_function=get_emote_command),
    '/bark':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bark. Woof woof!"''', alt_desc='''Emote "You bark at %s"''', assemble_function=get_emote_command),
    '/bashful':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are bashful."''', alt_desc='''Emote "You are so bashful...too bashful to get %s's attention."''', assemble_function=get_emote_command),
    '/beckon':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You beckon everyone over to you."''', alt_desc='''Emote "You beckon %s over."''', assemble_function=get_emote_command),
    '/beg':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You beg everyone around you. How pathetic."''', alt_desc='''Emote "You beg %s. How pathetic."''', assemble_function=get_emote_command),
    '/belch':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let out a loud belch."''', alt_desc='''Emote "You burp rudely in %s's face."''', assemble_function=get_emote_command),
    '/bite':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You look around for someone to bite."''', alt_desc='''Emote "You bite %s. Ouch!"''', assemble_function=get_emote_command),
    '/blame':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You blame yourself for what happened."''', alt_desc='''Emote "You blame %s for everything."''', assemble_function=get_emote_command),
    '/blank':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You stare blankly at your surroundings."''', alt_desc='''Emote "You stare blankly %s."''', assemble_function=get_emote_command),
    '/bleed':            Verb(secure=False, desc='''Emote "Blood oozes from your wounds."''', assemble_function=get_emote_command),
    '/blink':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You blink your eyes."''', alt_desc='''Emote "You blink at %s."''', assemble_function=get_emote_command),
    '/blood':            Verb(secure=False, desc='''Emote "Blood oozes from your wounds."''', assemble_function=get_emote_command),
    '/blow':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You blow a kiss into the wind."''', alt_desc='''Emote "You blow a kiss to %s."''', assemble_function=get_emote_command),
    '/blush':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You blush."''', alt_desc='''Emote "You blush at %s."''', assemble_function=get_emote_command),
    '/boggle':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You boggle at the situation."''', alt_desc='''Emote "You boggle at %s."''', assemble_function=get_emote_command),
    '/bonk':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bonk yourself on the noggin. Doh!"''', alt_desc='''Emote "You bonk %s on the noggin. Doh!"''', assemble_function=get_emote_command),
    '/bored':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are overcome with boredom. Oh the drudgery!"''', alt_desc='''Emote "You are terribly bored with %s."''', assemble_function=get_emote_command),
    '/bounce':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bounce up and down."''', alt_desc='''Emote "You bounce up and down in front of %s."''', assemble_function=get_emote_command),
    '/bow':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bow down graciously."''', alt_desc='''Emote "You bow before %s."''', assemble_function=get_emote_command),
    '/brandish':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You brandish your weapon fiercely."''', alt_desc='''Emote "You brandish your weapon fiercely at %s."''', assemble_function=get_emote_command),
    '/bravo':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You applaud. Bravo!"''', alt_desc='''Emote "You applaud at %s. Bravo!"''', assemble_function=get_emote_command),
    '/breath':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You take a deep breath. Bravo!"''', alt_desc='''Emote "You tell %s to take a deep breath."''', assemble_function=get_emote_command),
    '/burp':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let out a loud belch."''', alt_desc='''Emote "You burp rudely in %s's face."''', assemble_function=get_emote_command),
    '/bye':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You wave goodbye to everyone. Farewell!"''', alt_desc='''Emote "You wave goodbye to %s. Farewell!"''', assemble_function=get_emote_command),
    '/cackle':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cackle maniacally at the situation."''', alt_desc='''Emote "You cackle maniacally at %s."''', assemble_function=get_emote_command),
    '/calm':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You remain calm."''', alt_desc='''Emote "You try to calm %s down."''', assemble_function=get_emote_command),
    '/cat':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You scratch yourself. Ah, much better!"''', alt_desc='''Emote "You scratch %s. How catty!"''', assemble_function=get_emote_command),
    '/catty':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You scratch yourself. Ah, much better!"''', alt_desc='''Emote "You scratch %s. How catty!"''', assemble_function=get_emote_command),
    '/challenge':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You put out a challenge to everyone. Bring it on!."''', alt_desc='''Emote "You challenge %s to a duel."''', assemble_function=get_emote_command),
    '/charge':           Verb(secure=False, desc='''Emote "You start to charge."''', assemble_function=get_emote_command),
    '/charm':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You put on the charm."''', alt_desc='''Emote "You think %s is charming."''', assemble_function=get_emote_command),
    '/cheer':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cheer!"''', alt_desc='''Emote "You cheer at %s."''', assemble_function=get_emote_command),
    '/chew':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You begin to eat."''', alt_desc='''Emote "You begin to eat in front of %s."''', assemble_function=get_emote_command),
    '/chicken':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "With arms flapping, you strut around. Cluck, Cluck, Chicken!"''', alt_desc='''Emote "With arms flapping, you strut around %s. Cluck, Cluck, Chicken!"''', assemble_function=get_emote_command),
    '/chuckle':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let out a hearty chuckle."''', alt_desc='''Emote "You chuckle at %s."''', assemble_function=get_emote_command),
    '/chug':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You take a mighty quaff of your beverage."''', alt_desc='''Emote "You encourage %s to chug. CHUG! CHUG! CHUG!"''', assemble_function=get_emote_command),
    '/clap':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You clap excitedly."''', alt_desc='''Emote "You clap excitedly for %s."''', assemble_function=get_emote_command),
    '/cold':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let everyone know that you are cold."''', alt_desc='''Emote "You let %s know that you are cold."''', assemble_function=get_emote_command),
    '/comfort':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need to be comforted."''', alt_desc='''Emote "You comfort %s."''', assemble_function=get_emote_command),
    '/commend':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You commend everyone on a job well done."''', alt_desc='''Emote "You commend %s on a job well done."''', assemble_function=get_emote_command),
    '/confused':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are hopelessly confused."''', alt_desc='''Emote "You look at %s with a confused look."''', assemble_function=get_emote_command),
    '/cong':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You congratulate everyone around you."''', alt_desc='''Emote "You congratulate %s."''', assemble_function=get_emote_command),
    '/congrats':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You congratulate everyone around you."''', alt_desc='''Emote "You congratulate %s."''', assemble_function=get_emote_command),
    '/congratulate':     Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You congratulate everyone around you."''', alt_desc='''Emote "You congratulate %s."''', assemble_function=get_emote_command),
    '/cough':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let out a hacking cough."''', alt_desc='''Emote "You cough at %s."''', assemble_function=get_emote_command),
    '/coverears':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cover your ears."''', alt_desc='''Emote "You cover %s's ears."''', assemble_function=get_emote_command),
    '/cower':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cower in fear."''', alt_desc='''Emote "You cower in fear at the sight of %s."''', assemble_function=get_emote_command),
    '/crack':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You crack your knuckles."''', alt_desc='''Emote "You crack your knuckles while staring at %s."''', assemble_function=get_emote_command),
    '/cringe':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cringe in fear."''', alt_desc='''Emote "You cringe away from %s."''', assemble_function=get_emote_command),
    '/crossarms':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cross your arms."''', alt_desc='''Emote "You cross your arms at %s. Hmph!"''', assemble_function=get_emote_command),
    '/cry':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cry."''', alt_desc='''Emote "You cry on %s's shoulder."''', assemble_function=get_emote_command),
    '/cuddle':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need to be cuddled."''', alt_desc='''Emote "You cuddle up against %s."''', assemble_function=get_emote_command),
    '/curious':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You express your curiosity to those around you."''', alt_desc='''Emote "You are curious what %s is up to."''', assemble_function=get_emote_command),
    '/curtsey':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You curtsey."''', alt_desc='''Emote "You curtsey before %s."''', assemble_function=get_emote_command),
    '/dance':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You burst into dance."''', alt_desc='''Emote "You dance with %s."''', assemble_function=get_emote_command),
    '/ding':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You reached a new level. DING!"''', alt_desc='''Emote "You congratulate %s on a new level. DING!"''', assemble_function=get_emote_command),
    '/disagree':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You disagree."''', alt_desc='''Emote "You disagree with %s."''', assemble_function=get_emote_command),
    '/disappointed':     Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You frown."''', alt_desc='''Emote "You frown with disappointment at %s."''', assemble_function=get_emote_command),
    '/disappointment':   Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You frown."''', alt_desc='''Emote "You frown with disappointment at %s."''', assemble_function=get_emote_command),
    '/doh':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bonk yourself on the noggin. Doh!"''', alt_desc='''Emote "You bonk %s on the noggin. Doh!"''', assemble_function=get_emote_command),
    '/doom':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You threaten everyone with the wrath of doom."''', alt_desc='''Emote "You threaten %s with the wrath of doom."''', assemble_function=get_emote_command),
    '/doubt':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You doubt the situation will end in your favor."''', alt_desc='''Emote "You doubt %s."''', assemble_function=get_emote_command),
    '/drink':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise a drink in the air before chugging it down. Cheers!"''', alt_desc='''Emote "You raise a drink to %s. Cheers!"''', assemble_function=get_emote_command),
    '/drool':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "A tendril of drool runs down your lip."''', alt_desc='''Emote "You look at %s and begin to drool."''', assemble_function=get_emote_command),
    '/duck':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You duck for cover."''', alt_desc='''Emote "You duck behind %s."''', assemble_function=get_emote_command),
    '/eat':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You begin to eat."''', alt_desc='''Emote "You begin to eat in front of %s."''', assemble_function=get_emote_command),
    '/encourage':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You encourage everyone around you."''', alt_desc='''Emote "You encourage %s."''', assemble_function=get_emote_command),
    '/enemy':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You warn everyone that an enemy is near."''', alt_desc='''Emote "You warn %s that an enemy is near."''', assemble_function=get_emote_command),
    '/excited':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You talk excitedly with everyone."''', alt_desc='''Emote "You talk excitedly with %s."''', assemble_function=get_emote_command),
    '/eye':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cross your eyes."''', alt_desc='''Emote "You eye %s up and down."''', assemble_function=get_emote_command),
    '/exit':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Exit the game.''', assemble_function=get_emote_command),
    '/eyebrow':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise your eyebrow inquisitively."''', alt_desc='''Emote "You raise your eyebrow inquisitively at %s."''', assemble_function=get_emote_command),
    '/facepalm':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cover your face with your palm."''', alt_desc='''Emote "You look at %s and cover your face with your palm."''', assemble_function=get_emote_command),
    '/faint':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You faint."''', alt_desc='''Emote "You faint at the sight of %s."''', assemble_function=get_emote_command),
    '/farewell':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You wave goodbye to everyone. Farewell!"''', alt_desc='''Emote "You wave goodbye to %s. Farewell!"''', assemble_function=get_emote_command),
    '/fart':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You fart loudly. Whew...what stinks?"''', alt_desc='''Emote "You brush up against %s and fart loudly."''', assemble_function=get_emote_command),
    '/fear':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cower in fear."''', alt_desc='''Emote "You cower in fear at the sight of %s."''', assemble_function=get_emote_command),
    '/feast':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You begin to eat."''', alt_desc='''Emote "You begin to eat in front of %s."''', assemble_function=get_emote_command),
    '/fidget':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You fidget."''', alt_desc='''Emote "You fidget impatiently while waiting for %s."''', assemble_function=get_emote_command),
    '/flap':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "With arms flapping, you strut around. Cluck, Cluck, Chicken!"''', alt_desc='''Emote "With arms flapping, you strut around %s. Cluck, Cluck, Chicken!"''', assemble_function=get_emote_command),
    '/flee':             Verb(secure=False, desc='''Emote "You yell for everyone to flee!"''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/fle ':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You fle  your muscles. Oooooh so strong!"''', alt_desc='''Emote "You fle  at %s. Oooooh so strong!"''', assemble_function=get_emote_command),
    '/flirt':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You flirt."''', alt_desc='''Emote "You flirt with %s."''', assemble_function=get_emote_command),
    '/flop':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You flop about helplessly."''', alt_desc='''Emote "You flop about helplessly around %s."''', assemble_function=get_emote_command),
    '/follow':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Follow the currently targeted player.''', assemble_function=get_emote_command),
    '/followme':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You motion for everyone to follow."''', alt_desc='''Emote "You motion for %s to follow."''', assemble_function=get_emote_command),
    '/food':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are hungry!"''', alt_desc='''Emote "You are hungry. Maybe %s has some food..."''', assemble_function=get_emote_command),
    '/frown':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You frown."''', alt_desc='''Emote "You frown with disappointment at %s."''', assemble_function=get_emote_command),
    '/gasp':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You gasp."''', alt_desc='''Emote "You gasp at %s."''', assemble_function=get_emote_command),
    '/gaze':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You gaze off into the distance."''', alt_desc='''Emote "You gaze eagerly at %s."''', assemble_function=get_emote_command),
    '/giggle':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You giggle."''', alt_desc='''Emote "You giggle at %s."''', assemble_function=get_emote_command),
    '/glad':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are filled with happiness!"''', alt_desc='''Emote "You are very happy with %s!"''', assemble_function=get_emote_command),
    '/glare':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You glare angrily."''', alt_desc='''Emote "You glare angrily at %s."''', assemble_function=get_emote_command),
    '/gloat':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You gloat over everyone's misfortune."''', alt_desc='''Emote "You gloat over %s's misfortune."''', assemble_function=get_emote_command),
    '/glower':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You glower at everyone around you."''', alt_desc='''Emote "You glower at %s."''', assemble_function=get_emote_command),
    '/go':               Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You tell everyone to go."''', alt_desc='''Emote "You tell %s to go."''', assemble_function=get_emote_command),
    '/going':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You must be going."''', alt_desc='''Emote "You tell %s that you must be going."''', assemble_function=get_emote_command),
    '/golfclap':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You clap half heartedly, clearly unimpressed."''', alt_desc='''Emote "You clap for %s, clearly unimpressed."''', assemble_function=get_emote_command),
    '/goodbye':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You wave goodbye to everyone. Farewell!"''', alt_desc='''Emote "You wave goodbye to %s. Farewell!"''', assemble_function=get_emote_command),
    '/greet':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You greet everyone warmly."''', alt_desc='''Emote "You greet %s warmly."''', assemble_function=get_emote_command),
    '/greetings':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You greet everyone warmly."''', alt_desc='''Emote "You greet %s warmly."''', assemble_function=get_emote_command),
    '/grin':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You grin wickedly."''', alt_desc='''Emote "You grin wickedly at %s."''', assemble_function=get_emote_command),
    '/groan':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You begin to groan."''', alt_desc='''Emote "You look at %s and groan."''', assemble_function=get_emote_command),
    '/grovel':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You grovel on the ground, wallowing in subservience."''', alt_desc='''Emote "You grovel before %s like a subservient peon."''', assemble_function=get_emote_command),
    '/growl':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You growl menacingly."''', alt_desc='''Emote "You growl menacingly at %s."''', assemble_function=get_emote_command),
    '/guffaw':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let out a boisterous guffaw!"''', alt_desc='''Emote "You take one look at %s and let out a guffaw!"''', assemble_function=get_emote_command),
    '/hail':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You hail those around you."''', alt_desc='''Emote "You hail %s."''', assemble_function=get_emote_command),
    '/happy':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are filled with happiness!"''', alt_desc='''Emote "You are very happy with %s!"''', assemble_function=get_emote_command),
    '/headache':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are getting a headache."''', alt_desc='''Emote "You are getting a headache from %s's antics."''', assemble_function=get_emote_command),
    '/healme':           Verb(secure=False, desc='''Emote "You call out for healing!"''', assemble_function=get_emote_command),
    '/hello':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You greet everyone with a hearty hello!"''', alt_desc='''Emote "You greet %s with a hearty hello!"''', assemble_function=get_emote_command),
    '/helpme':           Verb(secure=False, desc='''Emote "You cry out for help!"''', assemble_function=get_emote_command),
    '/hi':               Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You greet everyone with a hearty hello!"''', alt_desc='''Emote "You greet %s with a hearty hello!"''', assemble_function=get_emote_command),
    '/hiccup':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You hiccup loudly."''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/highfive':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You put up your hand for a high five."''', alt_desc='''Emote "You give %s a high five!"''', assemble_function=get_emote_command),
    '/hiss':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You hiss at everyone around you."''', alt_desc='''Emote "You hiss at %s."''', assemble_function=get_emote_command),
    '/holdhand':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You wish someone would hold your hand."''', alt_desc='''Emote "You hold %s's hand."''', assemble_function=get_emote_command),
    '/hug':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need a hug!"''', alt_desc='''Emote "You hug %s."''', assemble_function=get_emote_command),
    '/hungry':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are hungry!"''', alt_desc='''Emote "You are hungry. Maybe %s has some food..."''', assemble_function=get_emote_command),
    '/hurry':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You try to pick up the pace."''', alt_desc='''Emote "You tell %s to hurry up."''', assemble_function=get_emote_command),
    '/idea':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You have an idea!"''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/impatient':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You fidget."''', alt_desc='''Emote "You fidget impatiently while waiting for %s."''', assemble_function=get_emote_command),
    '/incoming':         Verb(secure=False, desc='''Emote "You yell incoming enemies!"''', assemble_function=get_emote_command),
    '/insult':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You think everyone around you is a son of a motherless ogre."''', alt_desc='''Emote "You think %s is the son of a motherless ogre."''', assemble_function=get_emote_command),
    '/introduce':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You introduce yourself to everyone."''', alt_desc='''Emote "You introduce yourself to %s."''', assemble_function=get_emote_command),
    '/jealous':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are jealous of everyone around you."''', alt_desc='''Emote "You are jealous of %s."''', assemble_function=get_emote_command),
    '/jk':               Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You were just kidding!"''', alt_desc='''Emote "You let %s know that you were just kidding!"''', assemble_function=get_emote_command),
    '/kiss':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You blow a kiss into the wind."''', alt_desc='''Emote "You blow a kiss to %s."''', assemble_function=get_emote_command),
    '/kneel':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You kneel down."''', alt_desc='''Emote "You kneel before %s."''', assemble_function=get_emote_command),
    '/knuckles':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You crack your knuckles."''', alt_desc='''Emote "You crack your knuckles while staring at %s."''', assemble_function=get_emote_command),
    '/laugh':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You laugh."''', alt_desc='''Emote "You laugh at %s."''', assemble_function=get_emote_command),
    '/lavish':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You praise the Light."''', alt_desc='''Emote "You lavish praise upon %s."''', assemble_function=get_emote_command),
    '/lay':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You lie down."''', alt_desc='''Emote "You lie down before %s."''', assemble_function=get_emote_command),
    '/laydown':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You lie down."''', alt_desc='''Emote "You lie down before %s."''', assemble_function=get_emote_command),
    '/lick':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You lick your lips."''', alt_desc='''Emote "You lick %s."''', assemble_function=get_emote_command),
    '/lie':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You lie down."''', alt_desc='''Emote "You lie down before %s."''', assemble_function=get_emote_command),
    '/liedown':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You lie down."''', alt_desc='''Emote "You lie down before %s."''', assemble_function=get_emote_command),
    '/listen':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are listening!"''', alt_desc='''Emote "You listen intently to %s."''', assemble_function=get_emote_command),
    '/lol':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You laugh."''', alt_desc='''Emote "You laugh at %s."''', assemble_function=get_emote_command),
    '/look':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You look around."''', alt_desc='''Emote "You look at %s."''', assemble_function=get_emote_command),
    '/lost':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are hopelessly lost."''', alt_desc='''Emote "You want %s to know that you are hopelessly lost."''', assemble_function=get_emote_command),
    '/love':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You feel the love."''', alt_desc='''Emote "You love %s."''', assemble_function=get_emote_command),
    '/luck':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You wish everyone good luck."''', alt_desc='''Emote "You wish %s the best of luck."''', assemble_function=get_emote_command),
    '/mad':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise your fist in anger."''', alt_desc='''Emote "You raise your fist in anger at %s."''', assemble_function=get_emote_command),
    '/map':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You pull out your map."''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/massage':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need a massage!"''', alt_desc='''Emote "You massage %s's shoulders."''', assemble_function=get_emote_command),
    '/mercy':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You plead for mercy."''', alt_desc='''Emote "You plead with %s for mercy."''', assemble_function=get_emote_command),
    '/moan':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You moan suggestively."''', alt_desc='''Emote "You moan suggestively at %s."''', assemble_function=get_emote_command),
    '/mock':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You mock life and all it stands for."''', alt_desc='''Emote "You mock the foolishness of %s."''', assemble_function=get_emote_command),
    '/moo':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "Mooooooooooo."''', alt_desc='''Emote "You moo at %s. Mooooooooooo."''', assemble_function=get_emote_command),
    '/moon':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You drop your trousers and moon everyone."''', alt_desc='''Emote "You drop your trousers and moon %s."''', assemble_function=get_emote_command),
    '/mourn':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "In quiet contemplation, you mourn the loss of the dead."''', alt_desc='''Emote "In quiet contemplation, you mourn the death of %s."''', assemble_function=get_emote_command),
    '/mutter':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You mutter angrily to yourself. Hmmmph!"''', alt_desc='''Emote "You mutter angrily at %s. Hmmmph!"''', assemble_function=get_emote_command),
    '/nervous':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You look around nervously."''', alt_desc='''Emote "You look at %s nervously."''', assemble_function=get_emote_command),
    '/no':               Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You clearly state, NO."''', alt_desc='''Emote "You tell %s NO. Not going to happen."''', assemble_function=get_emote_command),
    '/nod':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You nod."''', alt_desc='''Emote "You nod at %s."''', assemble_function=get_emote_command),
    '/nosepick':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "With a finger deep in one nostril, you pass the time."''', alt_desc='''Emote "You pick your nose and show it to %s."''', assemble_function=get_emote_command),
    '/object':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You OBJECT!"''', alt_desc='''Emote "You object to %s."''', assemble_function=get_emote_command),
    '/offer':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You want to make an offer."''', alt_desc='''Emote "You attempt to make %s an offer they can't refuse."''', assemble_function=get_emote_command),
    '/oom':              Verb(secure=False, desc='''Emote "You announce that you have low mana!"''', assemble_function=get_emote_command),
    '/openfire':         Verb(secure=False, desc='''Emote "You give the order to open fire."''', assemble_function=get_emote_command),
    '/panic':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You run around in a frenzied state of panic."''', alt_desc='''Emote "You take one look at %s and panic."''', assemble_function=get_emote_command),
    '/pat':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need a pat."''', alt_desc='''Emote "You gently pat %s."''', assemble_function=get_emote_command),
    '/peer':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You peer around, searchingly."''', alt_desc='''Emote "You peer at %s searchingly."''', assemble_function=get_emote_command),
    '/peon':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You grovel on the ground, wallowing in subservience."''', alt_desc='''Emote "You grovel before %s like a subservient peon."''', assemble_function=get_emote_command),
    '/pest':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shoo the measly pests away."''', alt_desc='''Emote "You shoo %s away. Be gone pest!"''', assemble_function=get_emote_command),
    '/pet':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need to be petted."''', alt_desc='''Emote "You pet %s."''', assemble_function=get_emote_command),
    '/pick':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "With a finger deep in one nostril, you pass the time."''', alt_desc='''Emote "You pick your nose and show it to %s."''', assemble_function=get_emote_command),
    '/pinch':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You pinch yourself."''', alt_desc='''Emote "You pinch %s."''', assemble_function=get_emote_command),
    '/pity':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You pity those around you."''', alt_desc='''Emote "You look down upon %s with pity."''', assemble_function=get_emote_command),
    '/pizza':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are hungry!"''', alt_desc='''Emote "You are hungry. Maybe %s has some food..."''', assemble_function=get_emote_command),
    '/plead':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You drop to your knees and plead in desperation."''', alt_desc='''Emote "You plead with %s."''', assemble_function=get_emote_command),
    '/point':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You point over yonder."''', alt_desc='''Emote "You point at %s."''', assemble_function=get_emote_command),
    '/poke':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You poke your belly and giggle."''', alt_desc='''Emote "You poke %s. Hey!"''', assemble_function=get_emote_command),
    '/ponder':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You ponder the situation."''', alt_desc='''Emote "You ponder %s's actions."''', assemble_function=get_emote_command),
    '/pounce':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You pounce out from the shadows."''', alt_desc='''Emote "You pounce on top of %s."''', assemble_function=get_emote_command),
    '/pout':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You pout at everyone around you."''', alt_desc='''Emote "You pout at %s."''', assemble_function=get_emote_command),
    '/praise':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You praise the Light."''', alt_desc='''Emote "You lavish praise upon %s."''', assemble_function=get_emote_command),
    '/pray':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You pray to the Gods."''', alt_desc='''Emote "You say a prayer for %s."''', assemble_function=get_emote_command),
    '/proud':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are proud of yourself."''', alt_desc='''Emote "You are proud of %s."''', assemble_function=get_emote_command),
    '/pulse':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You check your own pulse."''', alt_desc='''Emote "You check %s for a pulse. Oh no!"''', assemble_function=get_emote_command),
    '/punch':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You punch yourself."''', alt_desc='''Emote "You punch %s's shoulder."''', assemble_function=get_emote_command),
    '/purr':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You purr like a kitten."''', alt_desc='''Emote "You purr at %s."''', assemble_function=get_emote_command),
    '/puzzled':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are puzzled. What's going on here?"''', alt_desc='''Emote "You are puzzled by %s."''', assemble_function=get_emote_command),
    '/question':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You want to know the meaning of life."''', alt_desc='''Emote "You question %s."''', assemble_function=get_emote_command),
    '/raise':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise your hand in the air."''', alt_desc='''Emote "You look at %s and raise your hand."''', assemble_function=get_emote_command),
    '/rasp':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You make a rude gesture."''', alt_desc='''Emote "You make a rude gesture at %s."''', assemble_function=get_emote_command),
    '/regret':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are filled with regret."''', alt_desc='''Emote "You think that %s will regret it."''', assemble_function=get_emote_command),
    '/revenge':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You vow you will have your revenge."''', alt_desc='''Emote "You vow revenge on %s."''', assemble_function=get_emote_command),
    '/rdy':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let everyone know that you are ready!"''', alt_desc='''Emote "You let %s know that you are ready!"''', assemble_function=get_emote_command),
    '/ready':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let everyone know that you are ready!"''', alt_desc='''Emote "You let %s know that you are ready!"''', assemble_function=get_emote_command),
    '/rear':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shake your rear."''', alt_desc='''Emote "You shake your rear at %s."''', assemble_function=get_emote_command),
    '/roar':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You roar with bestial vigor. So fierce!"''', alt_desc='''Emote "You roar with bestial vigor at %s. So fierce!"''', assemble_function=get_emote_command),
    '/rofl':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You roll on the floor laughing."''', alt_desc='''Emote "You roll on the floor laughing at %s."''', assemble_function=get_emote_command),
    '/rolleyes':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You roll your eyes."''', alt_desc='''Emote "You roll your eyes at %s."''', assemble_function=get_emote_command),
    '/rude':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You make a rude gesture."''', alt_desc='''Emote "You make a rude gesture at %s."''', assemble_function=get_emote_command),
    '/ruffle':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You ruffle your hair."''', alt_desc='''Emote "You ruffle %s's hair."''', assemble_function=get_emote_command),
    '/sad':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You hang your head dejectedly."''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/salute':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You stand at attention and salute."''', alt_desc='''Emote "You salute %s with respect."''', assemble_function=get_emote_command),
    '/search':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You search for something."''', alt_desc='''Emote "You search %s for something."''', assemble_function=get_emote_command),
    '/scared':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are scared!"''', alt_desc='''Emote "You are scared of %s."''', assemble_function=get_emote_command),
    '/scratch':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You scratch yourself. Ah, much better!"''', alt_desc='''Emote "You scratch %s. How catty!"''', assemble_function=get_emote_command),
    '/scoff':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You scoff.	You scoff at %s."''', assemble_function=get_emote_command),
    '/scold':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You scold yourself.	You scold %s."''', assemble_function=get_emote_command),
    '/scowl':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You scowl.	You scowl at %s."''', assemble_function=get_emote_command),
    '/sexy':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You're too sexy for your tunic...so sexy it hurts."''', alt_desc='''Emote "You think %s is a sexy devil."''', assemble_function=get_emote_command),
    '/shake':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shake your rear."''', alt_desc='''Emote "You shake your rear at %s."''', assemble_function=get_emote_command),
    '/shakefist':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shake your fist."''', alt_desc='''Emote "You shake your fist at %s."''', assemble_function=get_emote_command),
    '/shifty':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "Your eyes shift back and forth suspiciously."''', alt_desc='''Emote "You give %s a shifty look."''', assemble_function=get_emote_command),
    '/shimmy':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shimmy before the masses."''', alt_desc='''Emote "You shimmy before %s."''', assemble_function=get_emote_command),
    '/shindig':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise a drink in the air before chugging it down. Cheers!"''', alt_desc='''Emote "You raise a drink to %s. Cheers!"''', assemble_function=get_emote_command),
    '/shiver':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shiver in your boots. Chilling!"''', alt_desc='''Emote "You shiver beside %s. Chilling!"''', assemble_function=get_emote_command),
    '/shoo':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shoo the measly pests away."''', alt_desc='''Emote "You shoo %s away. Be gone pest!"''', assemble_function=get_emote_command),
    '/shrug':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shrug. Who knows?"''', alt_desc='''Emote "You shrug at %s. Who knows?"''', assemble_function=get_emote_command),
    '/shy':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You smile shyly."''', alt_desc='''Emote "You smile shyly at %s."''', assemble_function=get_emote_command),
    '/shudder':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You shudder."''', alt_desc='''Emote "You shudder at the sight of %s."''', assemble_function=get_emote_command),
    '/sigh':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let out a long, drawn-out sigh."''', alt_desc='''Emote "You sigh at %s."''', assemble_function=get_emote_command),
    '/signal':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You give the signal."''', alt_desc='''Emote "You give %s the signal."''', assemble_function=get_emote_command),
    '/silence':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You tell everyone to be quiet. Shhh!"''', alt_desc='''Emote "You tell %s to be quiet. Shhh!"''', assemble_function=get_emote_command),
    '/silly':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You tell a joke."''', alt_desc='''Emote "You tell %s a joke."''', assemble_function=get_emote_command),
    '/sing':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You burst into song."''', alt_desc='''Emote "You serenade %s with a song."''', assemble_function=get_emote_command),
    '/slap':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You slap yourself across the face. Ouch!"''', alt_desc='''Emote "You slap %s across the face. Ouch!"''', assemble_function=get_emote_command),
    '/sleep':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You fall asleep. Zzzzzzz."''', alt_desc='''Emote "You fall asleep. Zzzzzzz."''', assemble_function=get_emote_command),
    '/smack':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You smack your forehead."''', alt_desc='''Emote "You smack %s upside the head."''', assemble_function=get_emote_command),
    '/smell':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You smell the air around you. Wow, someone stinks!"''', alt_desc='''Emote "%s smells %s. Wow, someone stinks!"''', assemble_function=get_emote_command),
    '/smile':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You smile."''', alt_desc='''Emote "You smile at %s."''', assemble_function=get_emote_command),
    '/smirk':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "A sly smirk spreads across your face."''', alt_desc='''Emote "You smirk slyly at %s."''', assemble_function=get_emote_command),
    '/snap':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You snap your fingers."''', alt_desc='''Emote "You snap your fingers at %s."''', assemble_function=get_emote_command),
    '/snarl':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bare your teeth and snarl."''', alt_desc='''Emote "You bare your teeth and snarl at %s."''', assemble_function=get_emote_command),
    '/sneak':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You sneak away."''', alt_desc='''Emote "You sneak away from %s."''', assemble_function=get_emote_command),
    '/sneeze':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You sneeze. Achoo!"''', alt_desc='''Emote "You sneeze on %s. Achoo!"''', assemble_function=get_emote_command),
    '/snicker':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You quietly snicker to yourself."''', alt_desc='''Emote "You snicker at %s."''', assemble_function=get_emote_command),
    '/sniff':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You sniff the air around you."''', alt_desc='''Emote "You sniff %s."''', assemble_function=get_emote_command),
    '/snort':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You snort."''', alt_desc='''Emote "You snort derisively at %s."''', assemble_function=get_emote_command),
    '/snub':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You snub all of the lowly peons around you."''', alt_desc='''Emote "You snub %s."''', assemble_function=get_emote_command),
    '/sob':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cry."''', alt_desc='''Emote "You cry on %s's shoulder."''', assemble_function=get_emote_command),
    '/soothe':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need to be soothed."''', alt_desc='''Emote "You soothe %s. There, there...things will be ok."''', assemble_function=get_emote_command),
    '/sorry':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You apologize to everyone. Sorry!"''', alt_desc='''Emote "You apologize to %s. Sorry!"''', assemble_function=get_emote_command),
    '/spit':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You spit on the ground."''', alt_desc='''Emote "You spit on %s."''', assemble_function=get_emote_command),
    '/spoon':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You need to be cuddled."''', alt_desc='''Emote "You cuddle up against %s."''', assemble_function=get_emote_command),
    '/squeal':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You squeal like a pig."''', alt_desc='''Emote "You squeal at %s."''', assemble_function=get_emote_command),
    '/stare':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote ""''', alt_desc='''Emote "You stare %s down."''', assemble_function=get_emote_command),
    '/stink':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You smell the air around you. Wow, someone stinks!"''', alt_desc='''Emote "%s smells %s. Wow, someone stinks!"''', assemble_function=get_emote_command),
    '/strong':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You fle  your muscles. Oooooh so strong!"''', alt_desc='''Emote "You fle  at %s. Oooooh so strong!"''', assemble_function=get_emote_command),
    '/strut':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "With arms flapping, you strut around. Cluck, Cluck, Chicken!"''', alt_desc='''Emote "With arms flapping, you strut around %s. Cluck, Cluck, Chicken!"''', assemble_function=get_emote_command),
    '/surprised':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are so surprised!"''', alt_desc='''Emote "You are suprised by %s's actions."''', assemble_function=get_emote_command),
    '/surrender':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You surrender to your opponents."''', alt_desc='''Emote "You surrender before %s. Such is the agony of defeat..."''', assemble_function=get_emote_command),
    '/suspicious':       Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You narrow your eyes in suspicion."''', alt_desc='''Emote ""''', assemble_function=get_emote_command),
    '/sweat':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are sweating."''', alt_desc='''Emote "You sweat at the sight of %s."''', assemble_function=get_emote_command),
    '/tap':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You tap your foot. Hurry up already!"''', alt_desc='''Emote "You tap your foot as you wait for %s."''', assemble_function=get_emote_command),
    '/taunt':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You taunt everyone around you. Bring it fools!"''', alt_desc='''Emote "You make a taunting gesture at %s. Bring it!"''', assemble_function=get_emote_command),
    '/tease':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are such a tease."''', alt_desc='''Emote "You tease %s."''', assemble_function=get_emote_command),
    '/thank':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You thank everyone around you."''', alt_desc='''Emote "You thank %s."''', assemble_function=get_emote_command),
    '/thanks':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You thank everyone around you."''', alt_desc='''Emote "You thank %s."''', assemble_function=get_emote_command),
    '/think':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are lost in thought."''', alt_desc='''Emote "You think about %s."''', assemble_function=get_emote_command),
    '/thirsty':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are so thirsty. Can anyone spare a drink?"''', alt_desc='''Emote "You let %s know you are thirsty. Spare a drink?"''', assemble_function=get_emote_command),
    '/threat':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You threaten everyone with the wrath of doom."''', alt_desc='''Emote "You threaten %s with the wrath of doom."''', assemble_function=get_emote_command),
    '/threaten':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You threaten everyone with the wrath of doom."''', alt_desc='''Emote "You threaten %s with the wrath of doom."''', assemble_function=get_emote_command),
    '/tickle':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You want to be tickled. Hee hee!"''', alt_desc='''Emote "You tickle %s. Hee hee!"''', assemble_function=get_emote_command),
    '/tired':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let everyone know that you are tired."''', alt_desc='''Emote "You let %s know that you are tired."''', assemble_function=get_emote_command),
    '/train':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Make noise like a train)	 "''', assemble_function=get_emote_command),
    '/truce':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You offer a truce.	You offer %s a truce."''', assemble_function=get_emote_command),
    '/twiddle':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You twiddle your thumbs.	 "''', assemble_function=get_emote_command),
    '/ty':               Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You thank everyone around you."''', alt_desc='''Emote "You thank %s."''', assemble_function=get_emote_command),
    '/veto':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You veto the motion on the floor."''', alt_desc='''Emote "You veto %s's motion."''', assemble_function=get_emote_command),
    '/victory':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You bask in the glory of victory."''', alt_desc='''Emote "You bask in the glory of victory with %s."''', assemble_function=get_emote_command),
    '/violin':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You begin to play the world's smallest violin."''', alt_desc='''Emote "You play the world's smallest violin for %s."''', assemble_function=get_emote_command),
    '/volunteer':        Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You raise your hand in the air."''', alt_desc='''Emote "You look at %s and raise your hand."''', assemble_function=get_emote_command),
    '/wait':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You ask everyone to wait."''', alt_desc='''Emote "You ask %s to wait."''', assemble_function=get_emote_command),
    '/warn':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You warn everyone."''', alt_desc='''Emote "You warn %s."''', assemble_function=get_emote_command),
    '/wave':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You beckon everyone over to you."''', alt_desc='''Emote "You wave at %s."''', assemble_function=get_emote_command),
    '/weep':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You cry."''', alt_desc='''Emote "You cry on %s's shoulder."''', assemble_function=get_emote_command),
    '/welcome':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You welcome everyone."''', alt_desc='''Emote "You welcome %s."''', assemble_function=get_emote_command),
    '/whine':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You whine pathetically."''', alt_desc='''Emote "You whine pathetically at %s."''', assemble_function=get_emote_command),
    '/whistle':          Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You let forth a sharp whistle."''', alt_desc='''Emote "You whistle at %s."''', assemble_function=get_emote_command),
    '/wicked':           Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You grin wickedly."''', alt_desc='''Emote "You grin wickedly at %s."''', assemble_function=get_emote_command),
    '/wickedly':         Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You grin wickedly."''', alt_desc='''Emote "You grin wickedly at %s."''', assemble_function=get_emote_command),
    '/wink':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You wink slyly."''', alt_desc='''Emote "You wink slyly at %s."''', assemble_function=get_emote_command),
    '/work':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You begin to work."''', alt_desc='''Emote "You work with %s."''', assemble_function=get_emote_command),
    '/wrath':            Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You threaten everyone with the wrath of doom."''', alt_desc='''Emote "You threaten %s with the wrath of doom."''', assemble_function=get_emote_command),
    '/yawn':             Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You yawn sleepily."''', alt_desc='''Emote "You yawn sleepily at %s."''', assemble_function=get_emote_command),
    '/yay':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You are filled with happiness!"''', alt_desc='''Emote "You are very happy with %s!"''', assemble_function=get_emote_command),
    '/yes':              Verb(secure=False, takes_ext_target=True, takes_perc_target=True, takes_units=True, desc='''Emote "You nod."''', alt_desc='''Emote "You nod at %s. "''', assemble_function=get_emote_command),
    }
