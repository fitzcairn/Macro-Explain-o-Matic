'''
Specific intepret commands for language parts.

When interpreting commands, some parts need specific structure.  These
functions are saved as refs, and called at interpret time.
'''
import re
import logging
from macro.interpret.errors    import *
from macro.interpret.txt_token import TxtToken
from macro.interpret.slots     import decode_wow_slot, decode_data_slot, get_wow_slots_for_data, check_slot_token


#
# Verb Assembly Functions
#
# All return a list of TxtTokens
#

def get_assembled_command(token, params=[], mods=[], targets=[]):
    ''' Default command assemble. '''
    cmd = [token]
    if params: cmd.extend(params)
    if targets: cmd.extend(targets)
    if mods:    cmd.extend(mods)
    return cmd

def get_commented_command(token, params=[], mods=[], targets=[]):
    ''' Handle commands which use only the verb. '''
    return [TxtToken("Commented line, will not be evaluated:")] + [token]

def get_emote_command(token, params=[], mods=[], targets=[]):
    ''' Handle emotes, which can take a target. '''
    if targets and len(targets) == 1 and token.attrs.alt_desc:
        token.render_desc = token.attrs.alt_desc % (targets[0].get_render_desc())
    return [token]

def get_verb_only_command(token, params=[], mods=[], targets=[]):
    ''' Handle commands which use only the verb. '''
    return [token]

def get_verb_msg_command(token, params=[], mods=[], targets=[]):
    ''' Handle commands which use only the verb. '''
    if not params:
        return [token]
    return [token] + [TxtToken("with status message:")] + params

def get_follow_command(token, params=[], mods=[], targets=[]):
    ''' Handle follow and f commands. '''
    return [token] + targets

def get_roll_command(token, params=[], mods=[], targets=[]):
    ''' Handle roll, random, etc. '''
    if not params:
        token.render_desc = "%s between 1 and 100" % token.attrs.desc
        return [token]
    return [token] + params

def get_verb_params_command(token, params=[], mods=[], targets=[]):
    ''' Handle commands which use only the verb and params'''
    return [token] + params

def get_targeted_chat_command(token, params=[], mods=[], targets=[]):
    ''' Handle chat commands with a target.'''
    if not params: params = [TxtToken("nothing")]
    return [token] + params + [TxtToken("to")] + targets

def get_pet_autocast_command(token, params=[], mods=[], targets=[]):
    ''' Handle pet commands for autocasting that have parameters. '''
    return [token] + [TxtToken("for")] + params

def get_cancelaura_command(token, params=[], mods=[], targets=[]):
    ''' Handle cancelaura command '''
    return [token] + params + [TxtToken("from yourself", render_space_after=False)]

def get_equip_command(token, params=[], mods=[], targets=[]):
    ''' Handle equip command '''
    return [token] + params + [TxtToken("in its default slot", render_space_after=False)]

## TODO: add a parameter assembly function to add quotes to params.
def get_equipset_command(token, params=[], mods=[], targets=[]):
    ''' Handle equipset command '''
    params[-1].render_space_after = False
    return [token] + [TxtToken("'", render_space_after=False)] + params + [TxtToken("'"), TxtToken("via the Equipment Manager", render_space_after=False)]

def get_show_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for #show. '''
    if params: return [token, TxtToken("for")] + params + [TxtToken("for this macro on the action bar", render_space_after=False)]
    return [token, TxtToken("for the first item or spell in this macro on the action bar", render_space_after=False)]

def get_cast_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for /cast. '''
    if not params: return [token]
    return [token] + params + [TxtToken("on")] + targets

def get_castsequence_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for /castsequence and /castrandom '''
    # Did we get a target? If so, add a join
    if targets: targets = [TxtToken("on")] + targets 

    if mods: return [token, TxtToken("of")] + params + targets + [TxtToken("each time the macro is activated,")] + mods
    return [token, TxtToken("of")] + params + targets + [TxtToken("each time the macro is activated", render_space_after=False)]

def get_actionbar_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for /cast. '''
    for p in params:
        p.render_desc = "bar " + p.data
    if len(params) > 1:
        return [token, TxtToken("from"), params[0], TxtToken("to"), params[1], TxtToken("if"), params[0], TxtToken("is active, otherwise switch to"), params[0]]
    return [token, TxtToken("to")] + params

# Targeting
def get_assist_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for assist. '''
    # If we have a parameter, we will assist that.
    if params: return [token] + params
    # Otherwise, if we found a recognized target, target that
    elif targets: return [token] + targets
    return [token, TxtToken("your currently targeted unit", render_space_after=False)]

def get_focus_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for focus. '''
    # If we have a parameter, we will assist that.
    if params: return [token] + params
    # Otherwise, if we found a recognized target, target that
    elif targets: return [token] + targets
    return [token, TxtToken("your currently targeted unit", render_space_after=False)]

# TODO: MODIFY PARAMETER TO HAVE QUOTES
def get_target_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for /tar /or target. '''
    # If we have a parameter, we're searching.
    if params: return [token] + params
    # Otherwise, if we found a recognized targets, target that
    elif targets: return [token] + targets
    return [token, TxtToken("nothing")]

# TODO: MODIFY PARAMETER TO HAVE QUOTES
def get_targetexact_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for /tar /or target. '''
    if targets:
        return [token, TxtToken("visible unit named exactly")] + targets
    return [token, TxtToken("nothing")]

def get_target_cycle_command(token, params=[], mods=[], targets=[]):
    ''' Command assemble for targing commands that cycle through targets.'''
    # If we have a parameter, cycle in reverse.
    if params: return [token] + params
    return [token]


#
# Options Assembly Functions
#
# All return a list of TxtTokens
#

def get_assembled_option(token, neg=None, args=[], target_self=False):
    ''' Default description function for an option. '''
    if args:
        if neg: return [neg, token] +  args
        return [token] + args
    else:
        if neg: return [neg, token]
        return [token]

def get_exists_option(token, neg=None, args=[], target_self=False):
    if neg: return [TxtToken("does"), neg, token]
    # "you exist" vs "you exists"
    if target_self: return [token]
    token.render_desc = "exists"
    return [token] 
 
def get_stance_option(token, neg=None, args=[], target_self=False):
    if args:
        if neg: return [neg, TxtToken("in"), token] + args
        return [TxtToken("in"), token] + args
    else:
        if neg: return [neg, TxtToken("in a"), token]
        return [TxtToken("in a"), token]
 
def get_spec_option(token, neg=None, args=[], target_self=False):
    if args:
        if neg: return [neg, TxtToken("have"), token] + args + [TxtToken("active")]
        return [TxtToken("have"), token] + args + [TxtToken("active")]
    else:
        if neg: return [neg, TxtToken("have a"), token, TxtToken("active")]
        return [TxtToken("have a"), token, TxtToken("active")]
 
def get_channeling_option(token, neg=None, args=[], target_self=False):
    if args:
        if neg: return [neg, token] + args
        return [token] + args
    else:
        if neg: return [neg, token, TxtToken("any spell")]
        return [token, TxtToken("any spell")]
 
def get_mod_option(token, neg=None, args=[], target_self=False):
    if args:
        if neg: return [TxtToken("were"), neg, token, TxtToken("the")] + args
        return [TxtToken("were"), token, TxtToken("the")] + args
    else:
        if neg: return [TxtToken("were"), neg, token, TxtToken("any modifier key down")]
        return [token, TxtToken("a modifier key")]

def get_btn_option(token, neg=None, args=[], target_self=False):
    # Augment the arg str--if its a num, it'll be of len 2 or less.
    if args:
        for a in args:
            if not isinstance(a, TxtToken) and a.data_type is int:
                a.render_desc = "mouse button %s" % a.data
    if neg:
        token.render_desc = "activate this macro with"
        return [TxtToken("did"), neg, token] + args
    return [token] + args

def get_equipped_option(token, neg=None, args=[], target_self=False):
    if neg: return [TxtToken("have"), neg, token] + args
    return [TxtToken("have"), token] + args
    
def get_worn_option(token, neg=None, args=[], target_self=False):
    if neg: return [TxtToken("are"), neg, token] + args
    return [TxtToken("are"), token] + args

def get_bar_option(token, neg=None, args=[], target_self=False):
    if neg: return [TxtToken("do"), neg, token] + args + [TxtToken("active")]
    return [token] + args + [TxtToken("active")]

def get_pet_option(token, neg=None, args=[], target_self=False):
    if args:
        if neg: return [TxtToken("do"), neg, token] + args + [TxtToken("out")]
        return [token] + args + [TxtToken("out")]
    else:
        if neg: return [TxtToken("do"), neg, token, TxtToken("out")]
        return [token, TxtToken("out")]

def get_group_option(token, neg=None, args=[], target_self=False):
    if args:
        token.render_desc = "in a"
        if neg: return [neg, token] + args
        return [token] + args
    else:
        if neg: return [neg, token]
        return [token]


#
# Parameter Assembly Functions
#
# Required input into these is the params section of the parse tree,
# which is a list of [(toggle, parameter)...] or None
#
# Output is a list of TxtTokens.
#

# Default:
def get_assembled_parameter(params=[]):
    ''' Default description function for parameters for a macro.
    Parameter structure is [(toggle, parameter)...] or None.  Returns
    a list of TxtTokens.
    '''
    if not params: return [TxtToken("nothing")]
    param_list = []
    for toggle, param in params:
        if toggle:
            toggle.render_desc = "is not already active"
            toggle.render_space_after = False
            param_list.extend([param, TxtToken("(if"), param, toggle, TxtToken(")")])
        else: param_list.append(param)
    return param_list

def get_who_params(params=[]):
    ''' Translate /who parameters. '''
    if params:
        return [TxtToken('with attributes matching:')] + [p[1] for p in params]
    return params
    
def get_roll_params(params=[]):
    ''' Translate roll parameters. '''
    try:
        assert len(params) == 1
        bounds = map(int, params[0][1].data.split())
        if len(bounds) == 1 and bounds[0] > 0:
            return [TxtToken("between 1 and %s" % bounds[0])]
        if len(bounds) == 2 and bounds[0] >= 0 and bounds[1] > bounds[0]:
            return [TxtToken("between %s and %s" % tuple(bounds))]
    except:
        pass
    return [TxtToken("between 1 and 100")]
    
def get_translated_chat_params(params=[]):
    ''' Given chat parameters, translate %t/%T appropiately. '''
    p = re.compile('\%[t|T]')
    interp_params = []
    for toggle, param in params:
        p_txt = param.data
        p_txt = ''.join(['"',
                       p.sub('(your currently targeted unit)', p_txt),
                       '"'])
        param.render_desc = p_txt
        interp_params.append(param)
    return interp_params
    
def get_assembled_list_param(params=[], targets=[]):
    ''' Special param formating for verbs that take a list of
    parameters.  Parameter structure is [(toggle, parameter)...] or
    None.  Assigns each target to each parameter.  Returns a list of
    TxtTokens.  Returns [] unless accompanied by a target list.
    '''
    param_list = [TxtToken("[", render_space_after=True)]
    idx = 0
    for toggle, param in params:
        p_tokens = []
        idx += 1
        # Handle toggle
        if toggle:
            toggle.render_desc = "is not already active"
            toggle.render_space_after = False
            p_tokens = [param, TxtToken("(if"), param, toggle, TxtToken(")")]
        else:
            p_tokens = [param]
        # Handle target token, if we got one and the param isn't empty.
        if targets and not param.attrs.is_empty:
            param.render_space_after = True
            p_tokens.extend([TxtToken("on")] + targets[idx-1])
        param_list.extend(p_tokens)
        if idx < len(params):
            param_list[-1].render_space_after = False
            param_list.append(TxtToken(","))
    param_list[-1].render_space_after = True
    param_list.append(TxtToken("]"))
    return param_list

def get_assembled_parameter_equipslot(params):
    ''' Handle equipslot params: slotid item '''
    slot_list = []

    # Couple different otions: (str) for error case,
    # (int, str) for slot + param, or (int,int,int).
    # This has already been verified for us.
    if len(params) == 1:
        error_param = [p for t,p in params]
        return error_param
    elif len(params) == 2:
        slot, item = [p for t,p in params]
        check_slot_token(slot)
        
        # Decode the slot token.
        if decode_wow_slot(slot.data):
            slot.render_desc = decode_wow_slot(slot.data)
            slot_list = [TxtToken("as your"), slot]
        else:
            slot_list = [TxtToken("in equipment slot"), slot]
                          
        # If we recognize this item, use wowhead to decode it's slot.
        # This can fail because wowhead data is spotty.
        if item.found() and item.attrs.param_data_obj.is_item():
            # Make sure the slot we request is appropiate.
            # If not, keep the output as the slot requiested in the
            # macro, but display a warning with what slot the
            # item belongs in.
            if not item.attrs.param_data_obj.test_item_slotid(int(slot.data)):
                item.error_desc = item.get_render_desc()
                decoded = decode_wow_slot(slot.data)
                if not decoded:
                    decoded = ''
                else:
                    decoded = "(%s)" % decoded
                # Below changed for now for clarity.
                item.warn = (WARN_WRONG_SLOT,
                             [item],
                             [slot],
                             [TxtToken(txt=decoded)])
                             #[TxtToken(txt="%s" % get_wow_slots_for_data(item.slot()))],
                             #[TxtToken(txt="%s" % decode_data_slot(item.slot()))])
                
        # Create and return the description
        return [TxtToken("your"), item] + slot_list
    else:
        slot, bag_id, bag_slot = [p for t,p in params]
        check_slot_token(slot)
        if decode_wow_slot(slot.data):
            slot.render_desc = decode_wow_slot(slot.data)
            slot_list = [TxtToken("as your"), slot]
        else:
            slot_list = [TxtToken("in equipment slot"), slot]
        bag_id.render_space_after = False
        return [TxtToken("item from bag"), bag_id, TxtToken(", bag slot"), bag_slot] + slot_list

def get_assembled_parameter_show(params):
    ''' Handle parameters for #show* commands. '''
    # Couple different otions: (str), (int), or (int,int).  Parameter
    # correctness has already been verified for us.
    if len(params) == 2:
        bag_id, bag_slot = [p for t,p in params]
        bag_id.render_space_after = False
        return [TxtToken("item in bag"), bag_id, TxtToken(", bag slot"), bag_slot]
    else:
        param = params[0][1]
        if param.data_type is int:
            # Item slot--decode
            check_slot_token(param)
            if decode_wow_slot(param.data):
                param.render_desc = decode_wow_slot(param.data)
                return [TxtToken("item equipped as your"), param]
            else:
                return [TxtToken("item in equipment slot"), param]
        else:
            return [param]

def get_assembled_parameter_equip(params):
    ''' Handle equip params: item '''

    # Couple different otions: (str), or (int,int).
    # This has already been verified for us.
    if len(params) == 2:
        bag_id, bag_slot = [p for t,p in params]
        bag_id.render_space_after = False
        return [TxtToken("item in bag"), bag_id, TxtToken(", bag slot"), bag_slot]
    else:
        return [TxtToken("your"), params[0][1]]

def get_assembled_parameter_click(params):
    ''' Handle click params '''
    # Couple different otions: (str), (str, int, str), or (str,int).
    # This has already been verified for us.
    if not params: return [TxtToken("nothing")]
    if len(params) == 1:
        return [TxtToken("button:"), params[0][1]]
    if len(params) == 2:
        bar, num = [p for t,p in params]
        return [TxtToken("button"), num, TxtToken("on"), bar]
    else:
        bar, num, mouse = [p for t,p in params]
        return [TxtToken("button"), num, TxtToken("on"), bar, TxtToken("with"), mouse]

def get_assembled_parameter_use(params):
    ''' Handle use params '''
    # Couple different otions: (str), (int), (int,int).
    # This has already been verified for us.
    if len(params) == 2:
        bag, slot = [p for t,p in params]
        bag.render_space_after = False
        slot.render_space_after = False
        return [TxtToken("item in bag number"), bag, TxtToken(", bag slot number"), slot]
    else:
        item = [p for t,p in params][0]
        if item.data_type is int:
            if decode_wow_slot(item.data):
                item.render_desc = decode_wow_slot(item.data)
                return [TxtToken("your equipped"), item]
            else:
                check_slot_token(item)
                return [TxtToken("item in slot"), item]
        return [TxtToken("your"), item]


def get_assembled_parameter_targeting(params):
    ''' Doctor up "nearest match" targeting. '''
    return [TxtToken("visible unit with")] + [params[0][1]] + [TxtToken("anywhere in the unit name")]


def get_assembled_parameter_cycle_target(params):
    ''' If we have a param for this, it has already been
    checked and verified as an integer.  Do some error correcting
    and return an interpretation.'''
    if len(params) > 0:
        if params[0][1].data == "0":
            # We don't need this parameter.  Remove and warn.
            params[0][1].warn = (WARN_NUMBER_LT_1,)
            return []
        if params[0][1].data != "1":
            # Correct the param to just "1", and explain why.
            params[0][1].warn = (WARN_NUMBER_GT_1, [params[0][1]])
            params[0][1].data = "1"
        params[0][1].render_desc = "in reverse order"
        return [params[0][1]]
    return []
